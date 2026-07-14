"""Runtime runtime, plugin orchestration, and adapter supervision."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib
import importlib.util
import inspect
import json
import logging
import re
import sys
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .adapter import Adapter
from .config import load_config, redact_config_value
from .context import Context
from .di import Depends
from .event import Event
from .logging import configure_logging
from .message import Message
from .observability import AuditLogger, RuntimeMetrics
from .permissions import ensure_permission
from .plugin import BoundHandler, HandlerSpec, Plugin
from .rules import ensure_rule
from .session import SessionManager
from .state import StateStore, create_state_store
from .validation import plugin_config_schema, validate_plugin_config

LOGGER = logging.getLogger("iamai")

BUILTIN_ADAPTERS = {
    "terminal": "iamai.adapters.terminal:TerminalAdapter",
    "onebot11": "iamai.adapters.onebot11:OneBot11Adapter",
    "telegram": "iamai.adapters.telegram:TelegramAdapter",
    "webhook": "iamai.adapters.webhook:WebhookAdapter",
}

BUILTIN_PLUGINS = {
    "management": "iamai.plugins.management:ManagementPlugin",
    "management_api": "iamai.plugins.management_api:ManagementApiPlugin",
}

DEFAULT_BUILTIN_PLUGINS = ("management",)
MIDDLEWARE_PHASES = ("before", "around", "after", "error")
PLUGIN_ENTRY_POINT_GROUP = "iamai.plugins"
ADAPTER_ENTRY_POINT_GROUP = "iamai.adapters"


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    """Resolved plugin metadata used for ordering and runtime inspection."""

    name: str
    plugin_cls: type[Plugin]
    ref: str
    source_index: int
    priority: int
    description: str
    requires: tuple[str, ...]
    optional_requires: tuple[str, ...]
    load_after: tuple[str, ...]
    load_before: tuple[str, ...]
    is_builtin: bool = False


class Runtime:
    """Top-level runtime container that owns adapters, plugins, state, and dispatch."""

    def __init__(self, config: dict[str, Any], *, base_path: Path | None = None) -> None:
        self.config = config
        root_dir = config.get("__meta__", {}).get("root_dir")
        self.base_path = base_path or Path(root_dir or ".").resolve()
        self.state: dict[str, Any] = {}
        self.plugins: list[Plugin] = []
        self.adapters: list[Adapter] = []
        self.dependencies: dict[str, Any] = {}
        self._typed_dependencies: dict[type[Any], Any] = {}
        self._adapter_map: dict[str, Adapter] = {}
        self._plugin_map: dict[str, Plugin] = {}
        self._plugin_descriptors: list[PluginDescriptor] = []
        self._plugin_descriptor_map: dict[str, PluginDescriptor] = {}
        self._adapter_tasks: list[asyncio.Task[None]] = []
        self._adapter_failures: asyncio.Queue[BaseException] = asyncio.Queue()
        self._handler_tasks: set[asyncio.Task[None]] = set()
        self._handler_slots = asyncio.Semaphore(1)
        self._stop_event = asyncio.Event()
        self._bootstrapped = False
        self._serving = False
        self._runtime_lock = asyncio.Lock()
        self._hot_reload_task: asyncio.Task[None] | None = None
        self._plugin_watch_state: dict[str, Any] = {}
        self._python_path_entries: list[str] = []
        self._runtime_middlewares: list[tuple[str, int, Callable[..., Any]]] = []
        self.sessions = SessionManager()
        self._configure_runtime_limits()
        self.state_store: StateStore = create_state_store(config, base_path=self.base_path)
        self.metrics = RuntimeMetrics()
        self.audit_logger = AuditLogger()

    @classmethod
    def from_config_file(cls, path: str | Path) -> "Runtime":
        """Create a runtime from a TOML configuration file."""
        config = load_config(path)
        return cls(config, base_path=Path(config["__meta__"]["root_dir"]))

    @property
    def runtime_config(self) -> dict[str, Any]:
        """Return the validated ``[runtime]`` configuration."""
        return dict(self.config.get("runtime", {}))

    def superusers(self) -> set[str]:
        """Return configured superuser IDs as strings."""
        return {str(item) for item in self.runtime_config.get("superusers", [])}

    def command_prefixes(self) -> tuple[str, ...]:
        """Return configured command prefixes."""
        prefixes = self.runtime_config.get("command_prefixes", ["/"])
        return tuple(str(item) for item in prefixes)

    def get_plugin_config(self, plugin_name: str) -> dict[str, Any]:
        """Return raw configuration for one plugin."""
        return dict(self.config.get("plugin", {}).get(plugin_name, {}))

    def get_adapter_config(self, adapter_name: str) -> dict[str, Any]:
        """Return raw configuration for one adapter."""
        return dict(self.config.get("adapter", {}).get(adapter_name, {}))

    def get_plugin(self, name: str) -> Plugin:
        """Return a loaded plugin by name."""
        return self._plugin_map[name]

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return operator-facing metadata for loaded plugins."""
        result: list[dict[str, Any]] = []
        for plugin in self.plugins:
            descriptor = self._plugin_descriptor_map.get(plugin.plugin_name)
            result.append(
                {
                    "name": plugin.plugin_name,
                    "description": descriptor.description
                    if descriptor
                    else getattr(plugin, "description", ""),
                    "load_index": plugin.load_index,
                    "priority": descriptor.priority if descriptor else plugin.priority,
                    "builtin": plugin.is_builtin,
                    "ref": plugin.plugin_ref,
                    "config_model": (
                        getattr(descriptor.plugin_cls.config_model, "__name__", None)
                        if descriptor and descriptor.plugin_cls.config_model is not None
                        else None
                    ),
                    "requires": list(
                        descriptor.requires if descriptor else getattr(plugin, "requires", ())
                    ),
                    "optional_requires": list(
                        descriptor.optional_requires
                        if descriptor
                        else getattr(plugin, "optional_requires", ())
                    ),
                    "load_after": list(
                        descriptor.load_after if descriptor else getattr(plugin, "load_after", ())
                    ),
                    "load_before": list(
                        descriptor.load_before if descriptor else getattr(plugin, "load_before", ())
                    ),
                }
            )
        return result

    def iter_handlers(self) -> tuple[BoundHandler, ...]:
        """Return all bound handlers in runtime dispatch order.

        This exposes the actual bound callbacks for plugins that need advanced
        introspection. Prefer ``list_handlers`` for diagnostics and management
        API payloads.
        """
        handlers: list[BoundHandler] = []
        for plugin in self.plugins:
            handlers.extend(plugin.iter_handlers())
        return tuple(handlers)

    def list_handlers(self) -> list[dict[str, Any]]:
        """Return JSON-friendly metadata for all registered plugin handlers."""
        result: list[dict[str, Any]] = []
        for handler in self.iter_handlers():
            spec = handler.spec
            result.append(
                {
                    "plugin": handler.plugin.plugin_name,
                    "name": spec.func_name,
                    "kind": spec.kind,
                    "commands": list(spec.commands),
                    "prefixes": list(spec.prefixes),
                    "adapters": list(spec.adapters),
                    "event_types": list(spec.event_types),
                    "detail_types": list(spec.detail_types),
                    "startswith": list(spec.startswith),
                    "contains": list(spec.contains),
                    "regex": spec.regex,
                    "priority": spec.priority,
                    "block": spec.block,
                    "rule": spec.rule is not None,
                    "permission": spec.permission is not None,
                    "callback": (f"{handler.callback.__module__}.{handler.callback.__qualname__}"),
                }
            )
        return result

    def list_adapters(self) -> list[dict[str, Any]]:
        """Return operator-facing metadata for loaded adapters."""
        return [
            {
                "name": adapter.name,
                "class": adapter.__class__.__name__,
                "module": adapter.__class__.__module__,
                "config": redact_config_value(self.get_adapter_config(adapter.name)),
            }
            for adapter in self.adapters
        ]

    def list_sessions(self) -> list[dict[str, Any]]:
        """Return active session waiters for diagnostics."""
        return self.sessions.list_waiters()

    def list_metrics(self) -> list[dict[str, Any]]:
        """Return runtime metric series as dictionaries."""
        return [series.to_dict() for series in self.metrics.series()]

    def health(self) -> dict[str, Any]:
        """Return a compact runtime health payload."""
        return {
            "bootstrapped": self._bootstrapped,
            "plugins": len(self.plugins),
            "handlers": len(self.list_handlers()),
            "adapters": len(self.adapters),
            "hot_reload": self._hot_reload_enabled(),
            "sessions": len(self.list_sessions()),
            "state_store": self.state_store.__class__.__name__,
            "metric_series": len(self.metrics.series()),
            "audit_logger": self.audit_logger.logger_name,
        }

    def get_plugin_schema(self, plugin_name: str) -> dict[str, Any] | None:
        """Return a plugin configuration JSON schema, if available."""
        descriptor = self._plugin_descriptor_map.get(plugin_name)
        if descriptor is None:
            return None
        return plugin_config_schema(descriptor.plugin_cls)

    def list_plugin_traces(self) -> list[dict[str, Any]]:
        """Return trace payloads exposed by loaded plugins."""
        traces: list[dict[str, Any]] = []
        for plugin in self.plugins:
            for item in plugin.state.get("traces", []):
                if hasattr(item, "to_dict"):
                    payload = item.to_dict()
                elif isinstance(item, dict):
                    payload = dict(item)
                else:
                    payload = {"value": str(item)}
                payload.setdefault("plugin", plugin.plugin_name)
                traces.append(payload)
        return traces

    def register_dependency(
        self,
        name: str,
        value: Any,
        *,
        annotation: type[Any] | None = None,
    ) -> None:
        """Register a value for name-based and type-based dependency injection."""
        self.dependencies[name] = value
        typed_key = annotation or type(value)
        self._typed_dependencies[typed_key] = value

    def count_metric(self, name: str, value: int = 1, **labels: Any) -> None:
        """Increment a runtime counter."""
        self.metrics.increment(name, value=value, **labels)

    def audit(
        self,
        action: str,
        *,
        outcome: str = "ok",
        level: int = logging.INFO,
        **fields: Any,
    ) -> None:
        """Emit one structured runtime audit event."""
        self.audit_logger.emit(action, outcome=outcome, level=level, **fields)

    def add_middleware(
        self,
        callback: Callable[..., Any],
        *,
        priority: int = 100,
        phase: str = "around",
    ) -> None:
        """Register runtime middleware outside of a plugin class."""
        if phase not in MIDDLEWARE_PHASES:
            raise ValueError(f"unsupported middleware phase: {phase!r}")
        self._runtime_middlewares.append((phase, priority, callback))
        self._runtime_middlewares.sort(key=lambda item: (MIDDLEWARE_PHASES.index(item[0]), item[1]))

    async def bootstrap(self) -> None:
        """Load plugins and adapters, then run plugin startup hooks."""
        if self._bootstrapped:
            return
        self._configure_logging()
        self._refresh_runtime_dependencies()
        self.load_plugins()
        self.load_adapters()
        for plugin in self.plugins:
            await plugin.startup()
        self._plugin_watch_state = self._snapshot_plugin_watch_state()
        self._start_hot_reload_task()
        self._bootstrapped = True

    async def serve(self) -> None:
        """Run the runtime until stopped or an adapter fails."""
        await self.bootstrap()
        self._serving = True
        self._start_adapters()
        stop_task = asyncio.create_task(self._stop_event.wait(), name="iamai:stop")
        try:
            while True:
                failure_task = asyncio.create_task(
                    self._adapter_failures.get(),
                    name="iamai:adapter-failure",
                )
                done, pending = await asyncio.wait(
                    [stop_task, failure_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if stop_task in done:
                    failure_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await failure_task
                    break
                exc = failure_task.result()
                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task
                raise exc
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Stop adapters, cancel handler tasks, and run plugin shutdown hooks."""
        self._serving = False
        self._stop_event.set()
        if self._hot_reload_task is not None:
            self._hot_reload_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._hot_reload_task
            self._hot_reload_task = None
        await self._stop_adapters()
        for task in list(self._handler_tasks):
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        for plugin in reversed(self.plugins):
            with contextlib.suppress(Exception):
                self._save_plugin_state(plugin)
                await plugin.shutdown()

    async def stop(self) -> None:
        """Request graceful process shutdown."""
        self._stop_event.set()

    async def reload_plugins(self) -> None:
        """Reload user plugins while keeping the current adapter set."""
        async with self._runtime_lock:
            LOGGER.info("reloading plugins")
            for plugin in self.plugins:
                self._save_plugin_state(plugin)
            try:
                new_plugins, descriptors = self._build_plugins(reload_modules=True)
                started_plugins: list[Plugin] = []
                try:
                    for plugin in new_plugins:
                        await plugin.startup()
                        started_plugins.append(plugin)
                except Exception:
                    for plugin in reversed(started_plugins):
                        with contextlib.suppress(Exception):
                            await plugin.shutdown()
                    raise
                old_plugins = self.plugins
                self._set_plugins(new_plugins, descriptors)
                self._plugin_watch_state = self._snapshot_plugin_watch_state()
                for plugin in reversed(old_plugins):
                    with contextlib.suppress(Exception):
                        await plugin.shutdown()
                LOGGER.info("reloaded %s plugins", len(self.plugins))
                self.count_metric("runtime_reload_total", action="plugins", outcome="ok")
                self.audit(
                    "runtime.reload", target="plugins", outcome="ok", plugins=len(self.plugins)
                )
            except Exception as exc:
                self.count_metric("runtime_reload_total", action="plugins", outcome="error")
                self.audit(
                    "runtime.reload",
                    target="plugins",
                    outcome="error",
                    level=logging.ERROR,
                    error=type(exc).__name__,
                )
                raise

    async def reload_config(self) -> None:
        """Reload configuration, plugins, state backend, and adapters atomically."""
        config_path = self.config.get("__meta__", {}).get("config_path")
        if not config_path:
            await self.reload_plugins()
            return
        async with self._runtime_lock:
            LOGGER.info("reloading config from %s", config_path)
            for plugin in self.plugins:
                self._save_plugin_state(plugin)
            old_config = self.config
            old_base_path = self.base_path
            old_state_store = self.state_store
            old_plugins = self.plugins
            old_descriptors = self._plugin_descriptors
            old_adapters = self.adapters
            old_adapter_map = self._adapter_map

            try:
                self.config = load_config(config_path)
                self.base_path = Path(self.config["__meta__"]["root_dir"])
                self.state_store = create_state_store(self.config, base_path=self.base_path)
                self._refresh_runtime_dependencies()
                self._apply_python_paths()
                started_plugins: list[Plugin] = []
                try:
                    new_plugins, descriptors = self._build_plugins(reload_modules=True)
                    for plugin in new_plugins:
                        await plugin.startup()
                        started_plugins.append(plugin)
                    new_adapters, adapter_map = self._build_adapters()
                except Exception:
                    for plugin in reversed(started_plugins):
                        with contextlib.suppress(Exception):
                            await plugin.shutdown()
                    self.config = old_config
                    self.base_path = old_base_path
                    self.state_store = old_state_store
                    self._plugin_descriptors = old_descriptors
                    self._adapter_map = old_adapter_map
                    self._refresh_runtime_dependencies()
                    self._apply_python_paths()
                    raise

                self._configure_runtime_limits()
                self._set_plugins(new_plugins, descriptors)
                self._set_adapters(new_adapters, adapter_map)
                if self._serving:
                    await self._stop_adapters(adapters=old_adapters)
                    self._start_adapters()
                self._plugin_watch_state = self._snapshot_plugin_watch_state()
                for plugin in reversed(old_plugins):
                    with contextlib.suppress(Exception):
                        await plugin.shutdown()
                LOGGER.info("reloaded config and %s plugins", len(self.plugins))
                self.count_metric("runtime_reload_total", action="config", outcome="ok")
                self.audit(
                    "runtime.reload",
                    target="config",
                    outcome="ok",
                    plugins=len(self.plugins),
                    adapters=len(self.adapters),
                )
            except Exception as exc:
                self.count_metric("runtime_reload_total", action="config", outcome="error")
                self.audit(
                    "runtime.reload",
                    target="config",
                    outcome="error",
                    level=logging.ERROR,
                    error=type(exc).__name__,
                )
                raise

    async def dispatch(self, event: Event, adapter: Adapter) -> None:
        """Dispatch one normalized event to matching handlers."""
        if event.type == "meta_event":
            LOGGER.debug(
                "event[%s] %s/%s text=%r",
                event.id, event.adapter, event.type, event.text,
            )
        else:
            LOGGER.info(
                "event[%s] %s/%s text=%r",
                event.id, event.adapter, event.type, event.text,
            )
        handler_jobs: list[tuple[Context, BoundHandler, dict[str, list[Callable[..., Any]]]]] = []
        async with self._runtime_lock:
            plugins = list(self.plugins)
            middlewares = self._collect_middlewares(plugins)
            waiter_ctx = Context(
                runtime=self,
                adapter=adapter,
                plugin=plugins[0] if plugins else _NullPlugin(self),
                event=event,
                handler=_NULL_HANDLER,
                matches={},
            )
            if await self.sessions.consume(waiter_ctx):
                return
            for plugin in plugins:
                for handler in plugin.iter_handlers():
                    matches = self._match_handler(event, handler)
                    if matches is None:
                        continue
                    LOGGER.debug(
                        "handler matched: plugin=%s handler=%s event=%s",
                        plugin.plugin_name,
                        handler.spec.func_name,
                        event.id,
                    )
                    ctx = Context(
                        runtime=self,
                        adapter=adapter,
                        plugin=plugin,
                        event=event,
                        handler=handler,
                        matches=matches,
                    )
                    allowed, extra_matches = await self._check_rule_and_permission(ctx, handler)
                    if not allowed:
                        LOGGER.debug(
                            "handler denied by rule or permission: plugin=%s handler=%s event=%s",
                            plugin.plugin_name,
                            handler.spec.func_name,
                            event.id,
                        )
                        continue
                    if extra_matches:
                        ctx.matches.update(extra_matches)
                    handler_jobs.append((ctx, handler, middlewares))
                    if handler.spec.block:
                        break
                if handler_jobs and handler_jobs[-1][1].spec.block:
                    break

        for ctx, handler, middlewares in handler_jobs:
            slots = self._handler_slots
            await slots.acquire()
            try:
                task = asyncio.create_task(
                    self._execute_handler_job(ctx, handler, middlewares, slots),
                    name=f"handler:{ctx.plugin.plugin_name}.{handler.spec.func_name}",
                )
            except BaseException:
                slots.release()
                raise
            self._handler_tasks.add(task)
            task.add_done_callback(self._handler_tasks.discard)
            if handler.spec.block:
                return

    async def _execute_handler_job(
        self,
        ctx: Context,
        handler: BoundHandler,
        middlewares: dict[str, list[Callable[..., Any]]],
        slots: asyncio.Semaphore,
    ) -> None:
        try:
            await self._run_handler(ctx, handler, middlewares)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception(
                "handler failed: plugin=%s handler=%s",
                ctx.plugin.plugin_name,
                handler.spec.func_name,
            )
        finally:
            slots.release()

    def load_plugins(self) -> None:
        """Load plugins from the current configuration."""
        self._apply_python_paths()
        plugins, descriptors = self._build_plugins()
        self._set_plugins(plugins, descriptors)
        self._plugin_watch_state = self._snapshot_plugin_watch_state()

    def load_adapters(self) -> None:
        """Load adapters from the current configuration."""
        adapters, adapter_map = self._build_adapters()
        self._set_adapters(adapters, adapter_map)

    def _build_adapters(self) -> tuple[list[Adapter], dict[str, Adapter]]:
        adapters: list[Adapter] = []
        adapter_map: dict[str, Adapter] = {}
        for ref in self._configured_adapter_refs():
            adapter_ref = self._resolve_adapter_ref(str(ref))
            adapter_cls = self._resolve_adapter_class(adapter_ref)
            adapter = adapter_cls(self, self.get_adapter_config(adapter_cls.name))
            adapters.append(adapter)
            adapter_map[adapter.name] = adapter
        return adapters, adapter_map

    def _configured_adapter_refs(self) -> list[str]:
        refs = [str(ref) for ref in self.runtime_config.get("adapters", [])]
        if self.runtime_config.get("auto_discover_adapters", False):
            for name in self._discover_adapter_entry_points():
                if name not in refs:
                    refs.append(name)
        return refs

    def _set_adapters(self, adapters: list[Adapter], adapter_map: dict[str, Adapter]) -> None:
        self.adapters = adapters
        self._adapter_map = adapter_map

    def _refresh_runtime_dependencies(self) -> None:
        self.register_dependency("runtime", self, annotation=Runtime)
        self.register_dependency("state", self.state, annotation=dict)
        self.register_dependency("sessions", self.sessions, annotation=SessionManager)
        self.register_dependency("state_store", self.state_store, annotation=StateStore)
        self.register_dependency("metrics", self.metrics, annotation=RuntimeMetrics)
        self.register_dependency("audit_logger", self.audit_logger, annotation=AuditLogger)

    def _configure_runtime_limits(self) -> None:
        config = self.runtime_config
        self._handler_slots = asyncio.Semaphore(int(config.get("max_concurrent_handlers", 64)))
        self.sessions.configure(
            max_backlog_keys=int(config.get("session_backlog_max_keys", 1024)),
            max_backlog_per_key=int(config.get("session_backlog_per_key", 3)),
            backlog_ttl_seconds=float(config.get("session_backlog_ttl_seconds", 300.0)),
        )

    def _start_adapters(self) -> None:
        self._adapter_tasks = [
            asyncio.create_task(
                self._run_adapter(adapter),
                name=f"adapter:{adapter.name}",
            )
            for adapter in self.adapters
        ]

    async def _stop_adapters(self, *, adapters: list[Adapter] | None = None) -> None:
        targets = adapters if adapters is not None else self.adapters
        for adapter in targets:
            with contextlib.suppress(Exception):
                await adapter.close()
        for task in self._adapter_tasks:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._adapter_tasks = []

    async def _run_adapter(self, adapter: Adapter) -> None:
        try:
            await adapter.start()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if self._stop_event.is_set() or adapter not in self.adapters:
                return
            self.count_metric("adapter_failures_total", adapter=adapter.name, outcome="error")
            self.audit(
                "adapter.failure",
                adapter=adapter.name,
                outcome="error",
                level=logging.ERROR,
                error=type(exc).__name__,
            )
            await self._adapter_failures.put(exc)

    def _apply_python_paths(self) -> None:
        for entry in self._python_path_entries:
            with contextlib.suppress(ValueError):
                sys.path.remove(entry)
        self._python_path_entries = []
        for raw_path in reversed(self.runtime_config.get("python_paths", [])):
            path = self._resolve_runtime_path(str(raw_path), expect_dir=True)
            entry = str(path)
            if entry not in sys.path:
                sys.path.insert(0, entry)
            self._python_path_entries.append(entry)

    def get_adapter(self, name: str) -> Adapter:
        """Return a loaded adapter by name."""
        return self._adapter_map[name]

    def _build_plugins(
        self, *, reload_modules: bool = False
    ) -> tuple[list[Plugin], list[PluginDescriptor]]:
        descriptors = self._discover_plugin_descriptors(reload_modules=reload_modules)
        ordered_descriptors = self._resolve_plugin_order(descriptors)
        plugins: list[Plugin] = []
        for load_index, descriptor in enumerate(ordered_descriptors):
            plugin = descriptor.plugin_cls(self)
            config_data, config_obj = validate_plugin_config(
                descriptor.plugin_cls,
                descriptor.name,
                self.get_plugin_config(descriptor.name),
            )
            plugin._config_data = config_data
            plugin._config_object = config_obj
            plugin.state = self._load_plugin_state(plugin)
            plugin.load_index = load_index
            plugin.is_builtin = descriptor.is_builtin
            plugin.plugin_ref = descriptor.ref
            plugins.append(plugin)
        return plugins, ordered_descriptors

    def _set_plugins(self, plugins: list[Plugin], descriptors: list[PluginDescriptor]) -> None:
        self.plugins = plugins
        self._plugin_descriptors = descriptors
        self._plugin_descriptor_map = {descriptor.name: descriptor for descriptor in descriptors}
        self._plugin_map = {plugin.plugin_name: plugin for plugin in plugins}

    def _load_plugin_state(self, plugin: Plugin) -> dict[str, Any]:
        if getattr(plugin, "state_scope", "memory") != "persistent":
            return plugin.state
        return self.state_store.load_plugin_state(plugin.plugin_name)

    def _save_plugin_state(self, plugin: Plugin) -> None:
        if getattr(plugin, "state_scope", "memory") != "persistent":
            return
        self.state_store.save_plugin_state(plugin.plugin_name, plugin.state)

    def _discover_plugin_descriptors(
        self, *, reload_modules: bool = False
    ) -> list[PluginDescriptor]:
        descriptors: list[PluginDescriptor] = []
        source_index = 0

        for builtin_name in self._configured_builtin_plugin_names():
            ref = BUILTIN_PLUGINS[builtin_name]
            descriptors.extend(
                self._load_plugin_descriptors(
                    ref,
                    reload_modules=reload_modules,
                    source_index_start=source_index,
                    is_builtin=True,
                )
            )
            source_index += 1

        for ref in self._configured_user_plugin_refs():
            descriptors.extend(
                self._load_plugin_descriptors(
                    ref,
                    reload_modules=reload_modules,
                    source_index_start=source_index,
                    is_builtin=False,
                )
            )
            source_index += 1

        for plugin_dir in self._configured_plugin_dirs():
            if not plugin_dir.exists():
                continue
            for path in sorted(plugin_dir.glob("*.py")):
                if path.name.startswith("_"):
                    continue
                descriptors.extend(
                    self._load_plugin_descriptors(
                        str(path),
                        reload_modules=reload_modules,
                        source_index_start=source_index,
                        is_builtin=False,
                    )
                )
                source_index += 1

        self._assert_unique_plugin_names(descriptors)
        return descriptors

    def _configured_builtin_plugin_names(self) -> list[str]:
        raw = self.runtime_config.get("builtin_plugins")
        if raw is False:
            names: list[str] = []
        elif raw is None:
            names = list(DEFAULT_BUILTIN_PLUGINS)
        else:
            names = [str(item) for item in raw]
            unknown = [name for name in names if name not in BUILTIN_PLUGINS]
            if unknown:
                raise ValueError(f"unknown builtin plugins: {', '.join(unknown)}")
        disabled = {str(item) for item in self.runtime_config.get("disable_builtin_plugins", [])}
        return [name for name in names if name in BUILTIN_PLUGINS and name not in disabled]

    def _configured_user_plugin_refs(self) -> list[str]:
        refs = [str(ref) for ref in self.runtime_config.get("plugins", [])]
        if self.runtime_config.get("auto_discover_plugins", False):
            for name in self._discover_plugin_entry_points():
                if name not in refs:
                    refs.append(name)
        return refs

    def _configured_plugin_dirs(self) -> list[Path]:
        return [
            self._resolve_runtime_path(str(path), expect_dir=True)
            for path in self.runtime_config.get("plugin_dirs", [])
        ]

    def _load_plugin_descriptors(
        self,
        ref: str,
        *,
        reload_modules: bool,
        source_index_start: int,
        is_builtin: bool,
    ) -> list[PluginDescriptor]:
        plugin_classes: list[type[Any]]
        resolved_ref = self._resolve_plugin_ref(ref)
        # Check for a file path first: avoids splitting Windows drive letters (C:\...)
        # as if they were a "module:Class" separator.
        path_candidate = self._resolve_path_candidate(resolved_ref)
        if path_candidate is not None:
            module = self._load_module_from_path(path_candidate, reload_module=reload_modules)
            plugin_classes = self._plugin_classes_from_module(module)
        elif ":" in resolved_ref:
            module_name, attr_name = resolved_ref.split(":", 1)
            path_candidate = self._resolve_path_candidate(module_name)
            if path_candidate is not None:
                module = self._load_module_from_path(path_candidate, reload_module=reload_modules)
                plugin_classes = [getattr(module, attr_name)]
            else:
                obj = self._load_module_attr(module_name, attr_name, reload_module=reload_modules)
                plugin_classes = [obj]
        else:
            module = self._load_import_module(resolved_ref, reload_module=reload_modules)
            plugin_classes = self._plugin_classes_from_module(module)

        descriptors: list[PluginDescriptor] = []
        for offset, plugin_cls in enumerate(plugin_classes):
            if not issubclass(plugin_cls, Plugin):
                continue
            plugin_name = plugin_cls.name or plugin_cls.__name__.lower()
            descriptors.append(
                PluginDescriptor(
                    name=plugin_name,
                    plugin_cls=plugin_cls,
                    ref=resolved_ref,
                    source_index=source_index_start + offset,
                    priority=int(getattr(plugin_cls, "priority", 100)),
                    description=str(getattr(plugin_cls, "description", "")),
                    requires=tuple(getattr(plugin_cls, "requires", ()) or ()),
                    optional_requires=tuple(getattr(plugin_cls, "optional_requires", ()) or ()),
                    load_after=tuple(getattr(plugin_cls, "load_after", ()) or ()),
                    load_before=tuple(getattr(plugin_cls, "load_before", ()) or ()),
                    is_builtin=is_builtin,
                )
            )
        return descriptors

    def _resolve_plugin_ref(self, ref: str) -> str:
        if ref in BUILTIN_PLUGINS:
            return BUILTIN_PLUGINS[ref]
        entry_point = self._plugin_entry_points_by_name().get(ref)
        if entry_point is not None:
            return str(entry_point.value)
        return ref

    def _resolve_adapter_ref(self, ref: str) -> str:
        if ref in BUILTIN_ADAPTERS:
            return BUILTIN_ADAPTERS[ref]
        entry_point = self._adapter_entry_points_by_name().get(ref)
        if entry_point is not None:
            return str(entry_point.value)
        return ref

    def _discover_plugin_entry_points(self) -> list[str]:
        return sorted(self._plugin_entry_points_by_name())

    def _discover_adapter_entry_points(self) -> list[str]:
        return sorted(self._adapter_entry_points_by_name())

    def _plugin_entry_points_by_name(self) -> dict[str, metadata.EntryPoint]:
        return _entry_points_by_name(PLUGIN_ENTRY_POINT_GROUP)

    def _adapter_entry_points_by_name(self) -> dict[str, metadata.EntryPoint]:
        return _entry_points_by_name(ADAPTER_ENTRY_POINT_GROUP)

    def _assert_unique_plugin_names(self, descriptors: list[PluginDescriptor]) -> None:
        owners: dict[str, str] = {}
        for descriptor in descriptors:
            ref = owners.get(descriptor.name)
            if ref is not None:
                raise ValueError(
                    f"duplicate plugin name {descriptor.name!r} found in {ref!r} and {descriptor.ref!r}"
                )
            owners[descriptor.name] = descriptor.ref

    def _resolve_plugin_order(self, descriptors: list[PluginDescriptor]) -> list[PluginDescriptor]:
        by_name = {descriptor.name: descriptor for descriptor in descriptors}
        edges: dict[str, set[str]] = {descriptor.name: set() for descriptor in descriptors}
        indegree: dict[str, int] = {descriptor.name: 0 for descriptor in descriptors}

        def add_edge(source: str, target: str) -> None:
            if source == target:
                return
            if target not in edges[source]:
                edges[source].add(target)
                indegree[target] += 1

        for descriptor in descriptors:
            for dependency_name in descriptor.requires:
                if dependency_name not in by_name:
                    raise ValueError(
                        f"plugin {descriptor.name!r} requires missing plugin {dependency_name!r}"
                    )
                add_edge(dependency_name, descriptor.name)
            for dependency_name in descriptor.optional_requires:
                if dependency_name in by_name:
                    add_edge(dependency_name, descriptor.name)
            for dependency_name in descriptor.load_after:
                if dependency_name in by_name:
                    add_edge(dependency_name, descriptor.name)
            for dependency_name in descriptor.load_before:
                if dependency_name in by_name:
                    add_edge(descriptor.name, dependency_name)

        queue = [
            descriptor.name
            for descriptor in sorted(
                descriptors,
                key=lambda item: (item.source_index, item.priority, item.name),
            )
            if indegree[descriptor.name] == 0
        ]
        resolved: list[PluginDescriptor] = []

        while queue:
            current_name = queue.pop(0)
            descriptor = by_name[current_name]
            resolved.append(descriptor)
            for target_name in sorted(
                edges[current_name],
                key=lambda name: (
                    by_name[name].source_index,
                    by_name[name].priority,
                    by_name[name].name,
                ),
            ):
                indegree[target_name] -= 1
                if indegree[target_name] == 0:
                    queue.append(target_name)
                    queue.sort(
                        key=lambda name: (
                            by_name[name].source_index,
                            by_name[name].priority,
                            by_name[name].name,
                        )
                    )

        if len(resolved) != len(descriptors):
            unresolved = sorted(name for name, degree in indegree.items() if degree > 0)
            raise ValueError(f"plugin dependency cycle detected: {', '.join(unresolved)}")

        return resolved

    def _load_module_attr(self, module_name: str, attr_name: str, *, reload_module: bool) -> Any:
        module = self._load_import_module(module_name, reload_module=reload_module)
        return getattr(module, attr_name)

    def _load_import_module(self, module_name: str, *, reload_module: bool) -> ModuleType:
        module = importlib.import_module(module_name)
        if reload_module:
            module = importlib.reload(module)
        return module

    def _resolve_path_candidate(self, ref: str) -> Path | None:
        candidate = Path(ref).expanduser()
        if candidate.is_file():
            return self._ensure_allowed_path(candidate.resolve(), ref)
        relative = (self.base_path / ref).resolve()
        if relative.is_file():
            return self._ensure_allowed_path(relative, ref)
        return None

    def _resolve_runtime_path(self, raw_path: str, *, expect_dir: bool = False) -> Path:
        candidate = Path(raw_path).expanduser()
        path = (
            candidate.resolve()
            if candidate.is_absolute()
            else (self.base_path / candidate).resolve()
        )
        path = self._ensure_allowed_path(path, raw_path)
        if expect_dir and path.exists() and not path.is_dir():
            raise ValueError(f"path {raw_path!r} must point to a directory")
        return path

    def _ensure_allowed_path(self, path: Path, raw_path: str) -> Path:
        if self.runtime_config.get("allow_external_paths", False):
            return path
        try:
            path.relative_to(self.base_path)
        except ValueError as exc:
            raise ValueError(
                f"path {raw_path!r} escapes the runtime root {self.base_path}"
            ) from exc
        return path

    def _resolve_adapter_class(self, ref: str) -> type[Adapter]:
        if ":" not in ref:
            raise ValueError(f"adapter reference must be module:Class, got {ref!r}")
        module_name, attr_name = ref.split(":", 1)
        obj = getattr(importlib.import_module(module_name), attr_name)
        if not isinstance(obj, type) or not issubclass(obj, Adapter):
            raise TypeError(f"{ref!r} is not an Adapter subclass")
        return obj

    def _plugin_classes_from_module(self, module: ModuleType) -> list[type[Plugin]]:
        plugin_classes: list[type[Plugin]] = []
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj is Plugin:
                continue
            if issubclass(obj, Plugin) and obj.__module__ == module.__name__:
                plugin_classes.append(obj)
        return plugin_classes

    def _load_module_from_path(self, path: Path, *, reload_module: bool = False) -> ModuleType:
        module_name = f"iamai.dynamic.{path.stem}_{self._stable_path_hash(path)}"
        if reload_module:
            sys.modules.pop(module_name, None)
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"unable to load module from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _stable_path_hash(self, path: Path) -> str:
        digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()
        return digest[:12]

    async def _run_handler(
        self,
        ctx: Context,
        handler: BoundHandler,
        middlewares: dict[str, list[Callable[..., Any]]],
    ) -> Any:
        cache: dict[Any, Any] = {}
        try:
            await self._run_phase("before", ctx, middlewares["before"], cache=cache)
            result = await self._run_around_phase(ctx, handler, middlewares["around"], cache=cache)
            await self._run_phase(
                "after",
                ctx,
                middlewares["after"],
                cache=cache,
                extra={"result": result},
            )
            return result
        except Exception as exc:
            suppressed = await self._run_error_phase(
                ctx,
                middlewares["error"],
                error=exc,
                cache=cache,
            )
            if suppressed:
                return None
            raise

    async def _check_rule_and_permission(
        self,
        ctx: Context,
        handler: BoundHandler,
    ) -> tuple[bool, dict[str, Any]]:
        cache: dict[Any, Any] = {}
        rule_matches: dict[str, Any] = {}
        if handler.spec.rule is not None:
            compiled_rule = ensure_rule(handler.spec.rule)
            ok, payload = await compiled_rule.evaluate(self, ctx, cache)
            if not ok:
                return False, {}
            rule_matches.update(payload)
        if handler.spec.permission is not None:
            compiled_permission = ensure_permission(handler.spec.permission)
            allowed = await compiled_permission.evaluate(self, ctx, cache)
            if not allowed:
                return False, {}
        return True, rule_matches

    async def _run_around_phase(
        self,
        ctx: Context,
        handler: BoundHandler,
        middlewares: list[Callable[..., Any]],
        *,
        cache: dict[Any, Any],
    ) -> Any:
        async def invoke_handler() -> Any:
            return await self._invoke_callable(handler.callback, ctx, cache=cache)

        call_chain = invoke_handler
        for middleware in reversed(middlewares):
            next_call = call_chain

            async def invoke_middleware(
                middleware_func: Callable[..., Any] = middleware,
                next_func: Callable[[], Any] = next_call,
            ) -> Any:
                return await self._invoke_callable(
                    middleware_func,
                    ctx,
                    extra={"call_next": next_func},
                    cache=cache,
                )

            call_chain = invoke_middleware
        return await call_chain()

    async def _run_phase(
        self,
        phase: str,
        ctx: Context,
        callbacks: list[Callable[..., Any]],
        *,
        cache: dict[Any, Any],
        extra: dict[str, Any] | None = None,
    ) -> None:
        for callback in callbacks:
            await self._invoke_callable(callback, ctx, extra=extra or {}, cache=cache)

    async def _run_error_phase(
        self,
        ctx: Context,
        callbacks: list[Callable[..., Any]],
        *,
        error: Exception,
        cache: dict[Any, Any],
    ) -> bool:
        suppressed = False
        for callback in callbacks:
            try:
                result = await self._invoke_callable(
                    callback,
                    ctx,
                    extra={"error": error},
                    cache=cache,
                )
                if result is True:
                    suppressed = True
            except Exception:
                LOGGER.exception(
                    "error middleware failed: plugin=%s handler=%s",
                    ctx.plugin.plugin_name,
                    ctx.handler.spec.func_name,
                )
        return suppressed

    def _collect_middlewares(self, plugins: list[Plugin]) -> dict[str, list[Callable[..., Any]]]:
        ordered: dict[str, list[tuple[int, int, Callable[..., Any]]]] = {
            phase: [] for phase in MIDDLEWARE_PHASES
        }
        for phase, priority, callback in self._runtime_middlewares:
            ordered[phase].append((priority, -1, callback))
        for plugin in plugins:
            for middleware in plugin.iter_middlewares():
                ordered[middleware.spec.phase].append(
                    (middleware.spec.priority, plugin.load_index, middleware.callback)
                )
        return {
            phase: [
                callback for _, _, callback in sorted(items, key=lambda item: (item[0], item[1]))
            ]
            for phase, items in ordered.items()
        }

    async def _invoke_callable(
        self,
        func: Callable[..., Any],
        ctx: Context,
        *,
        extra: dict[str, Any] | None = None,
        cache: dict[Any, Any] | None = None,
    ) -> Any:
        kwargs = await self._resolve_callable_kwargs(
            func, ctx, extra=extra or {}, cache=cache or {}
        )
        result = func(**kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    async def _resolve_callable_kwargs(
        self,
        func: Callable[..., Any],
        ctx: Context,
        *,
        extra: dict[str, Any],
        cache: dict[Any, Any],
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        for parameter in inspect.signature(func).parameters.values():
            if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            kwargs[parameter.name] = await self._resolve_parameter(
                parameter=parameter,
                ctx=ctx,
                extra=extra,
                cache=cache,
            )
        return kwargs

    async def _resolve_parameter(
        self,
        *,
        parameter: inspect.Parameter,
        ctx: Context,
        extra: dict[str, Any],
        cache: dict[Any, Any],
    ) -> Any:
        if parameter.name in extra:
            return extra[parameter.name]

        if isinstance(parameter.default, Depends):
            key = ("depends", id(parameter.default))
            if parameter.default.use_cache and key in cache:
                return cache[key]
            value = await self._resolve_depends(parameter.default, ctx, cache)
            if parameter.default.use_cache:
                cache[key] = value
            return value

        built_in = self._resolve_builtin_parameter(parameter, ctx)
        if built_in is not _MISSING:
            return built_in

        if parameter.name in ctx.matches:
            return ctx.matches[parameter.name]

        if parameter.name in self.dependencies:
            return self.dependencies[parameter.name]

        if parameter.default is not inspect.Parameter.empty:
            return parameter.default

        raise TypeError(
            f"unable to resolve parameter {parameter.name!r} for "
            f"{ctx.plugin.plugin_name}.{ctx.handler.spec.func_name}"
        )

    async def _resolve_depends(
        self, dependency: Depends, ctx: Context, cache: dict[Any, Any]
    ) -> Any:
        provider = dependency.provider
        if callable(provider):
            return await self._invoke_callable(provider, ctx, cache=cache)
        return provider

    def _resolve_builtin_parameter(self, parameter: inspect.Parameter, ctx: Context) -> Any:
        annotation = parameter.annotation
        builtins_by_name = {
            "ctx": ctx,
            "context": ctx,
            "runtime": ctx.runtime,
            "event": ctx.event,
            "adapter": ctx.adapter,
            "plugin": ctx.plugin,
            "message": ctx.event.message,
            "matches": ctx.matches,
            "state": ctx.state,
            "shared_state": ctx.shared_state,
            "runtime_state": ctx.shared_state,
            "command": ctx.command_name,
            "command_name": ctx.command_name,
            "args": ctx.args,
        }
        if parameter.name in builtins_by_name:
            return builtins_by_name[parameter.name]
        annotation_map = {
            Runtime: ctx.runtime,
            Context: ctx,
            Event: ctx.event,
            Adapter: ctx.adapter,
            Plugin: ctx.plugin,
            Message: ctx.event.message,
        }
        if annotation in annotation_map:
            return annotation_map[annotation]
        if isinstance(annotation, type) and annotation in self._typed_dependencies:
            return self._typed_dependencies[annotation]
        return _MISSING

    def _match_handler(self, event: Event, handler: BoundHandler) -> dict[str, Any] | None:
        spec = handler.spec
        if spec.adapters and event.adapter not in spec.adapters:
            return None
        if spec.event_types and event.type not in spec.event_types:
            return None
        if spec.detail_types and event.detail_type not in spec.detail_types:
            return None
        if spec.kind == "event":
            return {}
        if spec.kind == "message":
            return self._match_message(event, spec)
        if spec.kind == "command":
            return self._match_command(event, spec)
        return None

    def _match_message(self, event: Event, spec: Any) -> dict[str, Any] | None:
        text = event.text
        if spec.startswith and not any(text.startswith(prefix) for prefix in spec.startswith):
            return None
        if spec.contains and not any(token in text for token in spec.contains):
            return None
        if spec.regex is not None:
            match = re.search(spec.regex, text)
            if match is None:
                return None
            return {"regex": match, **match.groupdict()}
        return {}

    def _match_command(self, event: Event, spec: Any) -> dict[str, Any] | None:
        text = event.text.strip()
        prefixes = spec.prefixes or self.command_prefixes()
        for prefix in prefixes:
            if not text.startswith(prefix):
                continue
            body = text[len(prefix) :].strip()
            for command_name in spec.commands:
                if body == command_name:
                    return {"command": command_name, "args": "", "prefix": prefix}
                if body.startswith(f"{command_name} "):
                    return {
                        "command": command_name,
                        "args": body[len(command_name) :].strip(),
                        "prefix": prefix,
                    }
        return None

    def _configure_logging(self) -> None:
        configure_logging(self.config, base_path=self.base_path)

    def _hot_reload_enabled(self) -> bool:
        hot_reload = self.runtime_config.get("hot_reload", False)
        if isinstance(hot_reload, dict):
            return bool(hot_reload.get("enabled", True))
        return bool(hot_reload)

    def _config_hot_reload_enabled(self) -> bool:
        hot_reload = self.runtime_config.get("hot_reload", False)
        if isinstance(hot_reload, dict):
            return bool(hot_reload.get("config", True))
        return bool(hot_reload)

    def _hot_reload_interval(self) -> float:
        hot_reload = self.runtime_config.get("hot_reload", False)
        if isinstance(hot_reload, dict):
            return float(hot_reload.get("interval", 1.0))
        return 1.0

    def _start_hot_reload_task(self) -> None:
        if not self._hot_reload_enabled():
            return
        if self._hot_reload_task is not None and not self._hot_reload_task.done():
            return
        self._hot_reload_task = asyncio.create_task(
            self._watch_plugin_changes(),
            name="iamai:hot-reload",
        )

    async def _watch_plugin_changes(self) -> None:
        interval = self._hot_reload_interval()
        while not self._stop_event.is_set():
            await asyncio.sleep(interval)
            try:
                current = self._snapshot_plugin_watch_state()
                if current != self._plugin_watch_state:
                    config_path = self.config.get("__meta__", {}).get("config_path")
                    config_changed = bool(
                        config_path
                        and current.get(config_path) != self._plugin_watch_state.get(config_path)
                    )
                    if config_changed and self._config_hot_reload_enabled():
                        LOGGER.info("config changed, reloading config")
                        await self.reload_config()
                    else:
                        LOGGER.info("plugin source changed, reloading")
                        await self.reload_plugins()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception("hot reload watcher failed")

    def _snapshot_plugin_watch_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        config_path = self.config.get("__meta__", {}).get("config_path")
        if config_path:
            path = Path(config_path)
            if path.exists():
                state[str(path)] = path.stat().st_mtime_ns
        for descriptor in self._plugin_descriptors:
            # Try descriptor.ref as a file path first (handles Windows paths like C:\...)
            path_candidate = self._resolve_path_candidate(descriptor.ref)
            if path_candidate is not None:
                state[str(path_candidate)] = path_candidate.stat().st_mtime_ns
                continue
            ref_root = descriptor.ref.split(":", 1)[0]
            path_candidate = self._resolve_path_candidate(ref_root)
            if path_candidate is not None:
                state[str(path_candidate)] = path_candidate.stat().st_mtime_ns
                continue
            module = sys.modules.get(ref_root)
            module_file = getattr(module, "__file__", None)
            if module_file:
                path = Path(module_file).resolve()
                if path.exists():
                    state[str(path)] = path.stat().st_mtime_ns
        for plugin_dir in self._configured_plugin_dirs():
            state[f"dir::{plugin_dir.resolve()}"] = self._snapshot_python_tree(plugin_dir)
        for raw_path in self.runtime_config.get("python_paths", []):
            python_path = self._resolve_runtime_path(str(raw_path), expect_dir=True)
            state[f"py::{python_path.resolve()}"] = self._snapshot_python_tree(python_path)
        return state

    def _snapshot_python_tree(self, root: Path) -> str:
        entries: list[str] = []
        if root.exists():
            for path in sorted(root.rglob("*.py")):
                if path.name.startswith("_"):
                    continue
                entries.append(f"{path.relative_to(root)}:{path.stat().st_mtime_ns}")
        return "|".join(entries)


def main() -> None:
    """Run the command-line entry point."""
    parser = argparse.ArgumentParser(description="Run a iamai instance")
    parser.add_argument("--config", default="config.toml", help="Path to the TOML config file")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run", help="Run the runtime")
    subparsers.add_parser(
        "config-check", help="Validate config, plugins, adapters, and plugin config"
    )
    schema_parser = subparsers.add_parser("config-schema", help="Print plugin config JSON schema")
    schema_parser.add_argument("plugin", nargs="?", help="Plugin name")
    args = parser.parse_args()

    if args.command == "config-check":
        result = check_config(args.config)
        print(f"ok: {len(result['plugins'])} plugins")
        for warning in result["warnings"]:
            print(f"warning: {warning}")
        for plugin in result["plugins"]:
            print(f"- {plugin['name']}")
        return
    if args.command == "config-schema":
        print(
            json.dumps(dump_config_schema(args.config, args.plugin), ensure_ascii=False, indent=2)
        )
        return

    runtime = Runtime.from_config_file(args.config)
    asyncio.run(runtime.serve())


def check_config(path: str | Path) -> dict[str, Any]:
    """Validate a config file and return loaded plugin metadata plus warnings."""
    runtime = Runtime.from_config_file(path)
    runtime.load_plugins()
    runtime.load_adapters()
    return {
        "plugins": runtime.list_plugins(),
        "warnings": list(runtime.config.get("__meta__", {}).get("warnings", [])),
    }


def dump_config_schema(path: str | Path, plugin_name: str | None = None) -> dict[str, Any]:
    """Return JSON schemas for all plugin configs or one selected plugin."""
    runtime = Runtime.from_config_file(path)
    runtime.load_plugins()
    if plugin_name is not None:
        return runtime.get_plugin_schema(plugin_name) or {}
    return {
        info["name"]: schema
        for info in runtime.list_plugins()
        if (schema := runtime.get_plugin_schema(info["name"])) is not None
    }


def _entry_points_by_name(group: str) -> dict[str, metadata.EntryPoint]:
    selected = metadata.entry_points().select(group=group)
    return {entry_point.name: entry_point for entry_point in selected}


class _NullPlugin(Plugin):
    name = "session"


def _noop_handler(ctx: Context) -> None:
    return None


_NULL_HANDLER = BoundHandler(
    plugin=_NullPlugin.__new__(_NullPlugin),
    spec=HandlerSpec(func_name="session_waiter", kind="event"),
    callback=_noop_handler,
)


_MISSING = object()
