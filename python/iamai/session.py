"""Session waiters for multi-turn plugin workflows."""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable


@dataclass(slots=True)
class Waiter:
    """Pending wait operation for a session-scoped future."""

    key: str
    future: asyncio.Future["Context"]
    rule: Callable[["Context"], Any] | None = None


@dataclass(slots=True)
class BacklogItem:
    """A context retained briefly for a future session waiter."""

    context: "Context"
    created_at: float


class SessionManager:
    """Coordinate per-session waiter registration and message consumption."""

    def __init__(
        self,
        *,
        max_backlog_keys: int = 1024,
        max_backlog_per_key: int = 3,
        backlog_ttl_seconds: float = 300.0,
    ) -> None:
        self._waiters: list[Waiter] = []
        self._backlog: OrderedDict[str, list[BacklogItem]] = OrderedDict()
        self._clock = time.monotonic
        self.configure(
            max_backlog_keys=max_backlog_keys,
            max_backlog_per_key=max_backlog_per_key,
            backlog_ttl_seconds=backlog_ttl_seconds,
        )

    def configure(
        self,
        *,
        max_backlog_keys: int,
        max_backlog_per_key: int,
        backlog_ttl_seconds: float,
    ) -> None:
        """Apply bounded backlog settings without replacing active waiters."""
        if max_backlog_keys <= 0 or max_backlog_per_key <= 0 or backlog_ttl_seconds <= 0:
            raise ValueError("session backlog limits must be greater than 0")
        self._max_backlog_keys = int(max_backlog_keys)
        self._max_backlog_per_key = int(max_backlog_per_key)
        self._backlog_ttl_seconds = float(backlog_ttl_seconds)
        self._prune_backlog()
        for items in self._backlog.values():
            del items[: -self._max_backlog_per_key]
        while len(self._backlog) > self._max_backlog_keys:
            self._backlog.popitem(last=False)

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
        self._prune_backlog()
        backlog = self._backlog.get(waiter.key, [])
        for item in list(backlog):
            if rule is not None:
                result = rule(item.context)
                if asyncio.iscoroutine(result):
                    result = await result
                if not result:
                    continue
            current_backlog = self._backlog.get(waiter.key)
            if current_backlog is None or item not in current_backlog:
                continue
            current_backlog.remove(item)
            if not current_backlog:
                self._backlog.pop(waiter.key, None)
            return item.context
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
            if waiter.future.done() or waiter not in self._waiters:
                continue
            waiter.future.set_result(ctx)
            self._waiters.remove(waiter)
            return True
        self._prune_backlog()
        backlog = self._backlog.setdefault(key, [])
        backlog.append(BacklogItem(context=ctx, created_at=self._clock()))
        del backlog[: -self._max_backlog_per_key]
        self._backlog.move_to_end(key)
        while len(self._backlog) > self._max_backlog_keys:
            self._backlog.popitem(last=False)
        return False

    def _prune_backlog(self) -> None:
        cutoff = self._clock() - self._backlog_ttl_seconds
        for key, items in list(self._backlog.items()):
            items[:] = [item for item in items if item.created_at >= cutoff]
            if not items:
                self._backlog.pop(key, None)

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
