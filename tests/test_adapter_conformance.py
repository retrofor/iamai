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
    assert_adapter_cancellation,
    assert_adapter_config,
    assert_adapter_error,
    assert_adapter_event,
    assert_adapter_lifecycle,
    assert_adapter_send_result,
    assert_adapter_start_failure,
)
from pydantic import BaseModel


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


class AdapterConfig(BaseModel):
    port: int = 8080
    options: dict[str, bool] = {"trace": False}


class ConfiguredAdapter(ConformingAdapter):
    name = "configured"
    config_model = AdapterConfig


class BlankNameAdapter(ConformingAdapter):
    name = "  "


class PaddedNameAdapter(ConformingAdapter):
    name = " demo "


class LifecycleAdapter(ConformingAdapter):
    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.closed = False
        self.close_calls = 0

    async def start(self) -> None:
        self.started.set()
        await self.release.wait()

    async def close(self) -> None:
        self.close_calls += 1
        self.closed = True
        self.release.set()


class CancellationAdapter(ConformingAdapter):
    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.started = asyncio.Event()
        self.cancelled = False
        self.closed = False

    async def start(self) -> None:
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True
            raise

    async def close(self) -> None:
        self.closed = True


class RuntimeStyleLifecycleAdapter(CancellationAdapter):
    """Close resources, then rely on Runtime to cancel the receive task."""


class SwallowsCancellationAdapter(CancellationAdapter):
    async def start(self) -> None:
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancelled = True


class AdapterProtocolError(RuntimeError):
    pass


class FailingStartAdapter(ConformingAdapter):
    def __init__(self, runtime: Runtime) -> None:
        super().__init__(runtime)
        self.resource_open = False
        self.failure = AdapterProtocolError("authentication denied by platform")

    async def start(self) -> None:
        self.resource_open = True
        raise self.failure

    async def close(self) -> None:
        self.resource_open = False


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

    assert_adapter_event(
        event,
        adapter="demo",
        expected_fields={"channel_id": "room", "text": "hello"},
    )
    assert_adapter_send_result(
        asyncio.run(adapter.send_message(Message("pong"), event=event)),
        expected={"target": "room", "text": "pong"},
    )
    assert_adapter_api_result(
        asyncio.run(adapter.call_api("ping", value=1)),
        check=lambda result: result == {"action": "ping", "params": {"value": 1}},
    )
    asyncio.run(assert_adapter_can_close(adapter))


def test_adapter_conformance_helpers_reject_incomplete_event() -> None:
    event = Event(id="evt-1", adapter="", platform="demo", type="", raw={})

    with pytest.raises(AdapterConformanceError, match="event.adapter"):
        assert_adapter_event(event)


@pytest.mark.parametrize("field", ["id", "adapter", "platform", "type"])
def test_adapter_event_rejects_empty_required_fields(field: str) -> None:
    values = {
        "id": "evt-1",
        "adapter": "demo",
        "platform": "demo",
        "type": "message",
    }
    values[field] = ""
    event = Event(**values)

    with pytest.raises(AdapterConformanceError, match=rf"event\.{field}"):
        assert_adapter_event(event)


def test_adapter_event_requires_message_instance() -> None:
    event = Event(id="evt-1", adapter="demo", platform="demo", type="message")
    event.message = "hello"  # type: ignore[assignment]

    with pytest.raises(AdapterConformanceError, match="event.message must be a Message"):
        assert_adapter_event(event)


def test_adapter_event_accepts_empty_message_and_raw() -> None:
    event = Event(id="evt-1", adapter="demo", platform="demo", type="notice")

    assert_adapter_event(event)


def test_adapter_config_constructs_and_checks_normalized_subset(tmp_path: Path) -> None:
    adapter = assert_adapter_config(
        ConfiguredAdapter,
        _make_runtime(tmp_path),
        config={"port": "9000", "options": {"trace": True}},
        expected={"port": 9000, "options": {"trace": True}},
    )

    assert isinstance(adapter, ConfiguredAdapter)
    assert isinstance(adapter.config_obj, AdapterConfig)


@pytest.mark.parametrize("adapter_cls", [BlankNameAdapter, PaddedNameAdapter])
def test_adapter_config_rejects_invalid_effective_name(
    adapter_cls: type[Adapter],
    tmp_path: Path,
) -> None:
    with pytest.raises(AdapterConformanceError, match="adapter.name"):
        assert_adapter_config(adapter_cls, _make_runtime(tmp_path))


def test_adapter_config_reports_nested_mismatch(tmp_path: Path) -> None:
    with pytest.raises(
        AdapterConformanceError,
        match=r"adapter.config.options.trace must be True, got False",
    ):
        assert_adapter_config(
            ConfiguredAdapter,
            _make_runtime(tmp_path),
            expected={"options": {"trace": True}},
        )


def test_event_expected_fields_and_result_checks_report_failures() -> None:
    event = Event(
        id="evt-1",
        adapter="demo",
        platform="demo",
        type="message",
        message=Message("hello"),
    )

    with pytest.raises(AdapterConformanceError, match="event.channel_id"):
        assert_adapter_event(event, expected_fields={"channel_id": "room"})
    with pytest.raises(AdapterConformanceError, match="send_message result check returned false"):
        assert_adapter_send_result({"ok": False}, check=lambda result: result["ok"] is True)
    with pytest.raises(AdapterConformanceError, match="mutually exclusive"):
        assert_adapter_api_result({}, expected={}, check=lambda _result: True)


def test_result_checks_require_a_synchronous_boolean() -> None:
    async def async_check(_result: object) -> bool:
        return False

    with pytest.raises(AdapterConformanceError, match="not awaitable"):
        assert_adapter_send_result({}, check=async_check)
    with pytest.raises(AdapterConformanceError, match="got int"):
        assert_adapter_api_result({}, check=lambda _result: 1)  # type: ignore[arg-type]


def test_result_helpers_require_awaited_values() -> None:
    async def result() -> dict[str, bool]:
        return {"ok": True}

    operation = result()
    try:
        with pytest.raises(AdapterConformanceError, match="must be awaited"):
            assert_adapter_send_result(operation)
    finally:
        operation.close()


def test_adapter_lifecycle_observes_ready_close_and_clean(tmp_path: Path) -> None:
    async def scenario() -> LifecycleAdapter:
        adapter = LifecycleAdapter(_make_runtime(tmp_path))
        await assert_adapter_lifecycle(
            adapter,
            ready=adapter.started.is_set,
            clean=lambda: adapter.closed and adapter.release.is_set(),
        )
        return adapter

    adapter = asyncio.run(scenario())

    assert adapter.close_calls == 1


def test_adapter_lifecycle_matches_runtime_close_then_cancel_contract(tmp_path: Path) -> None:
    async def scenario() -> RuntimeStyleLifecycleAdapter:
        adapter = RuntimeStyleLifecycleAdapter(_make_runtime(tmp_path))
        await assert_adapter_lifecycle(
            adapter,
            ready=adapter.started.is_set,
            clean=lambda: adapter.closed,
        )
        return adapter

    adapter = asyncio.run(scenario())

    assert adapter.closed is True
    assert adapter.cancelled is True


def test_adapter_cancellation_must_propagate_and_still_cleans(tmp_path: Path) -> None:
    async def scenario() -> CancellationAdapter:
        adapter = CancellationAdapter(_make_runtime(tmp_path))
        await assert_adapter_cancellation(
            adapter,
            ready=adapter.started.is_set,
            clean=lambda: adapter.closed,
        )
        return adapter

    adapter = asyncio.run(scenario())

    assert adapter.cancelled is True
    assert adapter.closed is True


def test_adapter_cancellation_rejects_swallowing_and_runs_cleanup(tmp_path: Path) -> None:
    async def scenario() -> SwallowsCancellationAdapter:
        adapter = SwallowsCancellationAdapter(_make_runtime(tmp_path))
        with pytest.raises(AdapterConformanceError, match="swallowed cancellation"):
            await assert_adapter_cancellation(adapter, ready=adapter.started.is_set)
        return adapter

    adapter = asyncio.run(scenario())

    assert adapter.cancelled is True
    assert adapter.closed is True


def test_adapter_start_failure_preserves_error_and_checks_cleanup(tmp_path: Path) -> None:
    async def scenario() -> tuple[FailingStartAdapter, BaseException]:
        adapter = FailingStartAdapter(_make_runtime(tmp_path))
        error = await assert_adapter_start_failure(
            adapter,
            error_type=AdapterProtocolError,
            match="authentication denied",
            clean=lambda: not adapter.resource_open,
        )
        return adapter, error

    adapter, error = asyncio.run(scenario())

    assert error is adapter.failure
    assert str(error) == "authentication denied by platform"


def test_adapter_error_preserves_error_type_message_and_identity() -> None:
    async def scenario() -> tuple[AdapterProtocolError, BaseException]:
        failure = AdapterProtocolError("request timed out")

        async def fail() -> None:
            raise failure

        captured = await assert_adapter_error(
            fail(),
            error_type=AdapterProtocolError,
            match="timed out",
        )
        return failure, captured

    failure, captured = asyncio.run(scenario())

    assert captured is failure


def test_adapter_error_does_not_swallow_cancellation() -> None:
    async def scenario() -> None:
        async def cancel() -> None:
            raise asyncio.CancelledError

        with pytest.raises(asyncio.CancelledError):
            await assert_adapter_error(cancel(), error_type=BaseException)

    asyncio.run(scenario())
