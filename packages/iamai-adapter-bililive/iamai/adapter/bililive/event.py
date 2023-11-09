"""Bililive 适配器事件。"""
import asyncio
import inspect
from enum import IntEnum
from email import message
from collections import UserDict
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

from isort import literal
from pydantic import Field, HttpUrl, BaseModel, validator, root_validator

from iamai.event import Event

from .message import Message, BililiveMessage

if TYPE_CHECKING:
    from . import BililiveAdapter
    from .message import T_BililiveMSG

T_BililiveEvent = TypeVar("T_BililiveEvent", bound="BililiveEvent")


# go-common\app\service\main\broadcast\model\operation.go
class Operation(IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    SEND_MSG_REPLY = 5
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9
    PROTO_READY = 10
    PROTO_FINISH = 11
    CHANGE_ROOM = 12
    CHANGE_ROOM_REPLY = 13
    REGISTER = 14
    REGISTER_REPLY = 15
    UNREGISTER = 16
    UNREGISTER_REPLY = 17
    # B站业务自定义OP
    # MinBusinessOp = 1000
    # MaxBusinessOp = 10000


class DanmakuPosition(IntEnum):
    TOP = (5,)
    BOTTOM = (4,)
    NORMAL = 1


class BililiveEvent(Event["BililiveAdapter"]):
    """Blilive 适配器事件类。"""

    __event__ = ""
    cmd: str


class MessageEvent(BililiveEvent):
    """消息事件"""

    __event__ = "message"
    post_type: Literal["message"] = "message"
    sub_type: str
    message: BililiveMessage
    session_id: str

    def __repr__(self) -> str:
        return f'Event<{self.type}>: "{self.message}"'

    def get_plain_text(self) -> str:
        return self.message.get_plain_text()

    async def reply(self, msg: "T_BililiveMSG") -> Dict[str, Any]:
        raise NotImplementedError


class Danmu_msg(MessageEvent):
    """弹幕"""

    __event__ = "message.danmu_msg"
    message_type: Literal["danmu_msg"]
    info: List[Any]

    async def reply(self, msg: "T_BililiveMSG") -> Dict[str, Any]:
        return await self.adapter.send(danmaku=msg)


class Super_chat_message(MessageEvent):
    """醒目留言"""

    __event__ = "message.super_chat_message"
    message_type: Literal["super_chat_message"]
    data: Dict[str, Any]
    duration: int


class NoticeEvent(Event):
    __event__ = "notice"


class Combo_send(NoticeEvent):
    """连击礼物"""

    __event__ = "notice.combo_send"
    data: Dict[Any, Any]
    notice_type: Literal["combo_send"]


class Send_gift(NoticeEvent):
    """投喂礼物"""

    __event__ = "notice.send_gift"
    data: Dict[Any, Any]
    notice_type: Literal["send_gift"]


class Common_notice_danmaku(NoticeEvent):
    """限时任务(系统通知的)"""

    __event__ = "notice.common_notice_danmaku"
    data: Dict[Any, Any]
    notice_type: Literal["common_notice_danmaku"]


class Entry_effect(NoticeEvent):
    """舰长进房"""

    __event__ = "notice.entry_effect"
    data: Dict[Any, Any]
    notice_type: Literal["entry_effect"]


class Interact_word(NoticeEvent):
    """普通进房消息"""

    __event__ = "notice_interact_word"
    data: Dict[Any, Any]
    notice_type: Literal["notice_interact_word"]


class Guard_buy(NoticeEvent):
    """上舰"""

    __event__ = "notice.guard_buy"
    data: Dict[Any, Any]
    notice_type: Literal["guard_buy"]


class User_toast_msg(NoticeEvent):
    """续费舰长"""

    __event__ = "notice.user_toast_msg"
    data: Dict[Any, Any]
    notice_type: Literal["user_toast_msg"]


class Notice_msg(NoticeEvent):
    """在本房间续费了舰长"""

    __event__ = "notice.notice_msg"
    id: int
    name: str
    full: Dict[str, Any]
    half: Dict[str, Any]
    side: Dict[str, Any]
    scatter: Dict[str, int]
    roomid: int
    real_roomid: int
    msg_common: int
    msg_self: str
    link_url: str
    msg_type: int
    shield_uid: int
    business_id: str
    marquee_id: str
    notice_type: Union[Literal["notice_msg"], int]


class Like_info_v3_click(NoticeEvent):
    """点赞"""

    __event__ = "notice.like_info_v3_click"
    data: Dict[Any, Any]
    notice_type: Literal["like_info_v3_click"]


class Like_info_v3_update(NoticeEvent):
    """总点赞数"""

    __event__ = "notice.like_info_v3_update"
    data: Dict[Any, Any]
    notice_type: Literal["like_info_v3_update"]


class Online_rank_count(NoticeEvent):
    """在线等级统计"""

    __event__ = "notice.online_rank_count"
    data: Dict[Any, Any]
    notice_type: Literal["online_rank_count"]


class Online_rank_v2(NoticeEvent):
    """在线等级榜"""

    __event__ = "notice.online_rank_v2"
    data: Dict[Any, Any]
    notice_type: Literal["online_rank_v2"]


class Popular_rank_changed(NoticeEvent):
    __event__ = "notice.popular_rank_changed"
    data: Dict[Any, Any]
    notice_type: Literal["popular_rank_changed"]


class Room_change(NoticeEvent):
    """房间信息变动(分区、标题等)"""

    __event__ = "notice.room_change"
    data: Dict[Any, Any]
    notice_type: Literal["room_change"]


class Room_real_time_message_update(NoticeEvent):
    """房间数据"""

    __event__ = "notice.room_real_time_message_update"
    data: Dict[Any, Any]
    notice_type: Literal["room_real_time_message_update"]


class Watched_change(NoticeEvent):
    """直播间观看人数"""

    __event__ = "notice.watched_change"
    data: Dict[Any, Any]
    notice_type: Literal["watched_change"]


class Stop_live_room_list(NoticeEvent):
    """下播列表"""

    __event__ = "notice.stop_live_room_list"
    data: Dict[Any, Any]
    room_id_list: List[int]
    notice_type: Literal["stop_live_room_list"]


class Anchor_lot_start(NoticeEvent):
    """天选之人开始"""

    __event__ = "notice.anchor_lot_start"
    data: Dict[Any, Any]
    notice_type: Literal["anchor_lot_start"]

    def get_anchor_lot_info(self):
        """获取天选之人的相关信息"""
        return {
            "award_name": self.data["award_name"],
            "danmu": self.data["danmu"],
            "gift_name": self.data["gift_name"],
        }


class Anchor_lot_award(NoticeEvent):
    """天选之人结果"""

    __event__ = "notice.anchor_lot_award"
    data: Dict[Any, Any]
    notice_type: Literal["anchor_lot_award"]

    def winner_info(self):
        """获取中奖人信息"""
        return self.data["award_users"]


# 事件类映射
_bililive_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, BililiveEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_BililiveEvent]:  # type: ignore
    if sub_type is None:
        return _bililive_events[".".join((post_type, event_type))]  # type: ignore
    return (
        _bililive_events.get(".".join((post_type, event_type, sub_type)))
        or _bililive_events[".".join((post_type, event_type))]
    )  # type: ignore
