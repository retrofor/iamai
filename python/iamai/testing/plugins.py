"""Conformance helpers for third-party iamai plugins."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from iamai.context import Context
from iamai.plugin import BoundHandler, Plugin
from iamai.validation import validate_plugin_config

CleanupCheck = Callable[[], bool | Awaitable[bool]]


class PluginConformanceError(AssertionError):
    """Raised when a plugin fails a conformance helper."""


def assert_plugin_metadata(plugin_cls: type[Any]) -> None:
    """Assert that a plugin class exposes valid public metadata."""
    if not isinstance(plugin_cls, type) or not issubclass(plugin_cls, Plugin):
        raise PluginConformanceError("plugin class must inherit from iamai.Plugin")

    _effective_plugin_name(plugin_cls)

    description = getattr(plugin_cls, "description", "")
    if not isinstance(description, str):
        raise PluginConformanceError("plugin description must be a string")

    priority = getattr(plugin_cls, "priority", 100)
    if type(priority) is not int:
        raise PluginConformanceError("plugin priority must be an integer")

    state_scope = getattr(plugin_cls, "state_scope", "memory")
    if state_scope not in {"memory", "persistent"}:
        raise PluginConformanceError("plugin state_scope must be either 'memory' or 'persistent'")


def assert_plugin_config(
    plugin_cls: type[Any],
    raw_config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Any | None]:
    """Validate plugin configuration and return its normalized forms."""
    assert_plugin_metadata(plugin_cls)
    plugin_name = _effective_plugin_name(plugin_cls)
    try:
        return validate_plugin_config(plugin_cls, plugin_name, raw_config)
    except Exception as exc:
        raise PluginConformanceError(
            f"plugin {plugin_name!r} configuration is invalid: {exc}"
        ) from exc


def assert_plugin_dependencies(plugin_cls: type[Any]) -> None:
    """Assert that plugin dependency and ordering declarations are well formed."""
    assert_plugin_metadata(plugin_cls)
    plugin_name = _effective_plugin_name(plugin_cls)
    declarations: dict[str, tuple[str, ...]] = {}

    for attribute in ("requires", "optional_requires", "load_after", "load_before"):
        value = getattr(plugin_cls, attribute, ())
        if not isinstance(value, tuple):
            raise PluginConformanceError(f"plugin {attribute} must be a tuple of plugin names")
        if any(not isinstance(item, str) or not item or item != item.strip() for item in value):
            raise PluginConformanceError(
                f"plugin {attribute} must contain only non-empty trimmed strings"
            )
        if len(value) != len(set(value)):
            raise PluginConformanceError(f"plugin {attribute} must not contain duplicates")
        if plugin_name in value:
            raise PluginConformanceError(f"plugin {attribute} must not reference itself")
        declarations[attribute] = value

    ordering_conflicts = set(declarations["load_after"]) & set(declarations["load_before"])
    if ordering_conflicts:
        conflict = sorted(ordering_conflicts)[0]
        raise PluginConformanceError(
            f"plugin cannot load both before and after dependency {conflict!r}"
        )


def _effective_plugin_name(plugin_cls: type[Plugin]) -> str:
    explicit_name = getattr(plugin_cls, "name", None)
    if explicit_name is None:
        effective_name = plugin_cls.__name__.lower()
    elif isinstance(explicit_name, str):
        effective_name = explicit_name
    else:
        raise PluginConformanceError("plugin name must be a string or None")
    if not effective_name or effective_name != effective_name.strip():
        raise PluginConformanceError("effective plugin name must be a non-empty trimmed string")
    return effective_name


def assert_plugin_handler(
    plugin: Plugin,
    handler_name: str,
    *,
    kind: str | None = None,
) -> BoundHandler:
    """Return one registered handler after validating its binding metadata."""
    if not isinstance(plugin, Plugin):
        raise PluginConformanceError("plugin instance must inherit from iamai.Plugin")
    if not handler_name:
        raise PluginConformanceError("handler_name must be non-empty")
    if kind is not None and kind not in {"command", "message", "event"}:
        raise PluginConformanceError(f"unsupported handler kind: {kind!r}")

    try:
        handlers = plugin.iter_handlers()
    except Exception as exc:
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} handler discovery failed: {exc}"
        ) from exc

    for handler in handlers:
        _assert_bound_handler(plugin, handler)

    matches = [
        handler
        for handler in handlers
        if handler.spec.func_name == handler_name and (kind is None or handler.spec.kind == kind)
    ]
    if not matches:
        suffix = "" if kind is None else f" with kind {kind!r}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} did not register handler {handler_name!r}{suffix}"
        )
    if len(matches) > 1:
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} registered ambiguous handler {handler_name!r}"
        )
    return matches[0]


async def assert_plugin_permission(
    handler: BoundHandler,
    context: Context,
    *,
    expected: bool,
) -> None:
    """Assert the allow/deny result of a registered handler permission."""
    if not isinstance(handler, BoundHandler):
        raise PluginConformanceError("handler must be an iamai.BoundHandler")
    if not isinstance(context, Context):
        raise PluginConformanceError("context must be an iamai.Context")
    if context.handler is not handler or context.plugin is not handler.plugin:
        raise PluginConformanceError("context must be bound to the handler and its plugin")
    if type(expected) is not bool:
        raise PluginConformanceError("expected permission result must be a boolean")

    permission = handler.spec.permission
    try:
        actual = (
            True
            if permission is None
            else await permission.evaluate(
                context.runtime,
                context,
                {},
            )
        )
    except Exception as exc:
        raise PluginConformanceError(
            f"permission for handler {handler.spec.func_name!r} raised: {exc}"
        ) from exc

    if actual is not expected:
        raise PluginConformanceError(
            f"permission for handler {handler.spec.func_name!r} returned {actual}; "
            f"expected {expected}"
        )


async def assert_plugin_lifecycle(
    plugin: Plugin,
    *,
    cleanup: CleanupCheck,
    timeout: float = 1.0,
) -> None:
    """Assert successful startup, shutdown, and final resource cleanup."""
    _assert_plugin_instance(plugin)
    _assert_timeout(timeout)
    try:
        await asyncio.wait_for(plugin.startup(), timeout=timeout)
    except asyncio.CancelledError:
        await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="startup cancellation",
            timeout=timeout,
        )
        raise
    except TimeoutError as exc:
        cleanup_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="startup timeout",
            timeout=timeout,
        )
        suffix = "" if cleanup_error is None else f"; cleanup failed: {cleanup_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} startup did not finish before timeout{suffix}"
        ) from exc
    except Exception as exc:
        cleanup_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="startup failure",
            timeout=timeout,
        )
        suffix = "" if cleanup_error is None else f"; cleanup failed: {cleanup_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} startup failed: {exc}{suffix}"
        ) from exc

    try:
        await asyncio.wait_for(plugin.shutdown(), timeout=timeout)
    except asyncio.CancelledError:
        await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="shutdown cancellation",
            timeout=timeout,
        )
        raise
    except TimeoutError as exc:
        cleanup_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="shutdown timeout",
            timeout=timeout,
        )
        suffix = "" if cleanup_error is None else f"; cleanup failed: {cleanup_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} shutdown did not finish before timeout{suffix}"
        ) from exc
    except Exception as exc:
        cleanup_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="shutdown failure",
            timeout=timeout,
        )
        suffix = "" if cleanup_error is None else f"; cleanup failed: {cleanup_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} shutdown failed: {exc}{suffix}"
        ) from exc

    await _assert_cleanup(plugin, cleanup, phase="shutdown", timeout=timeout)


async def assert_plugin_startup_failure_cleanup(
    plugin: Plugin,
    *,
    cleanup: CleanupCheck,
    expected_exception: type[Exception] | tuple[type[Exception], ...] = Exception,
    timeout: float = 1.0,
) -> Exception:
    """Assert that a failed startup releases resources before propagating its error."""
    _assert_plugin_instance(plugin)
    _assert_timeout(timeout)
    try:
        await asyncio.wait_for(plugin.startup(), timeout=timeout)
    except asyncio.CancelledError:
        await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="startup cancellation",
            timeout=timeout,
        )
        raise
    except TimeoutError as startup_error:
        cleanup_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="startup timeout",
            timeout=timeout,
        )
        suffix = "" if cleanup_error is None else f"; cleanup failed: {cleanup_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} startup did not finish before timeout{suffix}"
        ) from startup_error
    except Exception as startup_error:
        try:
            await _assert_cleanup(
                plugin,
                cleanup,
                phase="failed startup",
                timeout=timeout,
            )
        except PluginConformanceError as cleanup_error:
            raise PluginConformanceError(
                f"plugin {plugin.plugin_name!r} startup raised {startup_error!r}, "
                f"but self-cleanup failed: {cleanup_error}"
            ) from startup_error
        if not isinstance(startup_error, expected_exception):
            raise PluginConformanceError(
                f"plugin {plugin.plugin_name!r} startup raised "
                f"{type(startup_error).__name__}; expected {_exception_names(expected_exception)}"
            ) from startup_error
        return startup_error

    try:
        await asyncio.wait_for(plugin.shutdown(), timeout=timeout)
    except asyncio.CancelledError:
        await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="unexpected startup shutdown cancellation",
            timeout=timeout,
        )
        raise
    except TimeoutError as exc:
        recovery_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="unexpected startup shutdown timeout",
            timeout=timeout,
        )
        suffix = "" if recovery_error is None else f"; cleanup failed: {recovery_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} unexpectedly started and shutdown timed out{suffix}"
        ) from exc
    except Exception as exc:
        recovery_error = await _best_effort_plugin_cleanup(
            plugin,
            cleanup,
            phase="unexpected startup shutdown failure",
            timeout=timeout,
        )
        suffix = "" if recovery_error is None else f"; cleanup failed: {recovery_error}"
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} unexpectedly started and shutdown failed: {exc}{suffix}"
        ) from exc
    await _assert_cleanup(
        plugin,
        cleanup,
        phase="unexpected successful startup",
        timeout=timeout,
    )
    raise PluginConformanceError(f"plugin {plugin.plugin_name!r} startup was expected to fail")


def _assert_plugin_instance(plugin: Plugin) -> None:
    if not isinstance(plugin, Plugin):
        raise PluginConformanceError("plugin instance must inherit from iamai.Plugin")


def _assert_bound_handler(plugin: Plugin, handler: object) -> None:
    if not isinstance(handler, BoundHandler):
        raise PluginConformanceError("plugin iter_handlers() must return BoundHandler values")
    if handler.plugin is not plugin:
        raise PluginConformanceError(
            f"handler {handler.spec.func_name!r} must be bound to its plugin instance"
        )
    if handler.spec.kind not in {"command", "message", "event"}:
        raise PluginConformanceError(
            f"handler {handler.spec.func_name!r} has unsupported kind {handler.spec.kind!r}"
        )
    if not handler.spec.func_name or not callable(handler.callback):
        raise PluginConformanceError("registered handler must name a callable callback")


async def _assert_cleanup(
    plugin: Plugin,
    cleanup: CleanupCheck,
    *,
    phase: str,
    timeout: float,
) -> None:
    if not callable(cleanup):
        raise PluginConformanceError("cleanup check must be callable")
    try:
        result = cleanup()
        if inspect.isawaitable(result):
            result = await asyncio.wait_for(result, timeout=timeout)
    except TimeoutError as exc:
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} {phase} cleanup check timed out"
        ) from exc
    except Exception as exc:
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} {phase} cleanup check raised: {exc}"
        ) from exc
    if not isinstance(result, bool):
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} {phase} cleanup check must return bool, "
            f"got {type(result).__name__}"
        )
    if not result:
        raise PluginConformanceError(
            f"plugin {plugin.plugin_name!r} {phase} cleanup check returned False"
        )


def _assert_timeout(timeout: float) -> None:
    if timeout <= 0:
        raise PluginConformanceError("timeout must be greater than zero")


async def _best_effort_plugin_cleanup(
    plugin: Plugin,
    cleanup: CleanupCheck,
    *,
    phase: str,
    timeout: float,
) -> str | None:
    problems: list[str] = []
    try:
        await asyncio.wait_for(plugin.shutdown(), timeout=timeout)
    except TimeoutError:
        problems.append("shutdown timed out")
    except Exception as exc:
        problems.append(f"shutdown raised {type(exc).__name__}: {exc}")

    try:
        await _assert_cleanup(
            plugin,
            cleanup,
            phase=f"{phase} recovery",
            timeout=timeout,
        )
    except PluginConformanceError as exc:
        problems.append(str(exc))
    return "; ".join(problems) or None


def _exception_names(value: type[Exception] | tuple[type[Exception], ...]) -> str:
    if isinstance(value, tuple):
        return " or ".join(item.__name__ for item in value)
    return value.__name__
