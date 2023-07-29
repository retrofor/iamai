"""Console 适配器事件。"""
import inspect
from datetime import datetime
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    Literal,
    TypeVar,
    Optional,
)

from pydantic import BaseModel

from iamai.event import Event
from iamai.plugin import Plugin

from .message import Message, ConsoleMessage, MessageSegment

T_ConsoleEvent = TypeVar("T_ConsoleEvent", bound="ConsoleEvent")

if TYPE_CHECKING:
    from . import ConsoleAdapter  # type: ignore[class]

__all__ = ["ConsoleEvent", "MessageEvent", "User", "Robot"]


class User(BaseModel, frozen=True):
    """用户"""

    id: str
    avatar: str = "👤"
    nickname: str = "User"


class Robot(User, frozen=True):
    """机器人"""

    avatar: str = "🤖"
    nickname: str = "Bot"


class ConsoleEvent(Event["ConsoleAdapter"]):
    """Console 事件基类。"""

    __event__ = ""
    type = "console"

    def get_event_description(self) -> str:
        return str(self.dict())

    def get_message(self) -> Message:
        raise ValueError("Event has no message!")

    def get_user_id(self) -> str:
        raise ValueError("Event has no user_id!")

    def get_session_id(self) -> str:
        raise ValueError("Event has no session_id!")

    def is_tome(self) -> bool:
        """获取事件是否与机器人有关的方法。"""
        return True


class MessageEvent(ConsoleEvent):
    __event__ = "message"
    post_type: Literal["message"] = "message"
    message: str  # ConsoleMessage
    type: str = "message"

    def get_message(self) -> str:  # ConsoleMessage:
        return self.message

    def is_tome(self) -> bool:
        return True


# 事件类映射
_console_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, ConsoleEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_ConsoleEvent]:  # type: ignore
    """根据接收到的消息类型返回对应的事件类。

    Args:
        post_type: 请求类型。
        event_type: 事件类型。
        sub_type: 子类型。

    Returns:
        对应的事件类。
    """
    if sub_type is None:
        return _console_events[".".join((post_type, event_type))]  # type: ignore
    return (
        _console_events.get(".".join((post_type, event_type, sub_type)))
        or _console_events[".".join((post_type, event_type))]
    )  # type: ignore
