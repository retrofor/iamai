"""Installable reference adapter fixture."""

import asyncio
from typing import Any

from iamai import Adapter, Event, Message, Runtime
from pydantic import BaseModel, Field


class ReferenceAdapterConfig(BaseModel):
    """Schema-bearing configuration published by the reference adapter."""

    endpoint: str = "https://example.invalid/events"
    access_token: str = Field(default="", json_schema_extra={"writeOnly": True})
    token_hint: str = "metadata-only"


class ReferenceAdapter(Adapter):
    """Conforming adapter exported through the ``iamai.adapters`` entry-point group."""

    name = "reference_adapter"
    config_model = ReferenceAdapterConfig

    def __init__(
        self,
        runtime: Runtime,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(runtime, config)
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.closed = False

    async def start(self) -> None:
        self.started.set()
        await self.release.wait()

    async def close(self) -> None:
        self.closed = True
        self.release.set()

    def normalize(self, payload: dict[str, Any]) -> Event:
        """Normalize the reference platform payload used by conformance tests."""
        return Event(
            id=str(payload["id"]),
            adapter=self.name,
            platform="reference",
            type="message",
            channel_id=str(payload["channel_id"]),
            user_id=str(payload["user_id"]),
            message=Message(str(payload["text"])),
            raw=dict(payload),
        )

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        destination = target if target is not None else event.channel_id if event else None
        return {"target": destination, "text": message.plain_text()}

    async def call_api(self, action: str, **params: Any) -> Any:
        if action == "fail":
            raise ReferenceAdapterError("forced reference API failure")
        return {"action": action, "params": params}


class ReferenceAdapterError(RuntimeError):
    """Stable protocol error exposed by the reference adapter."""


class ReferenceFailingAdapter(ReferenceAdapter):
    """Reference adapter whose startup demonstrates failure cleanup."""

    name = "reference_failing_adapter"

    def __init__(
        self,
        runtime: Runtime,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(runtime, config)
        self.resource_open = False

    async def start(self) -> None:
        self.resource_open = True
        raise ReferenceAdapterError("forced reference startup failure")

    async def close(self) -> None:
        self.resource_open = False
        await super().close()
