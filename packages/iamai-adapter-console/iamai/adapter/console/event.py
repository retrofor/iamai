"""Console 适配器事件。"""

from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from pydantic import BaseModel

from iamai.event import Event

from .message import Message

T_ConsoleEvent = TypeVar("T_ConsoleEvent", bound="ConsoleEvent")

if TYPE_CHECKING:
    pass  # type: ignore[class]

__all__ = ["ConsoleEvent", "MessageEvent", "User", "Robot"]  # noqa: F822


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

    message: str

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
