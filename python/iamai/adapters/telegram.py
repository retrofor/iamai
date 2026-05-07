"""Telegram Bot API adapter using long polling."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ..adapter import Adapter
from ..core import new_event_id
from ..event import Event
from ..httpio import request_json
from ..message import Message


class TelegramAdapter(Adapter):
    """Adapter for Telegram Bot API long polling."""

    name = "telegram"

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.token = str(self.config.get("token", ""))
        self.api_base_url = str(self.config.get("api_base_url", "https://api.telegram.org"))
        self.poll_timeout = int(self.config.get("poll_timeout", 30))
        self.request_timeout = float(self.config.get("request_timeout", self.poll_timeout + 10))
        self.limit = int(self.config.get("limit", 100))
        self.allowed_updates = self.config.get("allowed_updates", ["message"])
        self.reconnect_interval = float(self.config.get("reconnect_interval", 3.0))
        self.platform = str(self.config.get("platform", "telegram"))
        self._closed = asyncio.Event()
        self._offset: int | None = _optional_int(self.config.get("offset"))

    async def start(self) -> None:
        """Start receiving Telegram updates through long polling."""
        if not self.token:
            raise RuntimeError("telegram token is required")
        self.logger.info("telegram adapter starting with long polling")
        while not self._closed.is_set():
            try:
                updates = await self._get_updates()
                for update in updates:
                    update_id = _optional_int(update.get("update_id"))
                    if update_id is not None:
                        self._offset = update_id + 1
                    event = self._normalize_update(update)
                    if event is not None:
                        await self.emit(event)
            except asyncio.CancelledError:
                raise
            except Exception:
                self.logger.exception("telegram polling failed")
                if self._closed.is_set():
                    break
                await asyncio.sleep(self.reconnect_interval)

    async def close(self) -> None:
        """Stop the long polling loop."""
        self._closed.set()

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        """Send a Telegram text message to an event chat or explicit chat id."""
        chat_id = self._resolve_chat_id(event=event, target=target)
        return await self.call_api(
            "sendMessage",
            chat_id=chat_id,
            text=Message.ensure(message).plain_text(),
        )

    async def call_api(self, action: str, **params: Any) -> Any:
        """Call one Telegram Bot API method."""
        if not self.token:
            raise RuntimeError("telegram token is required")
        result = await request_json(
            self._method_url(action),
            json_body=params,
            timeout=self.request_timeout,
        )
        if not isinstance(result, Mapping):
            raise RuntimeError("telegram API returned a non-object response")
        if not result.get("ok"):
            description = str(result.get("description", "telegram API request failed"))
            raise RuntimeError(description)
        return result.get("result")

    async def _get_updates(self) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "timeout": self.poll_timeout,
            "limit": self.limit,
            "allowed_updates": self.allowed_updates,
        }
        if self._offset is not None:
            params["offset"] = self._offset
        result = await self.call_api("getUpdates", **params)
        if not isinstance(result, list):
            return []
        return [dict(item) for item in result if isinstance(item, Mapping)]

    def _normalize_update(self, update: Mapping[str, Any]) -> Event | None:
        message = update.get("message") or update.get("edited_message")
        if not isinstance(message, Mapping):
            self.logger.debug("ignored Telegram update without message: %s", update)
            return None
        chat = message.get("chat")
        user = message.get("from")
        if not isinstance(chat, Mapping):
            return None
        text = _telegram_text(message)
        chat_id = chat.get("id")
        user_id = user.get("id") if isinstance(user, Mapping) else None
        detail_type = str(chat.get("type", "private"))
        return Event(
            id=str(message.get("message_id") or update.get("update_id") or new_event_id()),
            adapter=self.name,
            platform=self.platform,
            type="message",
            detail_type=detail_type,
            user_id=None if user_id is None else str(user_id),
            channel_id=None if chat_id is None else str(chat_id),
            guild_id=None if detail_type == "private" or chat_id is None else str(chat_id),
            self_id=None,
            message=Message(text),
            raw=dict(update),
        )

    def _resolve_chat_id(self, *, event: Event | None, target: Any | None) -> int | str:
        if isinstance(target, Mapping):
            value = target.get("chat_id") or target.get("channel_id")
            if value is not None:
                return _int_like(value)
        if target is not None:
            return _int_like(target)
        if event is not None and event.channel_id is not None:
            return _int_like(event.channel_id)
        raise ValueError("telegram send_message requires an event or chat_id target")

    def _method_url(self, action: str) -> str:
        base = self.api_base_url.rstrip("/")
        return f"{base}/bot{self.token}/{action}"


def _telegram_text(message: Mapping[str, Any]) -> str:
    text = message.get("text")
    if text is not None:
        return str(text)
    caption = message.get("caption")
    if caption is not None:
        return str(caption)
    return ""


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_like(value: Any) -> int | str:
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


if TYPE_CHECKING:
    from ..runtime import Runtime
