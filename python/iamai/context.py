"""Per-handler execution context exposed to plugin callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .event import Event
from .message import Message


@dataclass(slots=True)
class Context:
    """Runtime context passed to handlers and middleware."""

    runtime: "Runtime"
    adapter: "Adapter"
    plugin: "Plugin"
    event: Event
    handler: "BoundHandler"
    matches: dict[str, Any] = field(default_factory=dict)

    @property
    def text(self) -> str:
        """Return the plain text carried by the current event."""
        return self.event.text

    @property
    def args(self) -> str:
        """Return command arguments captured during command matching."""
        return str(self.matches.get("args", ""))

    @property
    def command_name(self) -> str | None:
        """Return the matched command name, if any."""
        value = self.matches.get("command")
        return None if value is None else str(value)

    @property
    def config(self) -> dict[str, Any]:
        """Return this plugin's validated configuration mapping."""
        return self.plugin.config

    @property
    def state(self) -> dict[str, Any]:
        """Return this plugin's private state mapping."""
        return self.plugin.state

    @property
    def shared_state(self) -> dict[str, Any]:
        """Return the runtime-wide shared state mapping."""
        return self.runtime.state

    async def reply(self, message: str | Message) -> Any:
        """Send a reply to the event's default target."""
        return await self.adapter.send_message(Message.ensure(message), event=self.event)

    async def send(self, message: str | Message, *, target: Any | None = None) -> Any:
        """Send a message to an explicit adapter target."""
        return await self.adapter.send_message(Message.ensure(message), target=target)

    async def call_api(self, action: str, **params: Any) -> Any:
        """Call an API action on the current adapter."""
        return await self.adapter.call_api(action, **params)

    async def reload_plugins(self) -> None:
        """Reload user plugins through the owning runtime."""
        await self.runtime.reload_plugins()

    async def wait_for_message(
        self,
        *,
        timeout: float | None = 60.0,
        rule: Callable[["Context"], Any] | None = None,
    ) -> "Context":
        """Wait for the next message in the same session."""
        if rule is None:
            prefixes = self.runtime.command_prefixes()

            def is_plain_message(ctx: "Context") -> bool:
                return not ctx.text.strip().startswith(prefixes)

            rule = is_plain_message
        return await self.runtime.sessions.wait_for(self, timeout=timeout, rule=rule)

if TYPE_CHECKING:
    from .adapter import Adapter
    from .runtime import Runtime
    from .plugin import BoundHandler, Plugin
