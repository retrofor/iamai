from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest
from iamai import Adapter, Event, Message, Runtime
from iamai.testing.adapters import (
    AdapterConformanceError,
    assert_adapter_api_result,
    assert_adapter_can_close,
    assert_adapter_event,
    assert_adapter_send_result,
)


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": [], "builtin_plugins": False},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


class ConformingAdapter(Adapter):
    name = "demo"

    async def start(self) -> None:
        return None

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        return {
            "target": target or event.channel_id if event else target,
            "text": message.plain_text(),
        }

    async def call_api(self, action: str, **params: Any) -> Any:
        return {"action": action, "params": params}


def test_adapter_conformance_helpers_accept_minimum_adapter_contract(
    tmp_path: Path,
) -> None:
    adapter = ConformingAdapter(_make_runtime(tmp_path))
    event = Event(
        id="evt-1",
        adapter="demo",
        platform="demo",
        type="message",
        channel_id="room",
        user_id="alice",
        message=Message("hello"),
    )

    assert_adapter_event(event, adapter="demo")
    assert_adapter_send_result(asyncio.run(adapter.send_message(Message("pong"), event=event)))
    assert_adapter_api_result(asyncio.run(adapter.call_api("ping", value=1)))
    asyncio.run(assert_adapter_can_close(adapter))


def test_adapter_conformance_helpers_reject_incomplete_event() -> None:
    event = Event(id="evt-1", adapter="", platform="demo", type="", raw={})

    with pytest.raises(AdapterConformanceError, match="event.adapter"):
        assert_adapter_event(event)
