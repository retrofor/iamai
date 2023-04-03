"""CQGuild 适配器事件。"""
import inspect
from typing import TYPE_CHECKING, Any, Dict, Type, Literal, TypeVar, Optional

from pydantic import Field, BaseModel

from iamai.event import Event

from .message import CQGuildMessage

if TYPE_CHECKING:
    from .message import T_CQMSG
    from . import CQGuildAdapter

T_CQGuildEvent = TypeVar("T_CQGuildEvent", bound="CQGuildEvent")


class Sender(BaseModel):
    user_id: Optional[int]
    nickname: Optional[str]
    card: Optional[str]
    sex: Optional[Literal["male", "female", "unknown"]]
    age: Optional[int]
    area: Optional[str]
    level: Optional[str]
    role: Optional[str]
    title: Optional[str]


class CQGuildEvent(Event["CQGuildAdapter"]):
    """CQGuild 事件基类"""

    __event__ = ""
    type: Optional[str] = Field(alias="post_type")
    tiny_id: int
    guild_id: str
    channel_id: str
    post_type: Literal["message", "notice", "meta_event"]

    @property
    def to_me(self) -> bool:
        """当前事件的 tiny_id 是否等于 self_id。"""
        return getattr(self, "tiny_id") == self.self_id


class MessageEvent(CQGuildEvent):
    """收到频道消息"""

    __event__ = "message"
    post_type: Literal["message"]
    message_type: Literal["guild"]
    sub_type: Literal["channel"]
    guild_id: str
    channel_id: str
    user_id: str
    message_id: str
    sender: Sender
    message: CQGuildMessage

    def __repr__(self) -> str:
        return f'Event<{self.type}>: "{self.message}"'

    def get_plain_text(self) -> str:
        """获取消息的纯文本内容。

        Returns:
            消息的纯文本内容。
        """
        return self.message.get_plain_text()

    async def reply(self, msg: "T_CQMSG") -> Dict[str, Any]:
        """回复消息。

        Args:
            msg: 回复消息的内容，同 `call_api()` 方法。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError


class NoticeEvent(CQGuildEvent):
    """通知事件"""

    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str


class ReactionInfo(BaseModel):
    """当前消息被贴表情列表"""

    emoji_id: str
    emoji_index: int
    emoji_type: int
    emoji_name: str
    count: int
    clicked: bool


class CQGuildMessageReactionUpdate(NoticeEvent):
    """频道消息表情贴更新"""

    __event__ = "notice.message_reactions_updated"
    notice_type: Literal["message_reactions_updated"]
    guild_id: str
    channel_id: str
    user_id: str
    message_id: str
    current_reactions: ReactionInfo


class CQGuildChannelUpdate(NoticeEvent):
    """子频道信息更新"""

    __event__ = "notice.channel_updated"
    notice_type: Literal["channel_updated"]
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    old_info: CQGuildEvent
    new_info: CQGuildEvent


class CQGuildChannelCreated(NoticeEvent):
    """子频道创建"""

    __event__ = "notice.channel_created"
    notice_type: Literal['channel_created']
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    channel_info: CQGuildEvent


class CQGuildChannelDestoryed(NoticeEvent):
    """子频道删除"""

    __event__ = 'notice.channel_destoryed'
    notice_type: Literal['channel_destoryed']
    guild_id: str
    channel_id: str
    user_id: str
    operator_id: str
    channel_info: CQGuildEvent


class MetaEvent(CQGuildEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str


class LifecycleMetaEvent(MetaEvent):
    """生命周期"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: Literal["enable", "disable", "connect"]


class Status(BaseModel):
    online: bool
    good: bool

    class Config:
        extra = "allow"


class HeartbeatMetaEvent(MetaEvent):
    """心跳包"""

    __event__ = "meta_event.heartbeat"
    meta_event_type: Literal["heartbeat"]
    status: Status
    interval: int


_CQGuild_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, CQGuildEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_CQGuildEvent]:
    """根据接收到的消息类型返回对应的事件类。

    Args:
        post_type: 请求类型。
        event_type: 事件类型。
        sub_type: 子类型。

    Returns:
        对应的事件类。
    """
    if sub_type is None:
        return _CQGuild_events[".".join((post_type, event_type))]
    return (
        _CQGuild_events.get(".".join((post_type, event_type, sub_type)))
        or _CQGuild_events[".".join((post_type, event_type))]
    )
