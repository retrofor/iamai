"""Dependency injection marker helpers used by handlers and middleware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class Depends:
    """Declare that a parameter should be resolved from a dependency provider."""

    provider: Callable[..., Any] | Any
    use_cache: bool = True


def depends(provider: Callable[..., Any] | Any, *, use_cache: bool = True) -> Any:
    """Return a dependency marker for a handler or middleware parameter."""
    return Depends(provider=provider, use_cache=use_cache)
