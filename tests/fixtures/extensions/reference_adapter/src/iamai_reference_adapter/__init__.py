"""Installable reference adapter fixture."""

from typing import Any

from iamai import Adapter, Event, Message


class ReferenceAdapter(Adapter):
    """Minimal adapter exported through the ``iamai.adapters`` entry-point group."""

    name = "reference_adapter"

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
