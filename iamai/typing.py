"""iamai type hint support.

This module defines some of the types used by iamai.
"""

# ruff: noqa: TCH001
from typing import TYPE_CHECKING, Awaitable, Callable, Optional, TypeVar

from .message import BuildMessageType, MessageSegmentT, MessageT

if TYPE_CHECKING:
    from typing import Any

    from .adapter import Adapter
    from .bot import Bot
    from .config import ConfigModel
    from .event import Event
    from .plugin import Plugin

__all__ = [
    "StateT",
    "EventT",
    "PluginT",
    "AdapterT",
    "ConfigT",
    "MessageT",
    "MessageSegmentT",
    "BuildMessageType",
    "BotHook",
    "AdapterHook",
    "EventHook",
]

StateT = TypeVar("StateT")
EventT = TypeVar("EventT", bound="Event[Any]")
PluginT = TypeVar("PluginT", bound="Plugin[Any, Any, Any]")
AdapterT = TypeVar("AdapterT", bound="Adapter[Any, Any]")
ConfigT = TypeVar("ConfigT", bound=Optional["ConfigModel"])

BotHook = Callable[["Bot"], Awaitable[None]]
AdapterHook = Callable[["Adapter[Any, Any]"], Awaitable[None]]
EventHook = Callable[["Event[Any]"], Awaitable[None]]
