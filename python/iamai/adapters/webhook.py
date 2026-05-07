"""Generic inbound webhook adapter with optional outbound reply delivery."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ..adapter import Adapter
from ..core import new_event_id
from ..event import Event
from ..httpio import HttpError, HttpRequest, HttpResponse, SimpleHttpServer, request_json
from ..message import Message
from ..net import OutboundUrlPolicy, compare_secret
from ..webhook_security import SignatureVerificationResult, build_webhook_signature_verifier


class WebhookAdapter(Adapter):
    """Generic HTTP webhook adapter with optional signed requests and replies."""

    name = "webhook"

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.host = str(self.config.get("host", "127.0.0.1"))
        self.port = int(self.config.get("port", 8090))
        self.path = str(self.config.get("path", "/webhook"))
        self.platform = str(self.config.get("platform", "webhook"))
        self.access_token = str(self.config.get("access_token", ""))
        self.allow_query_token = bool(self.config.get("allow_query_token", False))
        self.response_format = str(self.config.get("response_format", "segments"))
        self.http_timeout = float(self.config.get("http_timeout", 10.0))
        self.read_timeout = float(self.config.get("read_timeout", 10.0))
        self.max_body_bytes = int(self.config.get("max_body_bytes", 1_048_576))
        self.allow_event_reply_url = bool(self.config.get("allow_event_reply_url", False))
        self.reply_url_allowlist = tuple(str(item) for item in self.config.get("reply_url_allowlist", []))
        self.allow_private_reply_hosts = bool(self.config.get("allow_private_reply_hosts", False))
        self.allowed_reply_schemes = tuple(
            str(item).lower() for item in self.config.get("allowed_reply_schemes", ["https"])
        )
        self._server = SimpleHttpServer(
            self.host,
            self.port,
            read_timeout=self.read_timeout,
            max_body_bytes=self.max_body_bytes,
        )
        self._server.route("POST", self.path, self._handle_request)
        self._closed = asyncio.Event()
        self._signature_verifier = build_webhook_signature_verifier(self.config)

    async def start(self) -> None:
        """Start the HTTP server and wait until the adapter is closed."""
        await self._server.start()
        self.logger.info("webhook adapter listening on http://%s:%s%s", self.host, self.port, self.path)
        await self._closed.wait()

    async def close(self) -> None:
        """Stop the HTTP server."""
        self._closed.set()
        await self._server.close()

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        """Deliver an outgoing message to a validated webhook reply target."""
        message = Message.ensure(message)
        reply_target = self._resolve_reply_target(event=event, target=target)
        if reply_target is None:
            rendered = message.render_text()
            self.logger.info("webhook reply dropped because no reply_url is available: %s", rendered)
            self.runtime.count_metric("webhook_reply_total", adapter=self.name, outcome="dropped", reason="no_reply_url")
            self.runtime.audit("webhook.reply", adapter=self.name, outcome="dropped", reason="no_reply_url")
            return {"ok": True, "message": rendered, "delivered": False}
        payload = {
            "message": message.render_text(),
            "segments": message.segments,
            "event_id": getattr(event, "id", None),
        }
        method = str(reply_target.get("method", "POST")).upper()
        headers = dict(reply_target.get("headers", {}))
        try:
            result = await request_json(
                str(reply_target["url"]),
                method=method,
                json_body=payload,
                headers=headers,
                timeout=self.http_timeout,
                policy=None if reply_target.get("trusted") else self._reply_url_policy(),
            )
        except Exception as exc:
            self.runtime.count_metric(
                "webhook_reply_total",
                adapter=self.name,
                outcome="error",
                trusted=bool(reply_target.get("trusted")),
            )
            self.runtime.audit(
                "webhook.reply",
                adapter=self.name,
                outcome="error",
                trusted=bool(reply_target.get("trusted")),
                error=type(exc).__name__,
                url=str(reply_target["url"]),
            )
            raise
        self.runtime.count_metric(
            "webhook_reply_total",
            adapter=self.name,
            outcome="sent",
            trusted=bool(reply_target.get("trusted")),
        )
        self.runtime.audit(
            "webhook.reply",
            adapter=self.name,
            outcome="sent",
            trusted=bool(reply_target.get("trusted")),
            url=str(reply_target["url"]),
        )
        return result

    async def _handle_request(self, request: HttpRequest) -> HttpResponse:
        auth_result = self._authorize_request(request)
        if not auth_result.ok:
            self._record_request(
                request,
                outcome="unauthorized",
                status=401,
                reason=auth_result.reason,
                provider=auth_result.provider,
            )
            return HttpResponse.json({"ok": False, "error": "unauthorized"}, status=401)
        if not request.has_json_content_type():
            self._record_request(
                request,
                outcome="unsupported_media_type",
                status=415,
                reason="unsupported_media_type",
                provider=auth_result.provider,
            )
            return HttpResponse.json({"ok": False, "error": "unsupported media type"}, status=415)
        try:
            payload = request.json()
        except HttpError as exc:
            self._record_request(
                request,
                outcome="invalid_json",
                status=exc.status,
                reason=exc.message,
                provider=auth_result.provider,
            )
            return HttpResponse.json({"ok": False, "error": exc.message}, status=exc.status)
        if payload is None:
            self._record_request(
                request,
                outcome="invalid_payload",
                status=400,
                reason="invalid_payload",
                provider=auth_result.provider,
            )
            return HttpResponse.json({"ok": False, "error": "invalid payload"}, status=400)
        event = self._normalize_payload(payload)
        try:
            await self.emit(event)
        except Exception:
            self._record_request(
                request,
                outcome="dispatch_error",
                status=500,
                reason="dispatch_error",
                provider=auth_result.provider,
                event_id=event.id,
            )
            raise
        self._record_request(
            request,
            outcome="accepted",
            status=200,
            reason="ok",
            provider=auth_result.provider,
            event_id=event.id,
        )
        return HttpResponse.json({"ok": True, "event_id": event.id})

    def _normalize_payload(self, payload: Any) -> Event:
        if isinstance(payload, Mapping) and isinstance(payload.get("event"), Mapping):
            payload = payload["event"]

        if isinstance(payload, Mapping) and {"adapter", "platform", "type"} <= set(payload.keys()):
            raw_payload = dict(payload.get("raw", {}))
            if self.allow_event_reply_url:
                raw_payload.setdefault("reply_url", payload.get("reply_url"))
            else:
                raw_payload.pop("reply_url", None)
                raw_payload.pop("reply_method", None)
                raw_payload.pop("reply_headers", None)
            normalized = dict(payload)
            normalized["raw"] = raw_payload
            normalized.setdefault("id", new_event_id())
            return Event.from_dict(normalized)

        if not isinstance(payload, Mapping):
            payload = {"message": str(payload)}

        message_value = payload.get("message", payload.get("text", ""))
        event = Event(
            id=new_event_id(),
            adapter=self.name,
            platform=self.platform,
            type=str(payload.get("type", "message")),
            detail_type=_maybe_str(payload.get("detail_type")) or "webhook",
            user_id=_maybe_str(payload.get("user_id")),
            channel_id=_maybe_str(payload.get("channel_id")),
            guild_id=_maybe_str(payload.get("guild_id")),
            self_id=_maybe_str(payload.get("self_id")),
            message=Message.ensure(message_value),
            raw=dict(payload),
        )
        return event

    def _authorize_request(self, request: HttpRequest) -> SignatureVerificationResult:
        provider = self._signature_verifier.provider
        if not self._token_authorized(request):
            return SignatureVerificationResult(False, provider=provider, reason="invalid_token")
        return self._signature_verifier.verify(request)

    def _token_authorized(self, request: HttpRequest) -> bool:
        if not self.access_token:
            return True
        auth = request.headers.get("authorization", "")
        if compare_secret(f"Bearer {self.access_token}", auth):
            return True
        if not self.allow_query_token:
            return False
        token = request.query.get("access_token", [""])[0]
        return compare_secret(self.access_token, str(token))

    def _record_request(
        self,
        request: HttpRequest,
        *,
        outcome: str,
        status: int,
        reason: str,
        provider: str,
        event_id: str | None = None,
    ) -> None:
        client = _client_ip(request)
        self.runtime.count_metric(
            "webhook_requests_total",
            adapter=self.name,
            outcome=outcome,
            provider=provider,
            status=status,
        )
        self.runtime.audit(
            "webhook.request",
            adapter=self.name,
            outcome=outcome,
            provider=provider,
            status=status,
            reason=reason,
            client=client,
            event_id=event_id,
            path=request.path,
        )

    def _resolve_reply_target(
        self,
        *,
        event: Event | None,
        target: Any | None,
    ) -> dict[str, Any] | None:
        if isinstance(target, Mapping):
            if "reply_url" in target:
                return {
                    "url": str(target["reply_url"]),
                    "method": target.get("reply_method", "POST"),
                    "headers": dict(target.get("headers", {})),
                    "trusted": True,
                }
            if "url" in target:
                return {
                    "url": str(target["url"]),
                    "method": target.get("method", "POST"),
                    "headers": dict(target.get("headers", {})),
                    "trusted": True,
                }
        if event is None:
            return None
        if not self.allow_event_reply_url:
            return None
        reply_url = event.raw.get("reply_url")
        if not reply_url:
            return None
        return {
            "url": str(reply_url),
            "method": event.raw.get("reply_method", "POST"),
            "headers": dict(event.raw.get("reply_headers", {})),
            "trusted": False,
        }

    def _reply_url_policy(self) -> OutboundUrlPolicy:
        return OutboundUrlPolicy(
            allowed_schemes=self.allowed_reply_schemes or ("https",),
            allowed_hosts=self.reply_url_allowlist,
            allow_private_hosts=self.allow_private_reply_hosts,
            allow_redirects=False,
        )


def _maybe_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _client_ip(request: HttpRequest) -> str | None:
    if request.client is None:
        return None
    return str(request.client[0])

if TYPE_CHECKING:
    from ..runtime import Runtime
