"""Composable permission predicates for handler access control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable


@dataclass(frozen=True, slots=True)
class Permission:
    """Composable async permission predicate."""

    _executor: Callable[["Runtime", "Context", dict[Any, Any]], Any]
    name: str = "permission"

    async def evaluate(
        self,
        runtime: "Runtime",
        ctx: "Context",
        cache: dict[Any, Any],
    ) -> bool:
        """Return whether the current context is allowed to enter a handler."""
        result = await self._executor(runtime, ctx, cache)
        return bool(result)

    def __and__(self, other: Any) -> "Permission":
        """Return a permission that requires both predicates to pass."""
        other_permission = ensure_permission(other)

        async def _executor(runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]) -> bool:
            if not await self.evaluate(runtime, ctx, cache):
                return False
            return await other_permission.evaluate(runtime, ctx, cache)

        return Permission(_executor, name=f"({self.name}&{other_permission.name})")

    def __or__(self, other: Any) -> "Permission":
        """Return a permission that allows either predicate to pass."""
        other_permission = ensure_permission(other)

        async def _executor(runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]) -> bool:
            if await self.evaluate(runtime, ctx, cache):
                return True
            return await other_permission.evaluate(runtime, ctx, cache)

        return Permission(_executor, name=f"({self.name}|{other_permission.name})")

    def __invert__(self) -> "Permission":
        """Return a permission that negates this predicate."""
        async def _executor(runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]) -> bool:
            return not await self.evaluate(runtime, ctx, cache)

        return Permission(_executor, name=f"~{self.name}")


def permission(func: Callable[..., Any]) -> Permission:
    """Wrap a callable as a dependency-injected permission predicate."""

    async def _executor(runtime: "Runtime", ctx: "Context", cache: dict[Any, Any]) -> Any:
        return await runtime._invoke_callable(func, ctx, cache=cache)

    return Permission(_executor, name=getattr(func, "__name__", "permission"))


def ensure_permission(value: Any) -> Permission:
    """Coerce a ``Permission`` or callable into a ``Permission`` instance."""

    if isinstance(value, Permission):
        return value
    if callable(value):
        return permission(value)
    raise TypeError(f"unsupported permission value: {value!r}")


def allow_all() -> Permission:
    """Create a permission that always allows the handler to run."""

    return permission(lambda: True)


def deny_all() -> Permission:
    """Create a permission that always denies the handler."""

    return permission(lambda: False)


def any_of(*values: Any) -> Permission:
    """Create a permission that passes when at least one child passes."""

    if not values:
        return deny_all()
    current = ensure_permission(values[0])
    for value in values[1:]:
        current = current | ensure_permission(value)
    return current


def all_of(*values: Any) -> Permission:
    """Create a permission that passes only when every child passes."""

    current = allow_all()
    for value in values:
        current = current & ensure_permission(value)
    return current


def user_in(*user_ids: str | int) -> Permission:
    """Allow only events whose ``user_id`` appears in ``user_ids``."""

    allowed = {str(user_id) for user_id in user_ids}
    return permission(lambda event: (event.user_id or "") in allowed)


def channel_in(*channel_ids: str | int) -> Permission:
    """Allow only events from one of the selected channel IDs."""

    allowed = {str(channel_id) for channel_id in channel_ids}
    return permission(lambda event: (event.channel_id or "") in allowed)


def group_in(*group_ids: str | int) -> Permission:
    """Allow only group-like events from one of the selected group IDs."""

    allowed = {str(group_id) for group_id in group_ids}
    return permission(lambda event: (event.guild_id or event.channel_id or "") in allowed)


def adapter_in(*adapter_names: str) -> Permission:
    """Allow only events emitted by one of the selected adapters."""

    allowed = {str(name) for name in adapter_names}
    return permission(lambda event: event.adapter in allowed)


def superusers(*user_ids: str | int) -> Permission:
    """Allow configured runtime superusers or the explicit IDs passed here."""

    explicit = {str(user_id) for user_id in user_ids}

    def _check(runtime: "Runtime", event: Any) -> bool:
        configured = runtime.superusers()
        allowed = explicit or configured
        return (event.user_id or "") in allowed

    return permission(_check)


def predicate(func: Callable[..., Any]) -> Permission:
    """Alias for ``permission`` that reads naturally in decorator arguments."""

    return ensure_permission(func)


if TYPE_CHECKING:
    from .runtime import Runtime
    from .context import Context
