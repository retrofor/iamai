"""Conformance helpers for third-party iamai adapters."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from iamai.adapter import Adapter
from iamai.event import Event
from iamai.message import Message


class AdapterConformanceError(AssertionError):
    """Raised when an adapter fails a conformance helper."""


_UNSET = object()

ResultCheck = Callable[[Any], bool]
Probe = Callable[[], bool | Awaitable[bool]]


def assert_adapter_config(
    adapter_cls: type[Adapter],
    runtime: Any,
    *,
    config: Mapping[str, Any] | None = None,
    expected: Mapping[str, Any] | None = None,
) -> Adapter:
    """Construct an adapter and assert a subset of its normalized config."""
    if not isinstance(adapter_cls, type) or not issubclass(adapter_cls, Adapter):
        raise AdapterConformanceError("adapter_cls must be an Adapter subclass")
    _assert_non_empty_string(adapter_cls.name, path="adapter.name", trimmed=True)
    adapter = adapter_cls(runtime, dict(config or {}))
    if expected is not None:
        _assert_mapping_subset(adapter.config, expected, path="adapter.config")
    return adapter


def assert_adapter_event(
    event: Event,
    *,
    adapter: str | None = None,
    expected_fields: Mapping[str, Any] | None = None,
) -> None:
    """Assert that an inbound event has the minimum normalized fields."""
    if not isinstance(event, Event):
        raise AdapterConformanceError("normalized inbound value must be an Event")
    _assert_non_empty_string(event.id, path="event.id")
    _assert_non_empty_string(event.adapter, path="event.adapter")
    _assert_non_empty_string(event.platform, path="event.platform")
    _assert_non_empty_string(event.type, path="event.type")
    if not isinstance(event.message, Message):
        raise AdapterConformanceError("event.message must be a Message")
    if adapter is not None and event.adapter != adapter:
        raise AdapterConformanceError(f"event.adapter must be {adapter!r}")
    for field, expected in (expected_fields or {}).items():
        if not hasattr(event, field):
            raise AdapterConformanceError(f"event has no field {field!r}")
        _assert_expected_value(
            getattr(event, field),
            expected,
            path=f"event.{field}",
        )


def assert_adapter_send_result(
    result: Any,
    *,
    expected: Any = _UNSET,
    check: ResultCheck | None = None,
) -> None:
    """Assert that send_message returned a completed, non-coroutine result."""
    _assert_completed_result("send_message", result, expected=expected, check=check)


def assert_adapter_api_result(
    result: Any,
    *,
    expected: Any = _UNSET,
    check: ResultCheck | None = None,
) -> None:
    """Assert that call_api returned a completed, non-coroutine result."""
    _assert_completed_result("call_api", result, expected=expected, check=check)


async def assert_adapter_error(
    operation: Awaitable[Any],
    *,
    error_type: type[BaseException],
    match: str | None = None,
) -> BaseException:
    """Assert an async operation's error without converting or swallowing it."""
    try:
        await operation
    except asyncio.CancelledError:
        raise
    except BaseException as exc:
        _assert_exception(exc, error_type=error_type, match=match)
        return exc
    raise AdapterConformanceError(
        f"operation must raise {error_type.__name__}, but it completed successfully"
    )


async def assert_adapter_lifecycle(
    adapter: Adapter,
    *,
    ready: Probe | None = None,
    clean: Probe | None = None,
    timeout: float = 1.0,
) -> None:
    """Assert that start becomes ready and close stops the adapter cleanly."""
    _assert_timeout(timeout)
    task = asyncio.create_task(adapter.start(), name=f"conformance:{adapter.name}:start")
    try:
        await _wait_until_ready(task, ready=ready, timeout=timeout)
        await _close_adapter(adapter, timeout=timeout)
        await _stop_task_after_close(task, timeout=timeout)
        await _wait_for_probe(clean, label="clean", timeout=timeout)
    except BaseException:
        await _best_effort_cleanup(adapter, task, timeout=timeout)
        raise


async def assert_adapter_cancellation(
    adapter: Adapter,
    *,
    ready: Probe | None = None,
    clean: Probe | None = None,
    timeout: float = 1.0,
) -> None:
    """Assert that start propagates cancellation and leaves resources clean."""
    _assert_timeout(timeout)
    task = asyncio.create_task(adapter.start(), name=f"conformance:{adapter.name}:cancel")
    try:
        await _wait_until_ready(task, ready=ready, timeout=timeout)
        if task.done():
            raise AdapterConformanceError("adapter.start completed before cancellation")
        task.cancel()
        done, _ = await asyncio.wait({task}, timeout=timeout)
        if not done:
            raise AdapterConformanceError("adapter.start did not stop after cancellation")
        if not task.cancelled():
            exc = task.exception()
            if exc is None:
                raise AdapterConformanceError("adapter.start swallowed cancellation")
            raise AdapterConformanceError(
                f"adapter.start replaced cancellation with {type(exc).__name__}: {exc}"
            ) from exc
        await _close_adapter(adapter, timeout=timeout)
        await _wait_for_probe(clean, label="clean", timeout=timeout)
    except BaseException:
        await _best_effort_cleanup(adapter, task, timeout=timeout)
        raise


async def assert_adapter_start_failure(
    adapter: Adapter,
    *,
    error_type: type[BaseException],
    match: str | None = None,
    clean: Probe | None = None,
    timeout: float = 1.0,
) -> BaseException:
    """Assert start failure semantics and cleanup through adapter.close."""
    _assert_timeout(timeout)
    task = asyncio.create_task(adapter.start(), name=f"conformance:{adapter.name}:failure")
    try:
        done, _ = await asyncio.wait({task}, timeout=timeout)
        if not done:
            raise AdapterConformanceError("adapter.start did not fail before timeout")
        if task.cancelled():
            raise asyncio.CancelledError
        exc = task.exception()
        if exc is None:
            raise AdapterConformanceError("adapter.start completed without the expected failure")
        _assert_exception(exc, error_type=error_type, match=match)
        await _close_adapter(adapter, timeout=timeout)
        await _wait_for_probe(clean, label="clean", timeout=timeout)
        return exc
    except BaseException:
        await _best_effort_cleanup(adapter, task, timeout=timeout)
        raise


async def assert_adapter_can_close(adapter: Adapter) -> None:
    """Assert that adapter.close is idempotent."""
    await adapter.close()
    await adapter.close()


def _assert_completed_result(
    operation: str,
    result: Any,
    *,
    expected: Any,
    check: ResultCheck | None,
) -> None:
    if inspect.isawaitable(result):
        raise AdapterConformanceError(f"{operation} result must be awaited before assertion")
    if expected is not _UNSET and check is not None:
        raise AdapterConformanceError("expected and check are mutually exclusive")
    if expected is not _UNSET:
        _assert_expected_value(result, expected, path=f"{operation} result")
    if check is None:
        return
    try:
        accepted: Any = check(result)
    except Exception as exc:
        raise AdapterConformanceError(
            f"{operation} result check raised {type(exc).__name__}: {exc}"
        ) from exc
    if inspect.isawaitable(accepted):
        if inspect.iscoroutine(accepted):
            accepted.close()
        raise AdapterConformanceError(f"{operation} result check must return bool, not awaitable")
    if not isinstance(accepted, bool):
        raise AdapterConformanceError(
            f"{operation} result check must return bool, got {type(accepted).__name__}"
        )
    if not accepted:
        raise AdapterConformanceError(f"{operation} result check returned false")


def _assert_expected_value(actual: Any, expected: Any, *, path: str) -> None:
    if isinstance(actual, Mapping) and isinstance(expected, Mapping):
        _assert_mapping_subset(actual, expected, path=path)
        return
    if actual != expected:
        raise AdapterConformanceError(f"{path} must be {expected!r}, got {actual!r}")


def _assert_non_empty_string(value: object, *, path: str, trimmed: bool = False) -> None:
    if not isinstance(value, str) or not value:
        raise AdapterConformanceError(f"{path} must be a non-empty string")
    if trimmed and value != value.strip():
        raise AdapterConformanceError(f"{path} must be a non-empty trimmed string")


def _assert_mapping_subset(
    actual: Mapping[str, Any],
    expected: Mapping[str, Any],
    *,
    path: str,
) -> None:
    for key, expected_value in expected.items():
        if key not in actual:
            raise AdapterConformanceError(f"{path} is missing {key!r}")
        _assert_expected_value(actual[key], expected_value, path=f"{path}.{key}")


def _assert_exception(
    exc: BaseException,
    *,
    error_type: type[BaseException],
    match: str | None,
) -> None:
    if not isinstance(exc, error_type):
        raise AdapterConformanceError(
            f"expected {error_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    if match is not None and match not in str(exc):
        raise AdapterConformanceError(
            f"{error_type.__name__} message must contain {match!r}, got {str(exc)!r}"
        ) from exc


def _assert_timeout(timeout: float) -> None:
    if timeout <= 0:
        raise AdapterConformanceError("timeout must be greater than zero")


async def _wait_until_ready(
    task: asyncio.Task[None],
    *,
    ready: Probe | None,
    timeout: float,
) -> None:
    if ready is None:
        await asyncio.sleep(0)
        _assert_start_task_healthy(task, require_running=False)
        return

    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise AdapterConformanceError("ready probe did not become true before timeout")
        try:
            ready_now = await asyncio.wait_for(
                _evaluate_probe(ready, label="ready"),
                timeout=remaining,
            )
        except TimeoutError as exc:
            raise AdapterConformanceError("ready probe did not finish before timeout") from exc
        if ready_now:
            return
        _assert_start_task_healthy(task, require_running=True)
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise AdapterConformanceError("ready probe did not become true before timeout")
        await asyncio.sleep(min(0.01, remaining))


def _assert_start_task_healthy(
    task: asyncio.Task[None],
    *,
    require_running: bool,
) -> None:
    if not task.done():
        return
    if task.cancelled():
        raise AdapterConformanceError("adapter.start cancelled before readiness")
    exc = task.exception()
    if exc is not None:
        raise AdapterConformanceError(
            f"adapter.start failed before readiness: {type(exc).__name__}: {exc}"
        ) from exc
    if require_running:
        raise AdapterConformanceError("adapter.start completed before readiness")


async def _stop_task_after_close(
    task: asyncio.Task[None],
    *,
    timeout: float,
) -> None:
    await asyncio.sleep(0)
    if not task.done():
        task.cancel()
    done, _ = await asyncio.wait({task}, timeout=timeout)
    if not done:
        raise AdapterConformanceError("adapter.start did not stop after close and cancellation")
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        raise AdapterConformanceError(
            f"adapter.start failed during close: {type(exc).__name__}: {exc}"
        ) from exc


async def _close_adapter(adapter: Adapter, *, timeout: float) -> None:
    try:
        await asyncio.wait_for(adapter.close(), timeout=timeout)
    except asyncio.CancelledError:
        raise
    except TimeoutError as exc:
        raise AdapterConformanceError("adapter.close did not finish before timeout") from exc
    except Exception as exc:
        raise AdapterConformanceError(f"adapter.close failed: {type(exc).__name__}: {exc}") from exc


async def _wait_for_probe(
    probe: Probe | None,
    *,
    label: str,
    timeout: float,
) -> None:
    if probe is None:
        return
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            raise AdapterConformanceError(f"{label} probe did not become true before timeout")
        try:
            probe_succeeded = await asyncio.wait_for(
                _evaluate_probe(probe, label=label),
                timeout=remaining,
            )
        except TimeoutError as exc:
            raise AdapterConformanceError(f"{label} probe did not finish before timeout") from exc
        if probe_succeeded:
            return
        await asyncio.sleep(min(0.01, remaining))


async def _evaluate_probe(probe: Probe, *, label: str) -> bool:
    try:
        result = probe()
        if inspect.isawaitable(result):
            result = await result
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        raise AdapterConformanceError(f"{label} probe raised {type(exc).__name__}: {exc}") from exc
    if not isinstance(result, bool):
        raise AdapterConformanceError(
            f"{label} probe must return bool, got {type(result).__name__}"
        )
    return result


async def _best_effort_cleanup(
    adapter: Adapter,
    task: asyncio.Task[None],
    *,
    timeout: float,
) -> None:
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await asyncio.wait_for(adapter.close(), timeout=timeout)
    if task.done():
        with contextlib.suppress(asyncio.CancelledError, Exception):
            task.exception()
        return
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError, Exception):
        await asyncio.wait_for(task, timeout=timeout)
