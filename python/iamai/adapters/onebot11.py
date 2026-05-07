"""OneBot11 adapter supporting websocket and HTTP operating modes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ..core import normalize_onebot11_payload
from ..event import Event
from ..httpio import HttpRequest
from ..message import Message
from .middleware import InboundEnvelope, ModeSwitchingAdapterMiddleware, OutboundAction


class OneBot11Adapter(ModeSwitchingAdapterMiddleware):
    """Adapter for OneBot11 websocket and HTTP integration modes."""

    name = "onebot11"

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.url = str(self.config.get("url", "ws://127.0.0.1:6700"))
        self.host = str(self.config.get("host", "127.0.0.1"))
        self.port = int(self.config.get("port", 8080))
        self.path = str(self.config.get("path", "/onebot/v11/ws"))
        self.path_event = str(self.config.get("path_event", self.config.get("event_path", self.path)))
        self.path_api = str(self.config.get("path_api", self.config.get("api_path", self.path)))
        self.api_base_url = str(
            self.config.get("api_base_url", self.config.get("api_url", "http://127.0.0.1:5700"))
        )
        self.access_token = str(self.config.get("access_token", ""))
        self.allow_query_token = bool(self.config.get("allow_query_token", False))
        self.platform = str(self.config.get("platform", "qq"))
        self.reconnect_interval = float(self.config.get("reconnect_interval", 5.0))
        self.api_timeout = float(self.config.get("api_timeout", 10.0))
        self.ping_interval = float(self.config.get("ping_interval", 20.0))
        self.ping_timeout = float(self.config.get("ping_timeout", 20.0))
        self.open_timeout = float(self.config.get("open_timeout", 10.0))
        self.max_size = int(self.config.get("max_size", 1_048_576))
        self.origins = self.config.get("origins")
        self.read_timeout = float(self.config.get("read_timeout", 10.0))
        self.max_body_bytes = int(self.config.get("max_body_bytes", 1_048_576))

    def normalize_payload(
        self,
        payload: Any,
        envelope: InboundEnvelope,
    ) -> Event | list[Event] | None:
        """Normalize OneBot11 event payloads through the Rust core helper."""
        if not isinstance(payload, Mapping) or "post_type" not in payload:
            self.logger.debug("ignored OneBot11 payload: %s", payload)
            return None
        normalized = normalize_onebot11_payload(
            payload,
            adapter_name=self.name,
            platform=self.platform,
        )
        return Event.from_dict(normalized)

    def encode_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> OutboundAction:
        """Resolve a message target and encode the matching OneBot11 action."""
        action, params = self._resolve_send_target(event=event, target=target, message=message)
        return OutboundAction(kind="message", action=action, params=params)

    def _record_http_request(self, request: HttpRequest, *, outcome: str, status: int, reason: str) -> None:
        client = None if request.client is None else str(request.client[0])
        self.runtime.count_metric(
            "onebot_http_requests_total",
            adapter=self.name,
            outcome=outcome,
            status=status,
        )
        self.runtime.audit(
            "onebot.http_request",
            adapter=self.name,
            outcome=outcome,
            status=status,
            reason=reason,
            client=client,
            path=request.path,
        )

    async def _handle_payload(self, payload: str | bytes, *, role: str = "universal") -> None:
        """Compatibility shim for tests and older subclasses."""
        await self._handle_ws_payload(payload, role=role)

    def _resolve_send_target(
        self,
        *,
        event: Event | None,
        target: Any | None,
        message: Message,
    ) -> tuple[str, dict[str, Any]]:
        if isinstance(target, Mapping):
            if "action" in target:
                params = dict(target.get("params", {}))
                params.setdefault("message", message.to_onebot11())
                return str(target["action"]), params
            if "group_id" in target:
                return "send_group_msg", {
                    "group_id": _int_like(target["group_id"]),
                    "message": message.to_onebot11(),
                }
            if "user_id" in target:
                return "send_private_msg", {
                    "user_id": _int_like(target["user_id"]),
                    "message": message.to_onebot11(),
                }
        if event is not None:
            raw = event.raw
            if raw.get("message_type") == "group" or raw.get("group_id") is not None:
                return "send_group_msg", {
                    "group_id": _int_like(raw.get("group_id") or event.channel_id),
                    "message": message.to_onebot11(),
                }
            return "send_private_msg", {
                "user_id": _int_like(raw.get("user_id") or event.user_id),
                "message": message.to_onebot11(),
            }
        raise ValueError("onebot11 send_message requires either an event or an explicit target")

    def _normalize_mode(self, value: str) -> str:
        if value in {"reverse-ws", "ws-reverse"}:
            return "ws-reverse"
        return value


def _int_like(value: Any) -> int | str:
    if value is None:
        raise ValueError("OneBot11 target id is required")
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)

if TYPE_CHECKING:
    from ..runtime import Runtime
