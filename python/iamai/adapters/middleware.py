"""Reusable adapter middleware for JSON based platform integrations."""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import itertools
import json
from abc import abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, cast
from urllib.parse import parse_qs, urlsplit

import websockets

from ..adapter import Adapter
from ..core import new_event_id
from ..event import Event
from ..httpio import HttpError, HttpRequest, HttpResponse, SimpleHttpServer, request_json
from ..message import Message
from ..net import compare_secret

TransportKind = Literal["http-webhook", "ws-client", "ws-server"]
OutboundKind = Literal["api", "message", "http", "ws"]


@dataclass(slots=True)
class InboundEnvelope:
    """Transport metadata attached to one decoded inbound payload."""

    payload: Any
    transport: TransportKind
    headers: Mapping[str, str] = field(default_factory=dict)
    path: str | None = None
    query: Mapping[str, Sequence[str]] = field(default_factory=dict)
    client: Any | None = None
    connection_role: str | None = None


@dataclass(slots=True)
class OutboundAction:
    """Protocol action emitted by adapter mapping hooks."""

    kind: OutboundKind
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    http_url: str | None = None
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    trusted: bool = False
    echo: str | None = None


@dataclass(frozen=True, slots=True)
class EventFieldMap:
    """Declarative JSON field mapping for simple event payloads."""

    type: str | Sequence[str] = "type"
    detail_type: str | Sequence[str] | None = "detail_type"
    sub_type: str | Sequence[str] | None = "sub_type"
    user_id: str | Sequence[str] | None = "user_id"
    channel_id: str | Sequence[str] | None = "channel_id"
    guild_id: str | Sequence[str] | None = "guild_id"
    self_id: str | Sequence[str] | None = "self_id"
    message: str | Sequence[str] | None = "message"
    raw: str | Sequence[str] | None = None
    id: str | Sequence[str] | None = "id"
    default_type: str = "message"
    default_detail_type: str | None = None

    def build_event(
        self,
        payload: Mapping[str, Any],
        *,
        adapter: str,
        platform: str,
    ) -> Event:
        """Build an ``Event`` from a mapped payload."""
        raw = _get_path(payload, self.raw) if self.raw is not None else payload
        raw_mapping = raw if isinstance(raw, Mapping) else payload
        return Event(
            id=str(_get_path(payload, self.id) or new_event_id()),
            adapter=adapter,
            platform=platform,
            type=str(_get_path(payload, self.type) or self.default_type),
            detail_type=_maybe_str(
                _get_path(payload, self.detail_type) or self.default_detail_type
            ),
            sub_type=_maybe_str(_get_path(payload, self.sub_type)),
            user_id=_maybe_str(_get_path(payload, self.user_id)),
            channel_id=_maybe_str(_get_path(payload, self.channel_id)),
            guild_id=_maybe_str(_get_path(payload, self.guild_id)),
            self_id=_maybe_str(_get_path(payload, self.self_id)),
            message=_message_from_payload(_get_path(payload, self.message)),
            raw=dict(raw_mapping),
        )


class AdapterMiddleware(Adapter):
    """Base class for layered adapter implementations."""

    platform = "generic"
    field_map = EventFieldMap()

    def normalize_payload(
        self,
        payload: Any,
        envelope: InboundEnvelope,
    ) -> Event | list[Event] | None:
        """Convert a decoded payload into normalized iamai events."""
        if not isinstance(payload, Mapping):
            return None
        return self.field_map.build_event(payload, adapter=self.name, platform=self.platform)

    def encode_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> OutboundAction:
        """Convert an outbound message into a protocol action."""
        raise NotImplementedError(f"adapter {self.name!r} does not encode messages")

    def encode_api_call(self, action: str, params: Mapping[str, Any]) -> OutboundAction:
        """Convert ``call_api`` arguments into a protocol action."""
        return OutboundAction(kind="api", action=action, params=dict(params))

    def decode_api_result(self, payload: Any) -> Any:
        """Decode a protocol API response payload."""
        return payload

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        """Send a message through the encoded outbound action."""
        outbound = self.encode_message(Message.ensure(message), event=event, target=target)
        return await self.dispatch_outbound_action(outbound)

    async def call_api(self, action: str, **params: Any) -> Any:
        """Call a platform API through the encoded outbound action."""
        outbound = self.encode_api_call(action, params)
        return await self.dispatch_outbound_action(outbound)

    async def dispatch_outbound_action(self, outbound: OutboundAction) -> Any:
        """Dispatch one encoded outbound action to the active transport."""
        raise NotImplementedError(f"adapter {self.name!r} does not dispatch outbound actions")

    async def emit_normalized_payload(self, payload: Any, envelope: InboundEnvelope) -> None:
        """Normalize and emit one decoded inbound payload."""
        events = self.normalize_payload(payload, envelope)
        if events is None:
            return
        if isinstance(events, Event):
            await self.emit(events)
            return
        for event in events:
            await self.emit(event)


class JsonHttpWebhookMiddleware(AdapterMiddleware):
    """HTTP webhook transport for JSON payload adapters."""

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.host = str(self.config.get("host", "127.0.0.1"))
        self.port = int(self.config.get("port", 8080))
        self.path = str(self.config.get("path", "/events"))
        self.access_token = str(self.config.get("access_token", ""))
        self.allow_query_token = bool(self.config.get("allow_query_token", False))
        self.api_base_url = str(self.config.get("api_base_url", self.config.get("api_url", "")))
        self.api_timeout = float(self.config.get("api_timeout", 10.0))
        self.read_timeout = float(self.config.get("read_timeout", 10.0))
        self.max_body_bytes = int(self.config.get("max_body_bytes", 1_048_576))
        self._http_server: SimpleHttpServer | None = None
        self._closed = asyncio.Event()

    async def start(self) -> None:
        """Start the JSON webhook server."""
        await self._run_http_webhook_server()

    async def close(self) -> None:
        """Stop the JSON webhook server."""
        self._closed.set()
        if self._http_server is not None:
            await self._http_server.close()
            self._http_server = None

    async def dispatch_outbound_action(self, outbound: OutboundAction) -> Any:
        """Dispatch outbound actions over HTTP."""
        api_base = outbound.http_url or self.api_base_url.rstrip("/")
        if not api_base:
            raise RuntimeError("api_base_url is required for HTTP adapter calls")
        url = api_base if outbound.http_url else f"{api_base}/{outbound.action}"
        result = await request_json(
            url,
            method=outbound.method,
            json_body=outbound.params,
            headers={**self._auth_headers(), **outbound.headers},
            timeout=self.api_timeout,
        )
        return self.decode_api_result({} if result is None else result)

    async def _run_http_webhook_server(self) -> None:
        self._http_server = SimpleHttpServer(
            self.host,
            self.port,
            read_timeout=self.read_timeout,
            max_body_bytes=self.max_body_bytes,
        )
        self._http_server.route("POST", self.path, self._handle_http_request)
        await self._http_server.start()
        self.logger.info(
            "%s JSON webhook server listening on http://%s:%s%s",
            self.name,
            self.host,
            self.port,
            self.path,
        )
        await self._closed.wait()

    async def _handle_http_request(self, request: HttpRequest) -> HttpResponse:
        if not self._authorize_headers(request.headers, request.query_string):
            self._record_http_request(
                request, outcome="unauthorized", status=401, reason="invalid_token"
            )
            return HttpResponse.json({"status": "failed", "reason": "unauthorized"}, status=401)
        if not request.has_json_content_type():
            self._record_http_request(
                request,
                outcome="unsupported_media_type",
                status=415,
                reason="unsupported_media_type",
            )
            return HttpResponse.json(
                {"status": "failed", "reason": "unsupported media type"}, status=415
            )
        try:
            payload = request.json()
        except HttpError as exc:
            self._record_http_request(
                request, outcome="invalid_json", status=exc.status, reason=exc.message
            )
            return HttpResponse.json({"status": "failed", "reason": exc.message}, status=exc.status)
        try:
            envelope = InboundEnvelope(
                payload=payload,
                transport="http-webhook",
                headers=request.headers,
                path=request.path,
                query=request.query,
                client=request.client,
            )
            await self.emit_normalized_payload(payload, envelope)
        except Exception:
            self.logger.exception("failed to process %s HTTP payload", self.name)
            self._record_http_request(
                request, outcome="invalid_payload", status=400, reason="invalid_payload"
            )
            return HttpResponse.json({"status": "failed", "reason": "invalid payload"}, status=400)
        self._record_http_request(request, outcome="accepted", status=200, reason="ok")
        return HttpResponse.json({"status": "ok"})

    def _record_http_request(
        self, request: HttpRequest, *, outcome: str, status: int, reason: str
    ) -> None:
        client = None if request.client is None else str(request.client[0])
        self.runtime.count_metric(
            f"{self.name}_http_requests_total",
            adapter=self.name,
            outcome=outcome,
            status=status,
        )
        self.runtime.audit(
            f"{self.name}.http_request",
            adapter=self.name,
            outcome=outcome,
            status=status,
            reason=reason,
            client=client,
            path=request.path,
        )

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def _authorize_headers(self, headers: Mapping[str, str], request_target: str) -> bool:
        if not self.access_token:
            return True
        authorization = headers.get("Authorization") or headers.get("authorization")
        if compare_secret(f"Bearer {self.access_token}", str(authorization or "")):
            return True
        if not self.allow_query_token:
            return False
        parsed = urlsplit(request_target)
        query = parse_qs(parsed.query or request_target.lstrip("?"))
        token = query.get("access_token", [""])[0]
        return compare_secret(self.access_token, str(token))


class JsonWebSocketClientMiddleware(AdapterMiddleware):
    """Active JSON websocket client transport with reconnect and echo pending."""

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.url = str(self.config.get("url", "ws://127.0.0.1:6700"))
        self.access_token = str(self.config.get("access_token", ""))
        self.reconnect_interval = float(self.config.get("reconnect_interval", 5.0))
        self.api_timeout = float(self.config.get("api_timeout", 10.0))
        self.ping_interval = float(self.config.get("ping_interval", 20.0))
        self.ping_timeout = float(self.config.get("ping_timeout", 20.0))
        self.open_timeout = float(self.config.get("open_timeout", 10.0))
        self.max_size = int(self.config.get("max_size", 1_048_576))
        self._websocket: Any | None = None
        self._connection_ready = asyncio.Event()
        self._closed = asyncio.Event()
        self._pending: dict[str, asyncio.Future[Any]] = {}
        self._echo_seq = itertools.count(1)

    async def start(self) -> None:
        """Start the active websocket client loop."""
        await self._run_ws_client()

    async def close(self) -> None:
        """Close websocket resources."""
        self._closed.set()
        self._connection_ready.clear()
        await self._fail_pending(RuntimeError(f"{self.name} adapter closed"))
        if self._websocket is not None:
            with contextlib.suppress(Exception):
                await self._websocket.close()
        self._websocket = None

    async def dispatch_outbound_action(self, outbound: OutboundAction) -> Any:
        """Send outbound actions over the active websocket."""
        return await self._call_action_over_ws(outbound)

    async def _run_ws_client(self) -> None:
        connect_kwargs = self._connect_kwargs()
        while not self._closed.is_set():
            try:
                async with websockets.connect(self.url, **connect_kwargs) as websocket:
                    self.logger.info("connected to %s websocket server: %s", self.name, self.url)
                    await self._bind_connection(websocket)
                    await self._consume_connection(websocket)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger.exception("%s ws client loop failed", self.name)
            finally:
                await self._unbind_connection()
            if self._closed.is_set():
                return
            await asyncio.sleep(self.reconnect_interval)

    async def _consume_connection(self, websocket: Any, role: str = "universal") -> None:
        async for payload in websocket:
            try:
                await self._handle_ws_payload(payload, role=role)
            except Exception:
                self.logger.exception("failed to process %s websocket payload", self.name)

    async def _handle_ws_payload(self, payload: str | bytes, *, role: str = "universal") -> None:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        if self._resolve_pending_payload(data):
            return
        envelope = InboundEnvelope(payload=data, transport="ws-client", connection_role=role)
        await self.emit_normalized_payload(data, envelope)

    async def _call_action_over_ws(self, outbound: OutboundAction) -> Any:
        await self._wait_for_connection()
        websocket = self._api_socket_for_calls()
        if websocket is None:
            raise RuntimeError(f"{self.name} connection is not ready")
        echo = outbound.echo or f"{self.name}-{next(self._echo_seq)}"
        future: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[echo] = future
        payload = json.dumps(
            {"action": outbound.action, "params": outbound.params, "echo": echo},
            ensure_ascii=False,
        )
        try:
            await websocket.send(payload)
            result = await asyncio.wait_for(future, timeout=self.api_timeout)
            return self.decode_api_result(result)
        finally:
            self._pending.pop(echo, None)

    async def _bind_connection(self, websocket: Any, role: str = "universal") -> None:
        self._websocket = websocket
        self._connection_ready.set()

    async def _unbind_connection(
        self, role: str = "universal", websocket: Any | None = None
    ) -> None:
        if websocket is None or websocket is self._websocket:
            self._websocket = None
            self._connection_ready.clear()
        await self._fail_pending(ConnectionError(f"{self.name} connection closed"))

    async def _fail_pending(self, exc: BaseException) -> None:
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()

    async def _wait_for_connection(self) -> None:
        if self._connection_ready.is_set():
            return
        await asyncio.wait_for(self._connection_ready.wait(), timeout=self.api_timeout)

    def _api_socket_for_calls(self) -> Any | None:
        return self._websocket

    def _resolve_pending_payload(self, data: Any) -> bool:
        if not isinstance(data, Mapping) or "echo" not in data:
            return False
        echo = str(data["echo"])
        future = self._pending.get(echo)
        if future is not None and not future.done():
            future.set_result(dict(data))
        return True

    def _connect_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "open_timeout": self.open_timeout,
            "ping_interval": self.ping_interval,
            "ping_timeout": self.ping_timeout,
            "max_size": self.max_size,
        }
        headers = self._auth_headers()
        if headers:
            header_name = (
                "additional_headers"
                if "additional_headers" in inspect.signature(websockets.connect).parameters
                else "extra_headers"
            )
            kwargs[header_name] = headers
        return kwargs

    def _auth_headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}


class JsonWebSocketServerMiddleware(JsonWebSocketClientMiddleware):
    """Reverse JSON websocket server transport with role binding."""

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.host = str(self.config.get("host", "127.0.0.1"))
        self.port = int(self.config.get("port", 8080))
        self.path = str(self.config.get("path", "/ws"))
        self.path_event = str(
            self.config.get("path_event", self.config.get("event_path", self.path))
        )
        self.path_api = str(self.config.get("path_api", self.config.get("api_path", self.path)))
        self.allow_query_token = bool(self.config.get("allow_query_token", False))
        self.origins = self.config.get("origins")
        self._event_websocket: Any | None = None
        self._api_websocket: Any | None = None
        self._ws_server: Any | None = None

    async def start(self) -> None:
        """Start the reverse websocket server."""
        await self._run_ws_server()

    async def close(self) -> None:
        """Close reverse websocket resources."""
        self._closed.set()
        self._connection_ready.clear()
        await self._fail_pending(RuntimeError(f"{self.name} adapter closed"))
        websockets_to_close = {
            websocket
            for websocket in {
                self._websocket,
                self._event_websocket,
                self._api_websocket,
            }
            if websocket is not None
        }
        for websocket in websockets_to_close:
            with contextlib.suppress(Exception):
                await websocket.close()
        self._websocket = None
        self._event_websocket = None
        self._api_websocket = None
        if self._ws_server is not None:
            self._ws_server.close()
            await self._ws_server.wait_closed()
            self._ws_server = None

    async def _run_ws_server(self) -> None:
        self._ws_server = await websockets.serve(
            self._accept_ws_connection,
            self.host,
            self.port,
            origins=self.origins,
            open_timeout=self.open_timeout,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            max_size=self.max_size,
        )
        self.logger.info(
            "%s reverse websocket server listening on ws://%s:%s%s (event) / %s (api)",
            self.name,
            self.host,
            self.port,
            self.path_event,
            self.path_api,
        )
        await self._closed.wait()

    async def _accept_ws_connection(self, *args: Any) -> None:
        websocket = args[0]
        request_path = self._extract_path(websocket, args[1] if len(args) > 1 else "")
        request_url = urlsplit(request_path)
        request_only_path = request_url.path or request_path
        role = self._resolve_ws_role(request_only_path)
        if role is None:
            self.logger.warning(
                "reject reverse ws path=%s expected one of [%s, %s]",
                request_path,
                self.path_event,
                self.path_api,
            )
            self.runtime.count_metric(
                f"{self.name}_ws_connections_total",
                adapter=self.name,
                outcome="rejected",
                reason="path_mismatch",
            )
            self.runtime.audit(
                f"{self.name}.ws_connection",
                adapter=self.name,
                outcome="rejected",
                reason="path_mismatch",
                path=request_path,
            )
            await websocket.close(code=4404, reason="path mismatch")
            return
        if not self._authorize_headers(self._extract_headers(websocket), request_path):
            self.logger.warning("reject reverse ws connection due to invalid access token")
            self.runtime.count_metric(
                f"{self.name}_ws_connections_total",
                adapter=self.name,
                outcome="rejected",
                reason="invalid_token",
            )
            self.runtime.audit(
                f"{self.name}.ws_connection",
                adapter=self.name,
                outcome="rejected",
                reason="invalid_token",
                path=request_path,
            )
            await websocket.close(code=4401, reason="unauthorized")
            return
        current = self._current_ws_by_role(role)
        if current is not None:
            self.logger.warning("closing previous %s reverse ws %s connection", self.name, role)
            try:
                await current.close(code=1012, reason="replaced by new connection")
            except Exception:
                self.logger.exception("failed to close previous reverse ws connection")
        await self._bind_connection(websocket, role)
        try:
            await self._consume_connection(websocket, role)
        finally:
            await self._unbind_connection(role, websocket)

    async def _handle_ws_payload(self, payload: str | bytes, *, role: str = "universal") -> None:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        if self._resolve_pending_payload(data):
            return
        envelope = InboundEnvelope(payload=data, transport="ws-server", connection_role=role)
        await self.emit_normalized_payload(data, envelope)

    async def _bind_connection(self, websocket: Any, role: str = "universal") -> None:
        if role in {"event", "universal"}:
            self._event_websocket = websocket
        if role in {"api", "universal"}:
            self._api_websocket = websocket
        if self.path_event == self.path_api:
            self._websocket = websocket
        else:
            self._websocket = self._api_websocket or self._event_websocket
        if self._api_socket_for_calls() is not None:
            self._connection_ready.set()

    async def _unbind_connection(
        self, role: str = "universal", websocket: Any | None = None
    ) -> None:
        if websocket is None:
            websocket = self._current_ws_by_role(role)
        if self._event_websocket is websocket:
            self._event_websocket = None
        if self._api_websocket is websocket:
            self._api_websocket = None
        if self._websocket is websocket:
            self._websocket = None
        self._websocket = self._api_websocket or self._event_websocket
        if self._api_socket_for_calls() is None:
            self._connection_ready.clear()
        await self._fail_pending(ConnectionError(f"{self.name} connection closed"))

    def _api_socket_for_calls(self) -> Any | None:
        return self._api_websocket or self._websocket or self._event_websocket

    def _resolve_ws_role(self, path: str) -> str | None:
        if self.path_event == self.path_api and path == self.path_event:
            return "universal"
        if path == self.path_event:
            return "event"
        if path == self.path_api:
            return "api"
        return None

    def _current_ws_by_role(self, role: str) -> Any | None:
        if role == "event":
            return self._event_websocket
        if role == "api":
            return self._api_websocket
        return self._websocket

    def _authorize_headers(self, headers: Mapping[str, str], request_target: str) -> bool:
        if not self.access_token:
            return True
        authorization = headers.get("Authorization") or headers.get("authorization")
        if compare_secret(f"Bearer {self.access_token}", str(authorization or "")):
            return True
        if not self.allow_query_token:
            return False
        parsed = urlsplit(request_target)
        query = parse_qs(parsed.query or request_target.lstrip("?"))
        token = query.get("access_token", [""])[0]
        return compare_secret(self.access_token, str(token))

    def _extract_headers(self, websocket: Any) -> Mapping[str, str]:
        request = getattr(websocket, "request", None)
        headers = getattr(request, "headers", None)
        if headers is not None:
            return cast(Mapping[str, str], headers)
        return cast(Mapping[str, str], getattr(websocket, "request_headers", {}))

    def _extract_path(self, websocket: Any, fallback: str) -> str:
        request = getattr(websocket, "request", None)
        path = getattr(request, "path", None)
        if path:
            return str(path)
        direct = getattr(websocket, "path", None)
        if direct:
            return str(direct)
        return str(fallback)


class ModeSwitchingAdapterMiddleware(JsonWebSocketServerMiddleware, JsonHttpWebhookMiddleware):
    """Adapter middleware that switches between HTTP, WS client and reverse WS."""

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.mode = self._normalize_mode(str(self.config.get("mode", "ws-reverse")))

    async def start(self) -> None:
        """Start the configured transport mode."""
        self.logger.info("%s adapter starting in %s mode", self.name, self.mode)
        if self.mode == "ws":
            await self._run_ws_client()
            return
        if self.mode == "ws-reverse":
            await self._run_ws_server()
            return
        if self.mode == "http":
            await self._run_http_webhook_server()
            return
        raise ValueError(f"unsupported {self.name} mode: {self.mode!r}")

    async def close(self) -> None:
        """Close resources for all supported transport modes."""
        await JsonWebSocketServerMiddleware.close(self)
        if self._http_server is not None:
            await self._http_server.close()
            self._http_server = None

    async def dispatch_outbound_action(self, outbound: OutboundAction) -> Any:
        """Dispatch outbound actions over the active mode."""
        if self.mode == "http":
            return await JsonHttpWebhookMiddleware.dispatch_outbound_action(self, outbound)
        return await JsonWebSocketClientMiddleware.dispatch_outbound_action(self, outbound)

    @abstractmethod
    def _normalize_mode(self, value: str) -> str:
        """Normalize an adapter-specific mode string."""
        raise NotImplementedError


def _get_path(payload: Mapping[str, Any], path: str | Sequence[str] | None) -> Any:
    if path is None:
        return None
    parts = path.split(".") if isinstance(path, str) else list(path)
    current: Any = payload
    for part in parts:
        if isinstance(current, Mapping):
            current = current.get(str(part))
            continue
        if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                current = current[int(part)]
                continue
            except (ValueError, IndexError):
                return None
        return None
    return current


def _maybe_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _message_from_payload(value: Any) -> Message:
    if value is None:
        return Message()
    if isinstance(value, Message):
        return value
    if isinstance(value, str):
        return Message(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        segments = [item for item in value if isinstance(item, Mapping)]
        return Message(cast(list[Mapping[str, Any]], segments))
    return Message(str(value))


if TYPE_CHECKING:
    from ..runtime import Runtime
