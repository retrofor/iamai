"""Per-handler execution context exposed to plugin callbacks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .event import Event
from .message import Message


class ContextInvalidatedError(RuntimeError):
    """Raised when runtime-bound operations use a stale handler context."""


@dataclass(slots=True)
class Context:
    """Runtime context passed to handlers and middleware."""

    runtime: "Runtime"
    adapter: "Adapter"
    plugin: "Plugin"
    event: Event
    handler: "BoundHandler"
    matches: dict[str, Any] = field(default_factory=dict)
    _generation: int | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self._generation is None:
            self._generation = self.runtime._handler_generation

    @property
    def is_valid(self) -> bool:
        """Return whether this context still belongs to the active runtime generation."""
        return (
            self._generation == self.runtime._handler_generation
            and not self.runtime._stop_event.is_set()
        )

    def _assert_current(self) -> None:
        if not self.is_valid:
            raise ContextInvalidatedError(
                "context is no longer valid because the runtime generation changed"
            )

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
        self._assert_current()
        return self.plugin.config

    @property
    def state(self) -> dict[str, Any]:
        """Return this plugin's private state mapping."""
        self._assert_current()
        return self.plugin.state

    @property
    def shared_state(self) -> dict[str, Any]:
        """Return the runtime-wide shared state mapping."""
        self._assert_current()
        return self.runtime.state

    async def reply(self, message: str | Message) -> Any:
        """Send a reply to the event's default target."""
        self._assert_current()
        return await self.adapter.send_message(Message.ensure(message), event=self.event)

    async def send(self, message: str | Message, *, target: Any | None = None) -> Any:
        """Send a message to an explicit adapter target."""
        self._assert_current()
        return await self.adapter.send_message(Message.ensure(message), target=target)

    async def call_api(self, action: str, **params: Any) -> Any:
        """Call an API action on the current adapter."""
        self._assert_current()
        return await self.adapter.call_api(action, **params)

    async def reload_plugins(self) -> None:
        """Schedule a plugin reload after the current handler completes."""
        self._assert_current()
        self.runtime.request_plugin_reload()

    async def wait_for_message(
        self,
        *,
        timeout: float | None = 60.0,
        rule: Callable[["Context"], Any] | None = None,
    ) -> "Context":
        """Wait for the next message in the same session."""
        self._assert_current()
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
