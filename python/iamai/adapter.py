"""Base adapter abstractions for inbound events and outbound delivery."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .event import Event
from .message import Message


class Adapter(ABC):
    """Transport bridge between iamai and an external protocol or runtime."""

    name = "adapter"

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        self.runtime = runtime
        self.config = config or {}
        self.logger = logging.getLogger(f"iamai.adapter.{self.name}")

    @abstractmethod
    async def start(self) -> None:
        """Start the adapter and begin receiving external events."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close adapter resources before the runtime shuts down."""
        return None

    @abstractmethod
    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        """Send a message to an adapter-specific event or target."""
        raise NotImplementedError

    async def call_api(self, action: str, **params: Any) -> Any:
        """Call an adapter-specific API action."""
        raise RuntimeError(f"adapter {self.name!r} does not expose call_api")

    async def emit(self, event: Event) -> bool:
        """Emit an event and return whether the runtime admitted it."""
        result = await self.runtime.dispatch(event, self)
        return result is not False


if TYPE_CHECKING:
    from .runtime import Runtime
