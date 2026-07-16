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
from collections import deque
from collections.abc import Coroutine
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from .adapter import Adapter
from .config import load_config, redact_config_value
from .config_schema import build_config_schema
from .contract import ADAPTER_ENTRY_POINT_GROUP, PLUGIN_ENTRY_POINT_GROUP
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


class ExtensionDiscoveryError(RuntimeError):
    """Stable error raised when an installed extension cannot be discovered."""

    def __init__(
        self,
        *,
        code: str,
        group: str,
        entry_point: str,
        distributions: tuple[str, ...],
        reason: str,
    ) -> None:
        self.code = code
        self.group = group
        self.entry_point = entry_point
        self.distributions = tuple(sorted(distributions))
        self.reason = reason
        distribution = ",".join(self.distributions) or "unknown"
        super().__init__(
            "extension discovery failed: "
            f"code={code}; group={group}; entry_point={entry_point}; "
            f"distribution={distribution}; reason={reason}"
        )


@dataclass(frozen=True, slots=True)
class _InstalledEntryPoint:
    group: str
    name: str
    value: str
    distribution: str
    raw: Any


@dataclass(frozen=True, slots=True)
class _ResolvedExtensionRef:
    ref: str
    entry_point: _InstalledEntryPoint | None = None


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


@dataclass(frozen=True, slots=True)
class _AdapterDescriptor:
    """Resolved adapter metadata used for construction and schema export."""

    name: str
    adapter_cls: type[Adapter]
    ref: str
    is_builtin: bool = False


@dataclass(frozen=True, slots=True)
class _HandlerJob:
    ctx: Context
    handler: BoundHandler
    middlewares: dict[str, list[Callable[..., Any]]]
    generation: int


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
        self._adapter_descriptors: list[_AdapterDescriptor] = []
        self._plugin_map: dict[str, Plugin] = {}
        self._plugin_descriptors: list[PluginDescriptor] = []
        self._plugin_descriptor_map: dict[str, PluginDescriptor] = {}
        self._adapter_tasks: list[asyncio.Task[None]] = []
        self._active_adapter_ids: set[int] = set()
        self._adapter_failures: asyncio.Queue[BaseException] = asyncio.Queue()
        self._dispatch_tasks: set[asyncio.Task[list[_HandlerJob]]] = set()
        self._handler_tasks: set[asyncio.Task[None]] = set()
        self._pending_handler_jobs: deque[_HandlerJob] = deque()
        self._handler_generation = 0
        self._accepting_handlers = True
        self._max_concurrent_handlers = 1
        self._max_pending_handlers = 1
        self._handler_shutdown_timeout_seconds = 5.0
        self._stop_event = asyncio.Event()
        self._bootstrapped = False
        self._serving = False
        self._runtime_lock = asyncio.Lock()
        self._lifecycle_lock = asyncio.Lock()
        self._lifecycle_requests: set[asyncio.Task[None]] = set()
        self._shutdown_complete = False
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
            "dispatch_tasks": len(self._dispatch_tasks),
            "handler_tasks": len(self._handler_tasks),
            "handler_backlog": len(self._pending_handler_jobs),
            "handler_backlog_capacity": self._max_pending_handlers,
            "handler_capacity": self._handler_capacity(),
            "adapters": len(self.adapters),
            "hot_reload": self._hot_reload_enabled(),
            "sessions": len(self.list_sessions()),
            "state_store": self.state_store.__class__.__name__,
            "metric_series": len(self.metrics.series()),
            "audit_logger": self.audit_logger.logger_name,
        }

    def get_plugin_schema(self, plugin_name: str) -> dict[str, Any] | None:
        """Return a plugin configuration JSON schema, if available."""
        self._apply_python_paths()
        descriptor = self._plugin_descriptor_map.get(plugin_name)
        if descriptor is None:
            descriptor = next(
                (
                    item
                    for item in self._discover_plugin_descriptors()
                    if item.name == plugin_name
                ),
                None,
            )
        if descriptor is None:
            return None
        return plugin_config_schema(descriptor.plugin_cls)

    def config_schema(self) -> dict[str, Any]:
        """Return the versioned root configuration JSON Schema."""
        self._apply_python_paths()
        adapter_descriptors = self._adapter_descriptors or self._discover_adapter_descriptors()
        plugin_descriptors = self._plugin_descriptors or self._resolve_plugin_order(
            self._discover_plugin_descriptors()
        )
        return build_config_schema(
            adapters={
                descriptor.name: descriptor.adapter_cls
                for descriptor in adapter_descriptors
            },
            plugins={
                descriptor.name: descriptor.plugin_cls for descriptor in plugin_descriptors
            },
        )

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
        started_plugins: list[Plugin] = []
        try:
            for plugin in self.plugins:
                await plugin.startup()
                started_plugins.append(plugin)
        except BaseException:
            await self._close_adapters(self.adapters)
            await self._shutdown_plugins(started_plugins, save_state=False)
            raise
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
        async with self._lifecycle_lock:
            if self._shutdown_complete:
                return
            await self._pause_handler_dispatch(cancel_active=True)
            async with self._runtime_lock:
                if self._hot_reload_task is not None:
                    self._hot_reload_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await self._hot_reload_task
                    self._hot_reload_task = None
                await self._stop_adapters()
                await self._shutdown_plugins(self.plugins, save_state=True)
                self._shutdown_complete = True
        await self._cancel_lifecycle_requests()

    async def stop(self) -> None:
        """Request graceful process shutdown."""
        self._stop_event.set()

    async def reload_plugins(self) -> None:
        """Reload user plugins while keeping the current adapter set."""
        self._ensure_lifecycle_outside_handler()
        async with self._lifecycle_lock:
            self._ensure_runtime_running()
            try:
                await self._pause_handler_dispatch(cancel_active=False)
                async with self._runtime_lock:
                    await self._reload_plugins_locked()
            finally:
                self._resume_handler_dispatch()

    async def _reload_plugins_locked(self) -> None:
        LOGGER.info("reloading plugins")
        for plugin in self.plugins:
            self._save_plugin_state(plugin)
        old_plugins = self.plugins
        old_descriptors = self._plugin_descriptors
        try:
            new_plugins, descriptors = self._build_plugins(reload_modules=True)
            started_plugins: list[Plugin] = []
            self._set_plugins(new_plugins, descriptors)
            try:
                for plugin in new_plugins:
                    await plugin.startup()
                    started_plugins.append(plugin)
                new_watch_state = self._snapshot_plugin_watch_state()
            except BaseException:
                await self._shutdown_plugins(started_plugins, save_state=False)
                self._set_plugins(old_plugins, old_descriptors)
                raise
            self._plugin_watch_state = new_watch_state
            await self._shutdown_plugins(old_plugins, save_state=False)
            LOGGER.info("reloaded %s plugins", len(self.plugins))
            self.count_metric("runtime_reload_total", action="plugins", outcome="ok")
            self.audit("runtime.reload", target="plugins", outcome="ok", plugins=len(self.plugins))
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
        self._ensure_lifecycle_outside_handler()
        async with self._lifecycle_lock:
            self._ensure_runtime_running()
            try:
                await self._pause_handler_dispatch(cancel_active=False)
                async with self._runtime_lock:
                    await self._reload_config_locked(str(config_path))
            finally:
                self._resume_handler_dispatch()

    async def _reload_config_locked(self, config_path: str) -> None:
        LOGGER.info("reloading config from %s", config_path)
        for plugin in self.plugins:
            self._save_plugin_state(plugin)
        old_config = self.config
        old_base_path = self.base_path
        old_state_store = self.state_store
        old_dependencies = dict(self.dependencies)
        old_typed_dependencies = dict(self._typed_dependencies)
        old_plugins = self.plugins
        old_descriptors = self._plugin_descriptors
        old_adapters = self.adapters
        old_adapter_map = self._adapter_map
        old_adapter_descriptors = self._adapter_descriptors
        old_runtime_limits = (
            self._max_concurrent_handlers,
            self._max_pending_handlers,
            self._handler_shutdown_timeout_seconds,
        )
        old_session_limits = (
            self.sessions._max_backlog_keys,
            self.sessions._max_backlog_per_key,
            self.sessions._backlog_ttl_seconds,
        )
        started_plugins: list[Plugin] = []
        new_adapters: list[Adapter] = []

        try:
            try:
                self.config = load_config(config_path)
                self.base_path = Path(self.config["__meta__"]["root_dir"])
                self.state_store = create_state_store(self.config, base_path=self.base_path)
                self._refresh_runtime_dependencies()
                self._apply_python_paths()
                new_plugins, descriptors = self._build_plugins(reload_modules=True)
                new_adapters, adapter_map, adapter_descriptors = self._build_adapters()
                self._set_plugins(new_plugins, descriptors)
                self._set_adapters(new_adapters, adapter_map, adapter_descriptors)
                for plugin in new_plugins:
                    await plugin.startup()
                    started_plugins.append(plugin)
                self._configure_runtime_limits()
                new_watch_state = self._snapshot_plugin_watch_state()
            except BaseException:
                await self._close_adapters(new_adapters)
                await self._shutdown_plugins(started_plugins, save_state=False)
                self.config = old_config
                self.base_path = old_base_path
                self.state_store = old_state_store
                self.dependencies = old_dependencies
                self._typed_dependencies = old_typed_dependencies
                self._set_plugins(old_plugins, old_descriptors)
                self._set_adapters(old_adapters, old_adapter_map, old_adapter_descriptors)
                (
                    self._max_concurrent_handlers,
                    self._max_pending_handlers,
                    self._handler_shutdown_timeout_seconds,
                ) = old_runtime_limits
                with contextlib.suppress(Exception, asyncio.CancelledError):
                    self.sessions.configure(
                        max_backlog_keys=old_session_limits[0],
                        max_backlog_per_key=old_session_limits[1],
                        backlog_ttl_seconds=old_session_limits[2],
                    )
                with contextlib.suppress(Exception, asyncio.CancelledError):
                    self._apply_python_paths()
                raise

            await self._stop_adapters(adapters=old_adapters)
            if self._serving:
                self._start_adapters()
            self._plugin_watch_state = new_watch_state
            await self._shutdown_plugins(old_plugins, save_state=False)
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

    async def dispatch(self, event: Event, adapter: Adapter) -> bool:
        """Dispatch one event, returning whether all matched handlers were admitted.

        Handler admission is atomic per event. If the complete matched handler set
        cannot fit within the configured capacity, none of its handlers are scheduled.
        """
        if event.type == "meta_event":
            LOGGER.debug(
                "event[%s] %s/%s text=%r",
                event.id,
                event.adapter,
                event.type,
                event.text,
            )
        else:
            LOGGER.info(
                "event[%s] %s/%s text=%r",
                event.id,
                event.adapter,
                event.type,
                event.text,
            )
        if not self._try_admit_dispatch():
            return False
        evaluation = asyncio.create_task(
            self._evaluate_dispatch(event, adapter),
            name=f"dispatch:{event.id}",
        )
        self._dispatch_tasks.add(evaluation)
        try:
            handler_jobs = await asyncio.shield(evaluation)
        except asyncio.CancelledError:
            if evaluation.cancelled():
                return False
            evaluation.cancel()
            await asyncio.gather(evaluation, return_exceptions=True)
            raise
        finally:
            self._dispatch_tasks.discard(evaluation)

        return self._schedule_handler_jobs_atomically(handler_jobs)

    async def _evaluate_dispatch(self, event: Event, adapter: Adapter) -> list[_HandlerJob]:
        """Evaluate sessions, rules, and permissions for one admitted event."""
        handler_jobs: list[_HandlerJob] = []
        async with self._runtime_lock:
            generation = self._handler_generation
            plugins = list(self.plugins)
            middlewares = self._collect_middlewares(plugins)
            waiter_ctx = Context(
                runtime=self,
                adapter=adapter,
                plugin=plugins[0] if plugins else _NullPlugin(self),
                event=event,
                handler=_NULL_HANDLER,
                matches={},
                _generation=generation,
            )
            if await self.sessions.consume(waiter_ctx):
                return handler_jobs
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
                        _generation=generation,
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
                    handler_jobs.append(_HandlerJob(ctx, handler, middlewares, generation))
                    if handler.spec.block:
                        break
                if handler_jobs and handler_jobs[-1].handler.spec.block:
                    break
        return handler_jobs

    async def _execute_handler_job(
        self,
        ctx: Context,
        handler: BoundHandler,
        middlewares: dict[str, list[Callable[..., Any]]],
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

    def _schedule_handler_job(self, job: _HandlerJob) -> None:
        if not self._accepting_handlers or job.generation != self._handler_generation:
            self.count_metric("runtime_handler_dropped_total", reason="stale_generation")
            return
        if self._handler_load() >= self._handler_capacity():
            self.count_metric("runtime_handler_dropped_total", reason="queue_full")
            return
        if len(self._handler_tasks) < self._max_concurrent_handlers:
            self._start_handler_job(job)
            return
        if len(self._pending_handler_jobs) < self._max_pending_handlers:
            self._pending_handler_jobs.append(job)
            return
        self.count_metric("runtime_handler_dropped_total", reason="queue_full")

    def _schedule_handler_jobs_atomically(self, jobs: list[_HandlerJob]) -> bool:
        if not jobs:
            return True
        if not self._accepting_handlers or any(
            job.generation != self._handler_generation for job in jobs
        ):
            self.count_metric(
                "runtime_handler_dropped_total",
                value=len(jobs),
                reason="stale_generation",
            )
            return False
        if self._handler_load() + len(jobs) > self._handler_capacity():
            self.count_metric(
                "runtime_handler_dropped_total",
                value=len(jobs),
                reason="queue_full",
            )
            return False
        for job in jobs:
            self._schedule_handler_job(job)
        return True

    def _try_admit_dispatch(self) -> bool:
        if not self._accepting_handlers or self._stop_event.is_set():
            self.count_metric("runtime_handler_dropped_total", reason="lifecycle")
            return False
        if self._handler_load() >= self._handler_capacity():
            self.count_metric("runtime_handler_dropped_total", reason="queue_full")
            return False
        return True

    def _handler_load(self) -> int:
        return (
            len(self._dispatch_tasks) + len(self._handler_tasks) + len(self._pending_handler_jobs)
        )

    def _handler_capacity(self) -> int:
        return self._max_concurrent_handlers + self._max_pending_handlers

    def _start_handler_job(self, job: _HandlerJob) -> None:
        task = asyncio.create_task(
            self._execute_handler_job(job.ctx, job.handler, job.middlewares),
            name=f"handler:{job.ctx.plugin.plugin_name}.{job.handler.spec.func_name}",
        )
        self._handler_tasks.add(task)
        task.add_done_callback(self._handler_job_done)

    def _handler_job_done(self, task: asyncio.Task[None]) -> None:
        self._handler_tasks.discard(task)
        if not self._accepting_handlers:
            return
        while (
            self._pending_handler_jobs and len(self._handler_tasks) < self._max_concurrent_handlers
        ):
            job = self._pending_handler_jobs.popleft()
            if job.generation != self._handler_generation:
                self.count_metric("runtime_handler_dropped_total", reason="stale_generation")
                continue
            self._start_handler_job(job)

    async def _pause_handler_dispatch(self, *, cancel_active: bool) -> None:
        self._ensure_lifecycle_outside_handler()
        self._accepting_handlers = False
        if cancel_active:
            self._handler_generation += 1
            self.sessions.discard_stale_contexts()
        dispatch_tasks = [task for task in self._dispatch_tasks if not task.done()]
        if dispatch_tasks:
            self.count_metric(
                "runtime_handler_dropped_total",
                value=len(dispatch_tasks),
                reason="lifecycle",
            )
        for dispatch_task in dispatch_tasks:
            dispatch_task.cancel()
        if dispatch_tasks:
            await asyncio.gather(*dispatch_tasks, return_exceptions=True)
            for dispatch_task in dispatch_tasks:
                self._dispatch_tasks.discard(dispatch_task)
        if self._pending_handler_jobs:
            self.count_metric(
                "runtime_handler_dropped_total",
                value=len(self._pending_handler_jobs),
                reason="lifecycle",
            )
            self._pending_handler_jobs.clear()
        tasks = list(self._handler_tasks)
        if tasks:
            if cancel_active:
                self.count_metric(
                    "runtime_handler_dropped_total",
                    value=len(tasks),
                    reason="lifecycle",
                )
                for handler_task in tasks:
                    handler_task.cancel()
            else:
                _, pending = await asyncio.wait(
                    tasks,
                    timeout=self._handler_shutdown_timeout_seconds,
                )
                if pending:
                    self.count_metric(
                        "runtime_handler_dropped_total",
                        value=len(pending),
                        reason="lifecycle",
                    )
                for handler_task in pending:
                    handler_task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        if not cancel_active:
            self._handler_generation += 1
            self.sessions.discard_stale_contexts()

    def _resume_handler_dispatch(self) -> None:
        if not self._stop_event.is_set():
            self._accepting_handlers = True

    def request_plugin_reload(self) -> None:
        """Schedule a plugin reload outside the current handler task."""
        self._schedule_lifecycle_request(self.reload_plugins(), name="iamai:reload-plugins")

    def request_config_reload(self) -> None:
        """Schedule a configuration reload outside the current handler task."""
        self._schedule_lifecycle_request(self.reload_config(), name="iamai:reload-config")

    def _schedule_lifecycle_request(
        self,
        coro: Coroutine[Any, Any, None],
        *,
        name: str,
    ) -> None:
        task = asyncio.create_task(coro, name=name)
        self._lifecycle_requests.add(task)
        task.add_done_callback(self._lifecycle_request_done)

    def _lifecycle_request_done(self, task: asyncio.Task[None]) -> None:
        self._lifecycle_requests.discard(task)
        if task.cancelled():
            return
        try:
            task.result()
        except Exception:
            LOGGER.exception("background runtime lifecycle request failed")

    async def _cancel_lifecycle_requests(self) -> None:
        current = asyncio.current_task()
        tasks = [task for task in self._lifecycle_requests if task is not current]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _ensure_lifecycle_outside_handler(self) -> None:
        if asyncio.current_task() in self._handler_tasks:
            raise RuntimeError("runtime lifecycle operations must be scheduled outside handlers")

    def _ensure_runtime_running(self) -> None:
        if self._stop_event.is_set():
            raise RuntimeError("runtime is shutting down")

    def load_plugins(self) -> None:
        """Load plugins from the current configuration."""
        self._apply_python_paths()
        plugins, descriptors = self._build_plugins()
        self._set_plugins(plugins, descriptors)
        self._plugin_watch_state = self._snapshot_plugin_watch_state()

    def load_adapters(self) -> None:
        """Load adapters from the current configuration."""
        adapters, adapter_map, descriptors = self._build_adapters()
        self._set_adapters(adapters, adapter_map, descriptors)

    def _build_adapters(
        self,
    ) -> tuple[list[Adapter], dict[str, Adapter], list[_AdapterDescriptor]]:
        adapters: list[Adapter] = []
        adapter_map: dict[str, Adapter] = {}
        descriptors = self._discover_adapter_descriptors()
        for descriptor in descriptors:
            adapter_cls = descriptor.adapter_cls
            adapter = adapter_cls(self, self.get_adapter_config(descriptor.name))
            adapters.append(adapter)
            adapter_map[adapter.name] = adapter
        return adapters, adapter_map, descriptors

    def _discover_adapter_descriptors(self) -> list[_AdapterDescriptor]:
        descriptors: list[_AdapterDescriptor] = []
        for ref in self._configured_adapter_refs():
            resolved = self._resolve_adapter_ref(str(ref))
            if resolved.entry_point is None:
                adapter_cls = self._resolve_adapter_class(resolved.ref)
            else:
                adapter_cls = self._load_installed_extension(
                    resolved.entry_point,
                    expected=Adapter,
                    kind="Adapter",
                )
            name = adapter_cls.name or adapter_cls.__name__.lower()
            descriptors.append(
                _AdapterDescriptor(
                    name=name,
                    adapter_cls=adapter_cls,
                    ref=resolved.ref,
                    is_builtin=str(ref) in BUILTIN_ADAPTERS,
                )
            )
        self._assert_unique_adapter_names(descriptors)
        return descriptors

    def _configured_adapter_refs(self) -> list[str]:
        refs = [str(ref) for ref in self.runtime_config.get("adapters", [])]
        if self.runtime_config.get("auto_discover_adapters", False):
            for name in self._discover_adapter_entry_points():
                if name not in refs:
                    refs.append(name)
        return refs

    def _set_adapters(
        self,
        adapters: list[Adapter],
        adapter_map: dict[str, Adapter],
        descriptors: list[_AdapterDescriptor],
    ) -> None:
        self.adapters = adapters
        self._adapter_map = adapter_map
        self._adapter_descriptors = descriptors

    def _refresh_runtime_dependencies(self) -> None:
        self.register_dependency("runtime", self, annotation=Runtime)
        self.register_dependency("state", self.state, annotation=dict)
        self.register_dependency("sessions", self.sessions, annotation=SessionManager)
        self.register_dependency("state_store", self.state_store, annotation=StateStore)
        self.register_dependency("metrics", self.metrics, annotation=RuntimeMetrics)
        self.register_dependency("audit_logger", self.audit_logger, annotation=AuditLogger)

    def _configure_runtime_limits(self) -> None:
        config = self.runtime_config
        self._max_concurrent_handlers = int(config.get("max_concurrent_handlers", 64))
        self._max_pending_handlers = int(config.get("max_pending_handlers", 256))
        self._handler_shutdown_timeout_seconds = float(
            config.get("handler_shutdown_timeout_seconds", 5.0)
        )
        self.sessions.configure(
            max_backlog_keys=int(config.get("session_backlog_max_keys", 1024)),
            max_backlog_per_key=int(config.get("session_backlog_per_key", 3)),
            backlog_ttl_seconds=float(config.get("session_backlog_ttl_seconds", 300.0)),
        )

    def _start_adapters(self) -> None:
        self._active_adapter_ids.update(id(adapter) for adapter in self.adapters)
        self._adapter_tasks = [
            asyncio.create_task(
                self._run_adapter(adapter),
                name=f"adapter:{adapter.name}",
            )
            for adapter in self.adapters
        ]

    async def _stop_adapters(self, *, adapters: list[Adapter] | None = None) -> None:
        targets = adapters if adapters is not None else self.adapters
        self._active_adapter_ids.difference_update(id(adapter) for adapter in targets)
        await self._close_adapters(targets)
        for task in self._adapter_tasks:
            if not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await task
        self._adapter_tasks = []

    async def _close_adapters(self, adapters: list[Adapter]) -> None:
        for adapter in adapters:
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await adapter.close()

    async def _shutdown_plugins(
        self,
        plugins: list[Plugin],
        *,
        save_state: bool,
    ) -> None:
        for plugin in reversed(plugins):
            if save_state:
                with contextlib.suppress(Exception, asyncio.CancelledError):
                    self._save_plugin_state(plugin)
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await plugin.shutdown()

    async def _run_adapter(self, adapter: Adapter) -> None:
        try:
            await adapter.start()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if self._stop_event.is_set() or id(adapter) not in self._active_adapter_ids:
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
        resolved = self._resolve_plugin_ref(ref)
        resolved_ref = resolved.ref
        if resolved.entry_point is not None:
            plugin_classes = [
                self._load_installed_extension(
                    resolved.entry_point,
                    expected=Plugin,
                    kind="Plugin",
                    reload_module=reload_modules,
                )
            ]
        # Check for a file path first: avoids splitting Windows drive letters (C:\...)
        # as if they were a "module:Class" separator.
        elif (path_candidate := self._resolve_path_candidate(resolved_ref)) is not None:
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

    def _resolve_plugin_ref(self, ref: str) -> _ResolvedExtensionRef:
        entry_point = self._select_entry_point(
            self._plugin_entry_points_by_name(),
            group=PLUGIN_ENTRY_POINT_GROUP,
            name=ref,
            reserved=BUILTIN_PLUGINS,
        )
        if ref in BUILTIN_PLUGINS:
            return _ResolvedExtensionRef(BUILTIN_PLUGINS[ref])
        if entry_point is not None:
            return _ResolvedExtensionRef(entry_point.value, entry_point)
        return _ResolvedExtensionRef(ref)

    def _resolve_adapter_ref(self, ref: str) -> _ResolvedExtensionRef:
        entry_point = self._select_entry_point(
            self._adapter_entry_points_by_name(),
            group=ADAPTER_ENTRY_POINT_GROUP,
            name=ref,
            reserved=BUILTIN_ADAPTERS,
        )
        if ref in BUILTIN_ADAPTERS:
            return _ResolvedExtensionRef(BUILTIN_ADAPTERS[ref])
        if entry_point is not None:
            return _ResolvedExtensionRef(entry_point.value, entry_point)
        return _ResolvedExtensionRef(ref)

    def _discover_plugin_entry_points(self) -> list[str]:
        return self._discover_entry_point_names(
            self._plugin_entry_points_by_name(),
            group=PLUGIN_ENTRY_POINT_GROUP,
            reserved=BUILTIN_PLUGINS,
        )

    def _discover_adapter_entry_points(self) -> list[str]:
        return self._discover_entry_point_names(
            self._adapter_entry_points_by_name(),
            group=ADAPTER_ENTRY_POINT_GROUP,
            reserved=BUILTIN_ADAPTERS,
        )

    def _plugin_entry_points_by_name(self) -> dict[str, tuple[_InstalledEntryPoint, ...]]:
        return _entry_points_by_name(PLUGIN_ENTRY_POINT_GROUP)

    def _adapter_entry_points_by_name(self) -> dict[str, tuple[_InstalledEntryPoint, ...]]:
        return _entry_points_by_name(ADAPTER_ENTRY_POINT_GROUP)

    def _discover_entry_point_names(
        self,
        entry_points: dict[str, Any],
        *,
        group: str,
        reserved: dict[str, str],
    ) -> list[str]:
        for name in sorted(entry_points):
            self._select_entry_point(
                entry_points,
                group=group,
                name=name,
                reserved=reserved,
            )
        return sorted(entry_points)

    def _select_entry_point(
        self,
        entry_points: dict[str, Any],
        *,
        group: str,
        name: str,
        reserved: dict[str, str],
    ) -> _InstalledEntryPoint | None:
        raw_candidates = entry_points.get(name)
        if raw_candidates is None:
            return None
        candidates = _coerce_entry_point_candidates(raw_candidates, group=group, name=name)
        distributions = tuple(candidate.distribution for candidate in candidates)
        if name in reserved:
            raise ExtensionDiscoveryError(
                code="reserved_entry_point",
                group=group,
                entry_point=name,
                distributions=distributions,
                reason="entry point name is reserved by a built-in extension",
            )
        if len(candidates) != 1:
            raise ExtensionDiscoveryError(
                code="duplicate_entry_point",
                group=group,
                entry_point=name,
                distributions=distributions,
                reason="multiple installed distributions publish the same entry point",
            )
        return candidates[0]

    def _load_installed_extension(
        self,
        entry_point: _InstalledEntryPoint,
        *,
        expected: type[Any],
        kind: str,
        reload_module: bool = False,
    ) -> type[Any]:
        try:
            if reload_module:
                module_name, attr_name = _entry_point_target(entry_point)
                obj = self._load_module_attr(
                    module_name,
                    attr_name,
                    reload_module=True,
                )
            elif callable(getattr(entry_point.raw, "load", None)):
                obj = entry_point.raw.load()
            else:
                module_name, attr_name = _entry_point_target(entry_point)
                obj = self._load_module_attr(module_name, attr_name, reload_module=False)
        except Exception as exc:
            raise ExtensionDiscoveryError(
                code="load_failed",
                group=entry_point.group,
                entry_point=entry_point.name,
                distributions=(entry_point.distribution,),
                reason=f"entry point load raised {type(exc).__name__}: {exc}",
            ) from exc
        if not isinstance(obj, type) or not issubclass(obj, expected):
            article = "an" if kind.startswith(("A", "E", "I", "O", "U")) else "a"
            raise ExtensionDiscoveryError(
                code="invalid_object",
                group=entry_point.group,
                entry_point=entry_point.name,
                distributions=(entry_point.distribution,),
                reason=f"loaded object is not {article} {kind} subclass",
            )
        extension_name = getattr(obj, "name", "") or obj.__name__.lower()
        if extension_name != entry_point.name:
            raise ExtensionDiscoveryError(
                code="name_mismatch",
                group=entry_point.group,
                entry_point=entry_point.name,
                distributions=(entry_point.distribution,),
                reason=f"loaded {kind}.name is {extension_name!r}",
            )
        return obj

    def _assert_unique_plugin_names(self, descriptors: list[PluginDescriptor]) -> None:
        owners: dict[str, str] = {}
        for descriptor in descriptors:
            ref = owners.get(descriptor.name)
            if ref is not None:
                raise ValueError(
                    f"duplicate plugin name {descriptor.name!r} found in {ref!r} and {descriptor.ref!r}"
                )
            owners[descriptor.name] = descriptor.ref

    def _assert_unique_adapter_names(self, descriptors: list[_AdapterDescriptor]) -> None:
        owners: dict[str, str] = {}
        for descriptor in descriptors:
            ref = owners.get(descriptor.name)
            if ref is not None:
                raise ValueError(
                    f"duplicate adapter name {descriptor.name!r} found in "
                    f"{ref!r} and {descriptor.ref!r}"
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
        obj: Any = module
        for part in attr_name.split("."):
            obj = getattr(obj, part)
        return obj

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
            func,
            ctx,
            extra=extra or {},
            cache=cache if cache is not None else {},
        )
        ctx._assert_current()
        result = func(**kwargs)
        if inspect.isawaitable(result):
            result = await result
            ctx._assert_current()
        return result

    async def _resolve_callable_kwargs(
        self,
        func: Callable[..., Any],
        ctx: Context,
        *,
        extra: dict[str, Any],
        cache: dict[Any, Any],
    ) -> dict[str, Any]:
        ctx._assert_current()
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
            ctx._assert_current()
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
    """Return the root config schema or one selected plugin schema."""
    runtime = Runtime.from_config_file(path)
    if plugin_name is not None:
        return runtime.get_plugin_schema(plugin_name) or {}
    return runtime.config_schema()


def _entry_points_by_name(group: str) -> dict[str, tuple[_InstalledEntryPoint, ...]]:
    selected = metadata.entry_points().select(group=group)
    grouped: dict[str, list[_InstalledEntryPoint]] = {}
    for entry_point in selected:
        installed = _coerce_installed_entry_point(entry_point, group=group)
        grouped.setdefault(installed.name, []).append(installed)
    return {
        name: tuple(sorted(items, key=lambda item: (item.distribution, item.value)))
        for name, items in sorted(grouped.items())
    }


def _coerce_entry_point_candidates(
    raw: Any,
    *,
    group: str,
    name: str,
) -> tuple[_InstalledEntryPoint, ...]:
    candidates = raw if isinstance(raw, (tuple, list)) else (raw,)
    return tuple(
        candidate
        if isinstance(candidate, _InstalledEntryPoint)
        else _coerce_installed_entry_point(candidate, group=group, name=name)
        for candidate in candidates
    )


def _coerce_installed_entry_point(
    entry_point: Any,
    *,
    group: str,
    name: str | None = None,
) -> _InstalledEntryPoint:
    return _InstalledEntryPoint(
        group=str(getattr(entry_point, "group", group)),
        name=str(name or entry_point.name),
        value=str(entry_point.value),
        distribution=_entry_point_distribution(entry_point),
        raw=entry_point,
    )


def _entry_point_distribution(entry_point: Any) -> str:
    distribution = getattr(entry_point, "dist", None)
    if distribution is None:
        return "unknown"
    distribution_name = distribution.metadata.get("Name") or getattr(
        distribution, "name", "unknown"
    )
    version = getattr(distribution, "version", None)
    return f"{distribution_name}=={version}" if version else str(distribution_name)


def _entry_point_target(entry_point: _InstalledEntryPoint) -> tuple[str, str]:
    module_name = getattr(entry_point.raw, "module", None)
    attr_name = getattr(entry_point.raw, "attr", None)
    if module_name and attr_name:
        return str(module_name), str(attr_name)
    target = entry_point.value.partition(" [")[0]
    module_name, separator, attr_name = target.partition(":")
    if not separator or not module_name or not attr_name:
        raise ValueError(f"entry point value must be module:attribute, got {entry_point.value!r}")
    return module_name, attr_name


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
