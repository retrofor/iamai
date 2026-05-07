"""Middleware decorators and bound middleware metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Literal, TypeVar

MiddlewareFunc = TypeVar("MiddlewareFunc", bound=Callable[..., Any])
MiddlewarePhase = Literal["before", "around", "after", "error"]


@dataclass(frozen=True, slots=True)
class MiddlewareSpec:
    """Declarative metadata attached to a middleware callback."""

    func_name: str
    priority: int = 100
    phase: MiddlewarePhase = "around"


@dataclass(slots=True)
class BoundMiddleware:
    """A middleware callback bound to a concrete plugin instance."""

    plugin: "Plugin"
    spec: MiddlewareSpec
    callback: Callable[..., Awaitable[Any] | Any]


def middleware(
    *,
    priority: int = 100,
    phase: MiddlewarePhase = "around",
) -> Callable[[MiddlewareFunc], MiddlewareFunc]:
    """Decorate a plugin method as middleware for the selected dispatch phase."""
    spec = MiddlewareSpec(func_name="", priority=priority, phase=phase)

    def decorator(func: MiddlewareFunc) -> MiddlewareFunc:
        middlewares = list(getattr(func, "__iamai_middlewares__", []))
        middlewares.append(spec)
        setattr(func, "__iamai_middlewares__", middlewares)
        return func

    return decorator


if TYPE_CHECKING:
    from .plugin import Plugin
