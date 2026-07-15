"""Installable reference adapter fixture."""

from typing import Any

from iamai import Adapter, Event, Message
from pydantic import BaseModel, Field


class ReferenceAdapterConfig(BaseModel):
    """Schema-bearing configuration published by the reference adapter."""

    endpoint: str = "https://example.invalid/events"
    access_token: str = Field(default="", json_schema_extra={"writeOnly": True})
    token_hint: str = "metadata-only"


class ReferenceAdapter(Adapter):
    """Minimal adapter exported through the ``iamai.adapters`` entry-point group."""

    name = "reference_adapter"
    config_model = ReferenceAdapterConfig

    async def start(self) -> None:
        return None

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        return None
