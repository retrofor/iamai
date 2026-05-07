"""Normalized event model shared across adapters and plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .message import Message


@dataclass(slots=True)
class Event:
    """Adapter-agnostic event payload used by the dispatch pipeline."""

    id: str
    adapter: str
    platform: str
    type: str
    detail_type: str | None = None
    sub_type: str | None = None
    user_id: str | None = None
    channel_id: str | None = None
    guild_id: str | None = None
    self_id: str | None = None
    message: Message = field(default_factory=Message)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Event":
        """Build an event from a normalized dictionary payload."""
        return cls(
            id=str(payload["id"]),
            adapter=str(payload["adapter"]),
            platform=str(payload["platform"]),
            type=str(payload["type"]),
            detail_type=payload.get("detail_type"),
            sub_type=payload.get("sub_type"),
            user_id=_maybe_str(payload.get("user_id")),
            channel_id=_maybe_str(payload.get("channel_id")),
            guild_id=_maybe_str(payload.get("guild_id")),
            self_id=_maybe_str(payload.get("self_id")),
            message=Message(payload.get("message", [])),
            raw=dict(payload.get("raw", {})),
        )

    @property
    def text(self) -> str:
        """Return the plain text representation of the event message."""
        return self.message.plain_text()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event into a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "adapter": self.adapter,
            "platform": self.platform,
            "type": self.type,
            "detail_type": self.detail_type,
            "sub_type": self.sub_type,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "guild_id": self.guild_id,
            "self_id": self.self_id,
            "message": self.message.segments,
            "raw": self.raw,
        }


def _maybe_str(value: Any) -> str | None:
    return None if value is None else str(value)
