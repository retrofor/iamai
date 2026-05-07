"""Plugin base class plus decorators for handlers and command entrypoints."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

from .middleware import BoundMiddleware, MiddlewareSpec
from .permissions import Permission, ensure_permission
from .rules import Rule, ensure_rule

HandlerFunc = TypeVar("HandlerFunc", bound=Callable[..., Any])


@dataclass(frozen=True, slots=True)
class HandlerSpec:
    """Declarative metadata attached to a handler callback."""

    func_name: str
    kind: str
    commands: tuple[str, ...] = ()
    prefixes: tuple[str, ...] = ()
    adapters: tuple[str, ...] = ()
    event_types: tuple[str, ...] = ()
    detail_types: tuple[str, ...] = ()
    startswith: tuple[str, ...] = ()
    contains: tuple[str, ...] = ()
    regex: str | None = None
    rule: Rule | None = None
    permission: Permission | None = None
    priority: int = 100
    block: bool = False


@dataclass(slots=True)
class BoundHandler:
    """A handler callback bound to a concrete plugin instance."""

    plugin: "Plugin"
    spec: HandlerSpec
    callback: Callable[["Context"], Awaitable[Any] | Any]


def command(
    *names: str,
    prefixes: tuple[str, ...] | list[str] | None = None,
    adapters: tuple[str, ...] | list[str] | None = None,
    event_types: tuple[str, ...] | list[str] | None = None,
    detail_types: tuple[str, ...] | list[str] | None = None,
    rule: Rule | Callable[..., Any] | None = None,
    permission: Permission | Callable[..., Any] | None = None,
    priority: int = 100,
    block: bool = False,
) -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorate a plugin method as a command handler."""
    return _attach_handler(
        HandlerSpec(
            func_name="",
            kind="command",
            commands=tuple(names),
            prefixes=tuple(prefixes or ()),
            adapters=tuple(adapters or ()),
            event_types=tuple(event_types or ("message",)),
            detail_types=tuple(detail_types or ()),
            rule=None if rule is None else ensure_rule(rule),
            permission=None if permission is None else ensure_permission(permission),
            priority=priority,
            block=block,
        )
    )


def message_handler(
    *,
    adapters: tuple[str, ...] | list[str] | None = None,
    event_types: tuple[str, ...] | list[str] | None = None,
    detail_types: tuple[str, ...] | list[str] | None = None,
    startswith: tuple[str, ...] | list[str] | None = None,
    contains: tuple[str, ...] | list[str] | None = None,
    regex: str | None = None,
    rule: Rule | Callable[..., Any] | None = None,
    permission: Permission | Callable[..., Any] | None = None,
    priority: int = 100,
    block: bool = False,
) -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorate a plugin method as a message handler."""
    return _attach_handler(
        HandlerSpec(
            func_name="",
            kind="message",
            adapters=tuple(adapters or ()),
            event_types=tuple(event_types or ("message",)),
            detail_types=tuple(detail_types or ()),
            startswith=tuple(startswith or ()),
            contains=tuple(contains or ()),
            regex=regex,
            rule=None if rule is None else ensure_rule(rule),
            permission=None if permission is None else ensure_permission(permission),
            priority=priority,
            block=block,
        )
    )


def event_handler(
    *,
    adapters: tuple[str, ...] | list[str] | None = None,
    event_types: tuple[str, ...] | list[str] | None = None,
    detail_types: tuple[str, ...] | list[str] | None = None,
    rule: Rule | Callable[..., Any] | None = None,
    permission: Permission | Callable[..., Any] | None = None,
    priority: int = 100,
    block: bool = False,
) -> Callable[[HandlerFunc], HandlerFunc]:
    """Decorate a plugin method as a generic event handler."""
    return _attach_handler(
        HandlerSpec(
            func_name="",
            kind="event",
            adapters=tuple(adapters or ()),
            event_types=tuple(event_types or ()),
            detail_types=tuple(detail_types or ()),
            rule=None if rule is None else ensure_rule(rule),
            permission=None if permission is None else ensure_permission(permission),
            priority=priority,
            block=block,
        )
    )


def _attach_handler(spec: HandlerSpec) -> Callable[[HandlerFunc], HandlerFunc]:
    def decorator(func: HandlerFunc) -> HandlerFunc:
        handlers = list(getattr(func, "__iamai_handlers__", []))
        handlers.append(spec)
        setattr(func, "__iamai_handlers__", handlers)
        return func

    return decorator


class Plugin:
    """Base class for user-defined iamai plugins."""

    priority = 100
    name: str | None = None
    description: str = ""
    config_model: type[Any] | None = None
    requires: tuple[str, ...] = ()
    optional_requires: tuple[str, ...] = ()
    load_after: tuple[str, ...] = ()
    load_before: tuple[str, ...] = ()
    state_scope: str = "memory"

    def __init__(self, runtime: "Runtime") -> None:
        self.runtime = runtime
        self.state: dict[str, Any] = {}
        self._config_data: dict[str, Any] = {}
        self._config_object: Any | None = None
        self.load_index = -1
        self.is_builtin = False
        self.plugin_ref = ""

    @property
    def plugin_name(self) -> str:
        """Return the effective plugin name used by config and state."""
        return self.name or self.__class__.__name__.lower()

    @property
    def config(self) -> dict[str, Any]:
        """Return a copy of this plugin's raw configuration mapping."""
        return dict(self._config_data)

    @property
    def config_obj(self) -> Any | None:
        """Return the validated plugin configuration object, if configured."""
        return self._config_object

    async def startup(self) -> None:
        """Run plugin startup logic after loading."""
        return None

    async def shutdown(self) -> None:
        """Run plugin shutdown logic before unloading."""
        return None

    def iter_handlers(self) -> list[BoundHandler]:
        """Return handlers declared on this plugin instance."""
        bound_handlers: list[BoundHandler] = []
        for _, member in inspect.getmembers(self, predicate=callable):
            specs: list[HandlerSpec] = list(getattr(member, "__iamai_handlers__", []))
            for spec in specs:
                bound_handlers.append(
                    BoundHandler(
                        plugin=self,
                        spec=HandlerSpec(func_name=member.__name__, **_spec_dict(spec)),
                        callback=member,
                    )
                )
        return sorted(bound_handlers, key=lambda item: item.spec.priority)

    def iter_middlewares(self) -> list[BoundMiddleware]:
        """Return middleware callbacks declared on this plugin instance."""
        bound_middlewares: list[BoundMiddleware] = []
        for _, member in inspect.getmembers(self, predicate=callable):
            specs: list[MiddlewareSpec] = list(getattr(member, "__iamai_middlewares__", []))
            for spec in specs:
                bound_middlewares.append(
                    BoundMiddleware(
                        plugin=self,
                        spec=MiddlewareSpec(
                            func_name=member.__name__,
                            priority=spec.priority,
                            phase=spec.phase,
                        ),
                        callback=member,
                    )
                )
        return sorted(bound_middlewares, key=lambda item: item.spec.priority)


def _spec_dict(spec: HandlerSpec) -> dict[str, Any]:
    return {
        "kind": spec.kind,
        "commands": spec.commands,
        "prefixes": spec.prefixes,
        "adapters": spec.adapters,
        "event_types": spec.event_types,
        "detail_types": spec.detail_types,
        "startswith": spec.startswith,
        "contains": spec.contains,
        "regex": spec.regex,
        "rule": spec.rule,
        "permission": spec.permission,
        "priority": spec.priority,
        "block": spec.block,
    }


if TYPE_CHECKING:
    from .context import Context
    from .runtime import Runtime
