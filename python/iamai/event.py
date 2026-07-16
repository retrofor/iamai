"""Normalized event model shared across adapters and plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Mapping
from typing import Any

from .message import Message
from .serialization import (
    SERIALIZATION_CONTRACT_VERSION,
    SerializationContractError,
    _canonical_json,
    _child_path,
    _copy_json_value,
    _load_json_object,
    _require_contract_version,
    _require_field,
    _require_object,
    _require_optional_string,
    _require_string,
    _validate_json_value,
)


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

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "Event":
        """Build an event from a versioned serialization-contract payload."""
        object_payload = _require_object(payload, path="$")
        _validate_json_value(object_payload, path="$")
        _require_contract_version(object_payload, path="$")
        message_path = "$.message"
        message_payload = _require_object(
            _require_field(object_payload, "message", path="$"),
            path=message_path,
        )
        raw_path = "$.raw"
        raw = _require_object(object_payload.get("raw", {}), path=raw_path)
        return cls(
            id=_required_event_string(object_payload, "id"),
            adapter=_required_event_string(object_payload, "adapter"),
            platform=_required_event_string(object_payload, "platform"),
            type=_required_event_string(object_payload, "type"),
            detail_type=_optional_event_string(object_payload, "detail_type"),
            sub_type=_optional_event_string(object_payload, "sub_type"),
            user_id=_optional_event_string(object_payload, "user_id"),
            channel_id=_optional_event_string(object_payload, "channel_id"),
            guild_id=_optional_event_string(object_payload, "guild_id"),
            self_id=_optional_event_string(object_payload, "self_id"),
            message=Message._from_payload_at_path(message_payload, path=message_path),
            raw=_copy_json_value(raw, path=raw_path),
        )

    @classmethod
    def from_json(cls, payload: str | bytes | bytearray) -> "Event":
        """Build an event from strict JSON using the serialization contract."""
        return cls.from_payload(_load_json_object(payload))

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

    def to_payload(self) -> dict[str, Any]:
        """Return the canonical versioned serialization-contract payload."""
        if not isinstance(self.message, Message):
            raise SerializationContractError(
                "invalid_message",
                "$.message",
                "value must be a Message",
            )
        payload = {
            "contract_version": SERIALIZATION_CONTRACT_VERSION,
            "id": _require_string(self.id, path="$.id", non_empty=True),
            "adapter": _require_string(self.adapter, path="$.adapter", non_empty=True),
            "platform": _require_string(self.platform, path="$.platform", non_empty=True),
            "type": _require_string(self.type, path="$.type", non_empty=True),
            "detail_type": _require_optional_string(self.detail_type, path="$.detail_type"),
            "sub_type": _require_optional_string(self.sub_type, path="$.sub_type"),
            "user_id": _require_optional_string(self.user_id, path="$.user_id"),
            "channel_id": _require_optional_string(self.channel_id, path="$.channel_id"),
            "guild_id": _require_optional_string(self.guild_id, path="$.guild_id"),
            "self_id": _require_optional_string(self.self_id, path="$.self_id"),
            "message": self.message.to_payload(),
            "raw": _copy_json_value(_require_object(self.raw, path="$.raw"), path="$.raw"),
        }
        return payload

    def to_json(self) -> str:
        """Return canonical strict JSON for this event."""
        return _canonical_json(self.to_payload())


def _maybe_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _required_event_string(payload: Mapping[str, Any], field: str) -> str:
    return _require_string(
        _require_field(payload, field, path="$"),
        path=_child_path("$", field),
        non_empty=True,
    )


def _optional_event_string(payload: Mapping[str, Any], field: str) -> str | None:
    return _require_optional_string(payload.get(field), path=_child_path("$", field))
