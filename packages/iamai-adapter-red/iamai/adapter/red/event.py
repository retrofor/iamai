"""Red 适配器事件。"""
import inspect
from enum import IntEnum
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, Type, Union, Literal, TypeVar, Optional

from pydantic import Field, BaseModel

from iamai.event import Event

from .message import T_RedMSG, RedMessage

if TYPE_CHECKING:
    from . import RedAdapter
    from .message import T_RedMSG

T_RedEvent = TypeVar("T_RedEvent", bound="RedEvent")


class RedEvent(Event["RedAdapter"]):
    """Red 事件基类"""

    __event__ = ""
    # type = Optional[str] = Field(alias="post_type")
    post_type: Literal["message", "notice", "request", "meta_event"]


class EmojiAd(BaseModel):
    url: str
    desc: str


class EmojiMall(BaseModel):
    packageId: int
    emojiId: int


class EmojiZplan(BaseModel):
    actionId: int
    actionName: str
    actionType: int
    playerNumber: int
    peerUid: str
    bytesReserveInfo: str


class ThumbPath(BaseModel):
    ...


class TextElement(BaseModel):
    content: str
    atType: Literal[0, 1, 2]
    atUid: str
    atTinyId: str
    atNtUid: str
    subElementType: int
    atChannelId: str
    atRoleId: str
    atRoleColor: int
    atRoleName: str
    needNotify: int


class RoleInfo(BaseModel):
    roleId: str
    name: str
    color: int


class XMLElement(BaseModel):
    busiType: str
    busiId: str
    c2cType: int
    serviceType: int
    ctrlFlag: int
    content: str
    templId: str
    seqId: str
    templParam: Any
    pbReserv: str
    members: Any


class PicElement(BaseModel):
    picSubType: int
    fileName: str
    fileSize: str
    picWidth: int
    picHeight: int
    original: bool
    md5HexStr: str
    sourcePath: str
    thumbPath: ThumbPath
    transferStatus: int
    progress: int
    picType: int
    invalidState: int
    fileUuid: str
    fileSubId: str
    thumbFileSize: int
    summary: str
    emojiAd: EmojiAd
    emojiMall: EmojiMall
    emojiZplan: EmojiZplan


class Element(BaseModel):
    elementType: int
    elementId: str
    extBufForUI: str
    picElement: Optional[PicElement]
    textElement: Optional[TextElement]
    arkElement: Optional[Any]
    avRecordElement: Optional[Any]
    calendarElement: Optional[Any]
    faceElement: Optional[Any]
    fileElement: Optional[Any]
    giphyElement: Optional[Any]

    class grayTipElement:
        xmlElement: XMLElement
        aioOpGrayTipElement: Optional[Any]
        blockGrayTipElement: Optional[Any]
        buddyElement: Optional[Any]
        buddyNotifyElement: Optional[Any]
        emojiReplyElement: Optional[Any]
        essenceElement: Optional[Any]
        feedMsgElement: Optional[Any]
        fileReceiptElement: Optional[Any]
        groupElement: Optional[Any]
        groupNotifyElement: Optional[Any]
        jsonGrayTipElement: Optional[Any]
        localGrayTipElement: Optional[Any]
        proclamationElement: Optional[Any]
        revokeElement: Optional[Any]
        subElementType: Optional[Any]

    inlineKeyboardElement: Optional[Any]
    liveGiftElement: Optional[Any]
    markdownElement: Optional[Any]
    marketFaceElement: Optional[Any]
    multiForwardMsgElement: Optional[Any]
    pttElement: Optional[Any]
    replyElement: Optional[Any]
    structLongMsgElement: Optional[Any]
    textGiftElement: Optional[Any]
    videoElement: Optional[Any]
    walletElement: Optional[Any]
    yoloGameResultElement: Optional[Any]


class ChatType(IntEnum):
    FRIEND = 1
    GROUP = 2


class OtherAdd(BaseModel):
    uid: Optional[str]
    name: Optional[str]
    uin: Optional[str]


class MemberAdd(BaseModel):
    showType: int
    otherAdd: Optional[OtherAdd]
    otherAddByOtherQRCode: Optional[Any]
    otherAddByYourQRCode: Optional[Any]
    youAddByOtherQRCode: Optional[Any]
    otherInviteOther: Optional[Any]
    otherInviteYou: Optional[Any]
    youInviteOther: Optional[Any]


class ShutUpTarget(BaseModel):
    uid: Optional[str]
    card: str
    name: str
    role: int
    uin: str


class ShutUp(BaseModel):
    curTime: int
    duration: int
    admin: ShutUpTarget
    member: ShutUpTarget


class GroupElement(BaseModel):
    type: int
    role: int
    groupName: Optional[str]
    memberUid: Optional[str]
    memberNick: Optional[str]
    memberRemark: Optional[str]
    adminUid: Optional[str]
    adminNick: Optional[str]
    adminRemark: Optional[str]
    createGroup: Optional[Any]
    memberAdd: Optional[MemberAdd]
    shutUp: Optional[ShutUp]
    memberUin: Optional[str]
    adminUin: Optional[str]


class XmlElement(BaseModel):
    busiType: Optional[str]
    busiId: Optional[str]
    c2cType: int
    serviceType: int
    ctrlFlag: int
    content: Optional[str]
    templId: Optional[str]
    seqId: Optional[str]
    templParam: Optional[Any]
    pbReserv: Optional[str]
    members: Optional[Any]


class Member(BaseModel):
    uid: str
    qid: str
    uin: str
    nick: str
    remark: str
    cardType: int
    cardName: str
    role: int
    avatarPath: str
    shutUpTime: int
    isDelete: bool


class Group(BaseModel):
    groupCode: str
    maxMember: int
    memberCount: int
    groupName: str
    groupStatus: int
    memberRole: int
    isTop: bool
    toppedTimestamp: str
    privilegeFlag: int
    isConf: bool
    hasModifyConfGroupFace: bool
    hasModifyConfGroupName: bool
    remarkName: str
    avatarUrl: str
    hasMemo: bool
    groupShutupExpireTime: str
    personShutupExpireTime: str
    discussToGroupUin: str
    discussToGroupMaxMsgSeq: int
    discussToGroupTime: int


class ImageInfo(BaseModel):
    width: int
    height: int
    type: Optional[str]
    mime: Optional[str]
    wUnits: Optional[str]
    hUnits: Optional[str]


class UploadResponse(BaseModel):
    md5: str
    imageInfo: Optional[ImageInfo]
    fileSize: int
    filePath: str
    ntFilePath: str


class MsgType(IntEnum):
    normal = 2
    may_file = 3
    system = 5
    voice = 6
    video = 7
    value8 = 8
    reply = 9
    wallet = 10
    ark = 11
    may_market = 17


class MessageEvent(RedEvent):
    """消息事件"""

    __event__ = "message"
    post_type: Literal["message"]
    message_type: Literal["private", "group"]
    sub_type: Union[Literal["channel"], str]
    message: RedMessage
    original_message: RedMessage

    def __repr__(self) -> str:
        return f'Event<{self.type}>: "{self.message}"'

    async def reply(self, msg: "T_RedMSG") -> Dict[str, Any]:
        """回复消息"""

        raise NotImplementedError


class PrivateMessageEvent(MessageEvent):
    """私聊消息事件"""

    __event__ = "message.private"
    message_type: Literal["private"]
    sub_type: Literal["friend", "group", "group_self", "other"]
    roleType: int

    async def reply(self, msg: T_RedMSG) -> Dict[str, Any]:
        return await self.adapter.send_message(
            chatType=1, peerUin=self.peerUid, elements=RedMessage(msg)
        )


class GroupMessageEvent(MessageEvent):
    """群消息事件"""

    __event__ = "message.group"
    message_type: Literal["group"]
    sub_type: Literal["normal", "anonymous", "notice"]
    roleType: int

    async def reply(self, msg: T_RedMSG) -> Dict[str, Any]:
        return await self.adapter.send_message(
            chatType=2, peerUin=self.peerUid, elements=RedMessage(msg)
        )


class NoticeEvent(RedEvent):
    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str
    msgId: str
    msgRandom: str
    msgSeq: str
    cntSeq: str
    chatType: ChatType
    msgType: MsgType
    subMsgType: int
    peerUid: str
    peerUin: Optional[str]

    # class Config:
    #     extra = "ignore"


class GroupNameUpdateEvent(NoticeEvent):
    """群名变更事件"""

    __event__ = "notice.group_name_update"
    notice_type: Literal["group_name_update"]
    currentName: str
    operatorUid: str
    operatorName: str


class MemberAddEvent(NoticeEvent):
    """群成员增加事件"""

    __event__ = "notice.member_add"
    notice_type: Literal["member_add"]
    memberUid: str
    operatorUid: str
    memberName: Optional[str]


class MemberMuteEvent(NoticeEvent):
    """群成员禁言相关事件"""

    __event__ = "notice.member_mute"
    notice_type: Literal["member_mute"]
    start: datetime
    duration: timedelta
    operator: ShutUpTarget
    member: ShutUpTarget


class MemberUnmuteEvent(NoticeEvent):
    """群成员被解除禁言事件"""

    __event__ = "notice.member_unmute"
    notice_type: Literal["member_unmute"]
    start: datetime
    duration: timedelta
    operator: ShutUpTarget
    member: ShutUpTarget


class MetaEvent(RedEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str


class LifecycleMetaEvent(MetaEvent):
    """生命周期"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: Literal["enable", "disable", "connect"]


_red_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, RedEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_RedEvent]:
    """根据接收到的消息类型返回对应的事件类。

    Args:
        post_type: 请求类型。
        event_type: 事件类型。
        sub_type: 子类型。

    Returns:
        对应的事件类。
    """
    if sub_type is None:
        return _red_events[".".join((post_type, event_type))]
    return (
        _red_events.get(".".join((post_type, event_type, sub_type)))
        or _red_events[".".join((post_type, event_type))]
    )
