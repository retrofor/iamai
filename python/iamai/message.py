"""Message chain wrapper backed by the Rust core extension."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any, cast

from .core import CoreMessage


class Message:
    """Protocol-neutral message builder and container."""

    __slots__ = ("_core",)

    def __init__(self, value: str | Iterable[Mapping[str, Any]] | "Message" | None = None, *, core: CoreMessage | None = None) -> None:
        if core is not None:
            self._core = core.copy()
        elif isinstance(value, Message):
            self._core = value._core.copy()
        elif value is None:
            self._core = CoreMessage()
        elif isinstance(value, str):
            self._core = CoreMessage.from_plain_text(value)
        else:
            self._core = CoreMessage.from_json(json.dumps(list(value)))

    @classmethod
    def ensure(cls, value: str | "Message" | Iterable[Mapping[str, Any]]) -> "Message":
        """Return ``value`` as a ``Message`` instance."""
        return value if isinstance(value, cls) else cls(value)

    @classmethod
    def from_onebot11(cls, payload: Any) -> "Message":
        """Create a message from a OneBot11 message payload."""
        return cls(core=CoreMessage.from_onebot11_json(json.dumps(payload)))

    @property
    def core(self) -> CoreMessage:
        """Return the underlying Rust-backed core message object."""
        return self._core

    @property
    def segments(self) -> list[dict[str, Any]]:
        """Return message segments as plain dictionaries."""
        return cast(list[dict[str, Any]], json.loads(self._core.to_json()))

    def append_text(self, text: str) -> "Message":
        """Append a text segment and return this message."""
        self._core.push_text(str(text))
        return self

    def append(self, kind: str, **data: Any) -> "Message":
        """Append a generic segment and return this message."""
        self._core.push(kind, json.dumps(data))
        return self

    def extend(self, other: str | "Message" | Iterable[Mapping[str, Any]]) -> "Message":
        """Append all segments from another message-like value."""
        other_message = Message.ensure(other)
        self._core.extend_from_json(other_message._core.to_json())
        return self

    def plain_text(self) -> str:
        """Return only the textual content of the message."""
        return self._core.plain_text()

    def render_text(self) -> str:
        """Render the message into a debug-friendly text representation."""
        return self._core.render_text()

    def to_onebot11(self) -> list[dict[str, Any]]:
        """Convert the message into OneBot11 segment dictionaries."""
        return cast(list[dict[str, Any]], json.loads(self._core.to_onebot11_json()))

    def copy(self) -> "Message":
        """Return a copy of this message."""
        return Message(core=self._core.copy())

    def __bool__(self) -> bool:
        return not self._core.is_empty()

    def __add__(self, other: str | "Message" | Iterable[Mapping[str, Any]]) -> "Message":
        new_message = self.copy()
        new_message.extend(other)
        return new_message

    def __str__(self) -> str:
        return self.render_text()

    def __repr__(self) -> str:
        return f"Message({self.render_text()!r})"
