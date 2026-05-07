"""Terminal adapter for local interactive development and demos."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..adapter import Adapter
from ..core import new_event_id
from ..event import Event
from ..message import Message


class TerminalAdapter(Adapter):
    """Interactive stdin/stdout adapter for local development."""

    name = "terminal"

    def __init__(self, runtime: "Runtime", config: dict[str, Any] | None = None) -> None:
        super().__init__(runtime, config)
        self.prompt = str(self.config.get("prompt", "iamai> "))
        self.self_id = str(self.config.get("self_id", "terminal-runtime"))
        self.user_id = str(self.config.get("user_id", "terminal-user"))
        self.channel_id = str(self.config.get("channel_id", "terminal"))
        self.exit_commands = {
            str(item) for item in self.config.get("exit_commands", ["/quit", "/exit", ":q"])
        }
        self.output_prefix = str(self.config.get("output_prefix", "runtime> "))

    async def start(self) -> None:
        """Read terminal lines and emit them as message events."""
        self.logger.info("terminal adapter started")
        while True:
            if self.runtime._stop_event.is_set():
                return
            try:
                line = await asyncio.to_thread(input, self.prompt)
            except EOFError:
                await self.runtime.stop()
                return
            if line.strip() in self.exit_commands:
                await self.runtime.stop()
                return
            if not line.strip():
                continue
            event = Event(
                id=new_event_id(),
                adapter=self.name,
                platform="terminal",
                type="message",
                detail_type="line",
                user_id=self.user_id,
                channel_id=self.channel_id,
                self_id=self.self_id,
                message=Message(line),
                raw={"text": line},
            )
            await self.emit(event)

    async def send_message(
        self,
        message: Message,
        *,
        event: Event | None = None,
        target: Any | None = None,
    ) -> Any:
        """Render an outgoing message to stdout."""
        rendered = Message.ensure(message).render_text()
        print(f"{self.output_prefix}{rendered}")
        return {"ok": True, "target": target, "event_id": getattr(event, "id", None)}


if TYPE_CHECKING:
    from ..runtime import Runtime
