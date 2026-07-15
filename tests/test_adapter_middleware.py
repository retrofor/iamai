from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import websockets

from iamai import Event, Message, Runtime
from iamai.adapters.middleware import (
    EventFieldMap,
    InboundEnvelope,
    JsonHttpWebhookMiddleware,
    JsonWebSocketClientMiddleware,
    JsonWebSocketServerMiddleware,
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


async def _wait_until(predicate: Callable[[], bool], *, timeout: float = 2.0) -> None:
    async with asyncio.timeout(timeout):
        while not predicate():
            await asyncio.sleep(0.01)


def _server_port(server: Any) -> int:
    return int(server.sockets[0].getsockname()[1])


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


def test_json_http_webhook_middleware_reports_runtime_overload(tmp_path: Path) -> None:
    runtime = _make_runtime(tmp_path)

    async def dispatch(event: Event, adapter: Any) -> bool:
        return False

    runtime.dispatch = dispatch  # type: ignore[method-assign]
    adapter = MinimalWebhookAdapter(runtime)
    request = HttpRequest(
        method="POST",
        path="/events",
        query_string="",
        headers={"content-type": "application/json"},
        body=b'{"sender":{"id":123},"body":{"text":"hello"}}',
        client=("127.0.0.1", 12345),
    )

    response = asyncio.run(adapter._handle_http_request(request))

    assert response.status == 503
    assert response.headers["Retry-After"] == "1"
    assert json.loads(response.body)["reason"] == "runtime overloaded"


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


class MinimalReverseWsAdapter(JsonWebSocketServerMiddleware):
    name = "minimal_reverse_ws"
    field_map = EventFieldMap(message="message")

    def __init__(self, runtime: Runtime, config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.envelopes: list[InboundEnvelope] = []

    def normalize_payload(
        self,
        payload: Any,
        envelope: InboundEnvelope,
    ) -> Event | list[Event] | None:
        self.envelopes.append(envelope)
        return super().normalize_payload(payload, envelope)

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


def test_json_websocket_client_loopback_auth_echo_and_clean_close(tmp_path: Path) -> None:
    async def scenario() -> None:
        emitted: list[Event] = []
        authorization_headers: list[str | None] = []
        blocked_request_received = asyncio.Event()

        async def dispatch(event: Event, adapter: Any) -> None:
            emitted.append(event)

        async def handler(websocket: Any) -> None:
            authorization_headers.append(websocket.request.headers.get("Authorization"))
            await websocket.send('{"message":"from-loopback","user_id":"server"}')
            request = json.loads(await websocket.recv())
            await websocket.send(
                json.dumps({"status": "ok", "echo": request["echo"], "data": request["params"]})
            )
            await websocket.recv()
            blocked_request_received.set()
            await websocket.wait_closed()

        server = await websockets.serve(handler, "127.0.0.1", 0)
        runtime = _make_runtime(tmp_path)
        runtime.dispatch = dispatch  # type: ignore[method-assign]
        adapter = MinimalWsAdapter(
            runtime,
            {
                "url": f"ws://127.0.0.1:{_server_port(server)}/events",
                "access_token": "loopback-secret",
                "api_timeout": 1,
                "reconnect_interval": 0.01,
            },
        )
        adapter_task = asyncio.create_task(adapter.start())
        try:
            await _wait_until(adapter._connection_ready.is_set)
            response = await adapter.call_api("ping", value=1)
            await _wait_until(lambda: len(emitted) == 1)

            assert authorization_headers == ["Bearer loopback-secret"]
            assert emitted[0].text == "from-loopback"
            assert response["data"] == {"value": 1}

            pending = asyncio.create_task(adapter.call_api("never-replies"))
            await asyncio.wait_for(blocked_request_received.wait(), timeout=1)
            await adapter.close()
            with pytest.raises(RuntimeError, match="adapter closed"):
                await pending
            assert adapter._pending == {}
            assert adapter._websocket is None
            assert not adapter._connection_ready.is_set()
            await asyncio.wait_for(adapter_task, timeout=1)
        finally:
            await adapter.close()
            if not adapter_task.done():
                adapter_task.cancel()
                await asyncio.gather(adapter_task, return_exceptions=True)
            server.close()
            await server.wait_closed()

    asyncio.run(scenario())


def test_json_websocket_server_loopback_routes_event_and_api_roles(tmp_path: Path) -> None:
    async def scenario() -> None:
        emitted: list[Event] = []

        async def dispatch(event: Event, adapter: Any) -> None:
            emitted.append(event)

        runtime = _make_runtime(tmp_path)
        runtime.dispatch = dispatch  # type: ignore[method-assign]
        adapter = MinimalReverseWsAdapter(
            runtime,
            {
                "host": "127.0.0.1",
                "port": 0,
                "path_event": "/events",
                "path_api": "/api",
                "access_token": "reverse-secret",
                "api_timeout": 1,
            },
        )
        adapter_task = asyncio.create_task(adapter.start())
        try:
            await _wait_until(lambda: adapter._ws_server is not None)
            port = _server_port(adapter._ws_server)
            headers = {"Authorization": "Bearer reverse-secret"}
            async with websockets.connect(
                f"ws://127.0.0.1:{port}/events", additional_headers=headers
            ) as event_websocket:
                await _wait_until(lambda: adapter._event_websocket is not None)
                assert adapter._api_websocket is None
                assert not adapter._connection_ready.is_set()

                async with websockets.connect(
                    f"ws://127.0.0.1:{port}/api", additional_headers=headers
                ) as api_websocket:
                    await _wait_until(lambda: adapter._api_websocket is not None)
                    await _wait_until(
                        lambda: (
                            adapter._event_websocket is not None
                            and adapter._api_websocket is not None
                        )
                    )
                    assert adapter._event_websocket is not adapter._api_websocket

                    await event_websocket.send('{"message":"reverse-event","user_id":"client"}')
                    await _wait_until(lambda: len(emitted) == 1)

                    call = asyncio.create_task(adapter.call_api("get-status", detail=True))
                    request = json.loads(await asyncio.wait_for(api_websocket.recv(), timeout=1))
                    await event_websocket.close()
                    await _wait_until(lambda: adapter._event_websocket is None)
                    assert adapter._connection_ready.is_set()
                    await api_websocket.send(
                        json.dumps({"status": "ok", "echo": request["echo"], "role": "api"})
                    )
                    response = await call

                    assert emitted[0].text == "reverse-event"
                    assert adapter.envelopes[0].transport == "ws-server"
                    assert adapter.envelopes[0].connection_role == "event"
                    assert request["action"] == "get-status"
                    assert request["params"] == {"detail": True}
                    assert response["role"] == "api"
                    assert adapter._pending == {}
        finally:
            await adapter.close()
            await asyncio.wait_for(adapter_task, timeout=1)
            assert adapter._pending == {}

    asyncio.run(scenario())


def test_json_websocket_server_loopback_rejects_bad_path_and_token(tmp_path: Path) -> None:
    async def scenario() -> None:
        adapter = MinimalReverseWsAdapter(
            _make_runtime(tmp_path),
            {
                "host": "127.0.0.1",
                "port": 0,
                "path_event": "/events",
                "path_api": "/api",
                "access_token": "reverse-secret",
            },
        )
        adapter_task = asyncio.create_task(adapter.start())
        try:
            await _wait_until(lambda: adapter._ws_server is not None)
            port = _server_port(adapter._ws_server)
            valid_headers = {"Authorization": "Bearer reverse-secret"}
            invalid_headers = {"Authorization": "Bearer wrong-secret"}

            async with websockets.connect(
                f"ws://127.0.0.1:{port}/wrong", additional_headers=valid_headers
            ) as wrong_path:
                await wrong_path.wait_closed()
                assert wrong_path.close_code == 4404

            async with websockets.connect(
                f"ws://127.0.0.1:{port}/events", additional_headers=invalid_headers
            ) as wrong_token:
                await wrong_token.wait_closed()
                assert wrong_token.close_code == 4401
            assert adapter._event_websocket is None
            assert adapter._api_websocket is None
            assert adapter._websocket is None
            assert not adapter._connection_ready.is_set()
            assert adapter._pending == {}
        finally:
            await adapter.close()
            await asyncio.wait_for(adapter_task, timeout=1)

    asyncio.run(scenario())


def test_json_websocket_server_replaces_api_socket_and_fails_old_pending(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        adapter = MinimalReverseWsAdapter(
            _make_runtime(tmp_path),
            {
                "host": "127.0.0.1",
                "port": 0,
                "path_event": "/events",
                "path_api": "/api",
                "api_timeout": 1,
            },
        )
        adapter_task = asyncio.create_task(adapter.start())
        try:
            await _wait_until(lambda: adapter._ws_server is not None)
            port = _server_port(adapter._ws_server)
            async with websockets.connect(f"ws://127.0.0.1:{port}/api") as first_api:
                await _wait_until(adapter._connection_ready.is_set)
                old_call = asyncio.create_task(adapter.call_api("old-connection"))
                await asyncio.wait_for(first_api.recv(), timeout=1)

                async with websockets.connect(f"ws://127.0.0.1:{port}/api") as second_api:
                    with pytest.raises(ConnectionError, match="connection replaced"):
                        await asyncio.wait_for(old_call, timeout=0.5)
                    assert adapter._pending == {}
                    await _wait_until(adapter._connection_ready.is_set)

                    new_call = asyncio.create_task(adapter.call_api("new-connection"))
                    request = json.loads(await asyncio.wait_for(second_api.recv(), timeout=1))
                    await second_api.send(
                        json.dumps({"status": "ok", "echo": request["echo"], "generation": 2})
                    )
                    response = await new_call

                    assert response["generation"] == 2
                    assert adapter._pending == {}
        finally:
            await adapter.close()
            await asyncio.wait_for(adapter_task, timeout=1)

    asyncio.run(scenario())


def test_json_websocket_client_reconnects_and_close_interrupts_backoff(tmp_path: Path) -> None:
    async def scenario() -> None:
        connection_count = 0
        close_second_connection = asyncio.Event()

        async def handler(websocket: Any) -> None:
            nonlocal connection_count
            connection_count += 1
            if connection_count == 1:
                await websocket.close(code=1012, reason="restart")
                return
            request = json.loads(await websocket.recv())
            await websocket.send(
                json.dumps({"status": "ok", "echo": request["echo"], "attempt": connection_count})
            )
            await close_second_connection.wait()
            await websocket.close(code=1012, reason="restart")

        server = await websockets.serve(handler, "127.0.0.1", 0)
        adapter = MinimalWsAdapter(
            _make_runtime(tmp_path),
            {
                "url": f"ws://127.0.0.1:{_server_port(server)}/events",
                "api_timeout": 1,
                "reconnect_interval": 0.01,
            },
        )
        adapter_task = asyncio.create_task(adapter.start())
        try:
            await _wait_until(lambda: connection_count == 2 and adapter._connection_ready.is_set())
            response = await adapter.call_api("second-attempt")
            assert response["attempt"] == 2
            assert adapter._pending == {}

            adapter.reconnect_interval = 5
            close_second_connection.set()
            await _wait_until(lambda: not adapter._connection_ready.is_set())
            await asyncio.sleep(0.02)
            await adapter.close()
            await asyncio.wait_for(adapter_task, timeout=0.25)
            assert connection_count == 2
            assert adapter._pending == {}
            assert adapter._websocket is None
        finally:
            await adapter.close()
            if not adapter_task.done():
                adapter_task.cancel()
                await asyncio.gather(adapter_task, return_exceptions=True)
            server.close()
            await server.wait_closed()

    asyncio.run(scenario())


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
