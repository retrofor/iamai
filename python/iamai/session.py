"""Session waiters for multi-turn plugin workflows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable


@dataclass(slots=True)
class Waiter:
    """Pending wait operation for a session-scoped future."""

    key: str
    future: asyncio.Future["Context"]
    rule: Callable[["Context"], Any] | None = None


class SessionManager:
    """Coordinate per-session waiter registration and message consumption."""

    def __init__(self) -> None:
        self._waiters: list[Waiter] = []
        self._backlog: dict[str, list["Context"]] = {}

    def session_key(self, ctx: "Context") -> str:
        """Return the stable waiter key for a context."""
        event = ctx.event
        adapter = event.adapter or "adapter"
        channel = event.channel_id or event.guild_id or "global"
        user = event.user_id or "anonymous"
        return f"{adapter}:{channel}:{user}"

    async def wait_for(
        self,
        ctx: "Context",
        *,
        timeout: float | None = 60.0,
        key: str | None = None,
        rule: Callable[["Context"], Any] | None = None,
    ) -> "Context":
        """Wait for a future context in the same session."""
        loop = asyncio.get_running_loop()
        waiter = Waiter(
            key=key or self.session_key(ctx),
            future=loop.create_future(),
            rule=rule,
        )
        backlog = self._backlog.get(waiter.key, [])
        for item in list(backlog):
            if rule is not None:
                result = rule(item)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    continue
            backlog.remove(item)
            return item
        self._waiters.append(waiter)
        try:
            return await asyncio.wait_for(waiter.future, timeout=timeout)
        finally:
            if waiter in self._waiters:
                self._waiters.remove(waiter)

    async def consume(self, ctx: "Context") -> bool:
        """Deliver a context to the first waiter that accepts it."""
        key = self.session_key(ctx)
        for waiter in list(self._waiters):
            if waiter.key != key or waiter.future.done():
                continue
            if waiter.rule is not None:
                result = waiter.rule(ctx)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    continue
            waiter.future.set_result(ctx)
            self._waiters.remove(waiter)
            return True
        backlog = self._backlog.setdefault(key, [])
        backlog.append(ctx)
        if len(backlog) > 3:
            del backlog[:-3]
        return False

    def cancel(self, key: str | None = None) -> int:
        """Cancel waiters, optionally scoped to a single key."""
        count = 0
        for waiter in list(self._waiters):
            if key is not None and waiter.key != key:
                continue
            if not waiter.future.done():
                waiter.future.cancel()
            self._waiters.remove(waiter)
            count += 1
        return count

    def list_waiters(self) -> list[dict[str, Any]]:
        """Return diagnostic information about active waiters."""
        return [{"key": waiter.key, "done": waiter.future.done()} for waiter in self._waiters]


if TYPE_CHECKING:
    from .context import Context
