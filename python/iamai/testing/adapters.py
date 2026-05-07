"""Conformance helpers for third-party iamai adapters."""

from __future__ import annotations

import inspect
from typing import Any

from iamai.adapter import Adapter
from iamai.event import Event


class AdapterConformanceError(AssertionError):
    """Raised when an adapter fails a conformance helper."""


def assert_adapter_event(event: Event, *, adapter: str | None = None) -> None:
    """Assert that an inbound event has the minimum normalized fields."""
    if not isinstance(event, Event):
        raise AdapterConformanceError("normalized inbound value must be an Event")
    if adapter is not None and event.adapter != adapter:
        raise AdapterConformanceError(f"event.adapter must be {adapter!r}")
    if not event.adapter:
        raise AdapterConformanceError("event.adapter is required")
    if not event.type:
        raise AdapterConformanceError("event.type is required")
    if not event.message.segments and not event.raw:
        raise AdapterConformanceError("event.message or event.raw is required")


def assert_adapter_send_result(result: Any) -> None:
    """Assert that send_message returned a completed, non-coroutine result."""
    if inspect.isawaitable(result):
        raise AdapterConformanceError("send_message result must be awaited before assertion")


def assert_adapter_api_result(result: Any) -> None:
    """Assert that call_api returned a completed, non-coroutine result."""
    if inspect.isawaitable(result):
        raise AdapterConformanceError("call_api result must be awaited before assertion")


async def assert_adapter_can_close(adapter: Adapter) -> None:
    """Assert that adapter.close is idempotent."""
    await adapter.close()
    await adapter.close()
