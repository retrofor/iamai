from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from iamai import Event, Message, Runtime
from iamai.adapters.middleware import (
    EventFieldMap,
    JsonHttpWebhookMiddleware,
    JsonWebSocketClientMiddleware,
    OutboundAction,
)
from iamai.adapters.onebot11 import OneBot11Adapter
from iamai.httpio import HttpRequest


def _make_runtime(tmp_path: Path) -> Runtime:
    return Runtime(
        {
            "runtime": {"adapters": []},
            "adapter": {},
            "plugin": {},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )


def test_event_field_map_builds_default_event_and_coerces_ids() -> None:
    field_map = EventFieldMap(
        type="event.kind",
        detail_type="event.detail",
        user_id="actor.id",
        channel_id="room.id",
        message="content",
    )
    event = field_map.build_event(
        {
            "event": {"kind": "message", "detail": "text"},
            "actor": {"id": 42},
            "room": {"id": 99},
            "content": "hello",
        },
        adapter="demo",
        platform="demo-platform",
    )

    assert event.type == "message"
    assert event.detail_type == "text"
    assert event.user_id == "42"
    assert event.channel_id == "99"
    assert event.text == "hello"


def test_event_field_map_supports_segment_messages_and_inheritance() -> None:
    parent = EventFieldMap(message="payload.message", user_id="payload.user")
    child = EventFieldMap(
        message=parent.message,
        user_id=parent.user_id,
        channel_id="payload.channel",
    )

    event = child.build_event(
        {
            "payload": {
                "user": "alice",
                "channel": "room-1",
                "message": [{"type": "text", "data": {"text": "hi"}}],
            }
        },
        adapter="demo",
        platform="demo-platform",
    )

    assert event.user_id == "alice"
    assert event.channel_id == "room-1"
    assert event.text == "hi"


class MinimalWebhookAdapter(JsonHttpWebhookMiddleware):
    name = "minimal"
    platform = "minimal-platform"
    field_map = EventFieldMap(user_id="sender.id", message="body.text")

    def encode_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> OutboundAction:
        return OutboundAction(kind="message", action="send", params={"message": message.segments})


def test_json_http_webhook_middleware_emits_event_from_field_map(
    tmp_path: Path,
) -> None:
    runtime = _make_runtime(tmp_path)
    emitted: list[Event] = []

    async def dispatch(event: Event, adapter: Any) -> None:
        emitted.append(event)

    runtime.dispatch = dispatch  # type: ignore[method-assign]
    adapter = MinimalWebhookAdapter(runtime, {"access_token": "secret"})
    request = HttpRequest(
        method="POST",
        path="/events",
        query_string="",
        headers={"authorization": "Bearer secret", "content-type": "application/json"},
        body=b'{"sender":{"id":123},"body":{"text":"hello"}}',
        client=("127.0.0.1", 12345),
    )

    response = asyncio.run(adapter._handle_http_request(request))

    assert response.status == 200
    assert emitted[0].adapter == "minimal"
    assert emitted[0].platform == "minimal-platform"
    assert emitted[0].user_id == "123"
    assert emitted[0].text == "hello"


class FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send(self, payload: str) -> None:
        self.sent.append(payload)


class MinimalWsAdapter(JsonWebSocketClientMiddleware):
    name = "minimal_ws"
    field_map = EventFieldMap(message="message")

    def encode_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> OutboundAction:
        return OutboundAction(kind="message", action="send", params={"message": message.segments})


def test_json_websocket_client_middleware_matches_pending_echo(tmp_path: Path) -> None:
    async def scenario() -> Any:
        adapter = MinimalWsAdapter(_make_runtime(tmp_path), {"api_timeout": 1})
        websocket = FakeWebSocket()
        await adapter._bind_connection(websocket)
        task = asyncio.create_task(adapter.call_api("ping", value=1))
        while not websocket.sent:
            await asyncio.sleep(0)
        sent = json.loads(websocket.sent[0])
        await adapter._handle_ws_payload(json.dumps({"status": "ok", "echo": sent["echo"]}))
        return await task, sent

    result, sent = asyncio.run(scenario())

    assert sent["action"] == "ping"
    assert sent["params"] == {"value": 1}
    assert result == {"status": "ok", "echo": sent["echo"]}


def test_json_websocket_client_middleware_emits_inbound_json(tmp_path: Path) -> None:
    async def scenario() -> list[Event]:
        runtime = _make_runtime(tmp_path)
        emitted: list[Event] = []

        async def dispatch(event: Event, adapter: Any) -> None:
            emitted.append(event)

        runtime.dispatch = dispatch  # type: ignore[method-assign]
        adapter = MinimalWsAdapter(runtime)
        await adapter._handle_ws_payload('{"message":"hello","user_id":"alice"}')
        return emitted

    emitted = asyncio.run(scenario())

    assert emitted[0].text == "hello"
    assert emitted[0].user_id == "alice"


def test_onebot11_send_message_keeps_group_and_private_params(tmp_path: Path) -> None:
    adapter = OneBot11Adapter(_make_runtime(tmp_path), {"mode": "ws-reverse"})

    group_action = adapter.encode_message(Message("hello"), target={"group_id": "10001"})
    private_action = adapter.encode_message(Message("hello"), target={"user_id": "20002"})

    assert group_action.action == "send_group_msg"
    assert group_action.params == {
        "group_id": 10001,
        "message": [{"type": "text", "data": {"text": "hello"}}],
    }
    assert private_action.action == "send_private_msg"
    assert private_action.params == {
        "user_id": 20002,
        "message": [{"type": "text", "data": {"text": "hello"}}],
    }


def test_onebot11_ws_echo_pending_result_is_preserved(tmp_path: Path) -> None:
    async def scenario() -> Any:
        adapter = OneBot11Adapter(_make_runtime(tmp_path), {"mode": "ws", "api_timeout": 1})
        websocket = FakeWebSocket()
        await adapter._bind_connection(websocket)
        task = asyncio.create_task(adapter.call_api("get_status"))
        while not websocket.sent:
            await asyncio.sleep(0)
        sent = json.loads(websocket.sent[0])
        response = {
            "status": "ok",
            "retcode": 0,
            "data": {"online": True},
            "echo": sent["echo"],
        }
        await adapter._handle_payload(json.dumps(response))
        return await task

    assert asyncio.run(scenario())["data"] == {"online": True}
