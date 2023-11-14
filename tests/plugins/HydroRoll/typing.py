"""HydroRoll 类型提示支持。

此模块定义了部分 HydroRoll 使用的类型。
"""

from typing import TYPE_CHECKING, TypeVar, Callable, NoReturn, Awaitable

from iamai.message import T_MS, T_Message, T_MessageSegment

if TYPE_CHECKING:
    from iamai.bot import Bot  # noqa
    from iamai.event import Event  # noqa
    from iamai.plugin import Plugin  # noqa
    from iamai.config import ConfigModel  # noqa

__all__ = [
    "T_State",
    "T_Event",
    "T_Plugin",
    "T_Config",
    "T_Message",
    "T_MessageSegment",
    "T_MS",
    "T_BotHook",
    "T_EventHook",
]

T_State = TypeVar("T_State")
T_Event = TypeVar("T_Event", bound="Event")
T_Plugin = TypeVar("T_Plugin", bound="Plugin")
T_Config = TypeVar("T_Config", bound="ConfigModel")

T_BotHook = Callable[["Bot"], Awaitable[NoReturn]]
T_EventHook = Callable[[T_Event], Awaitable[NoReturn]]
