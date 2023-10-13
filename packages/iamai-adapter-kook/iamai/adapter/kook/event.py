"""Kook 适配器事件。"""
import asyncio
import inspect
from enum import IntEnum
from collections import UserDict
from typing import (  # type: ignore
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

from pydantic import Field, HttpUrl, BaseModel, validator, root_validator

from iamai.event import Event

from .api import Role, User, Emoji, Guild, Channel
from .message import KookMessage, MessageDeserializer

if TYPE_CHECKING:
    from . import KookAdapter
    from .message import T_KookMSG

T_KookEvent = TypeVar("T_KookEvent", bound="KookEvent")


class ResultStore:
    _seq = 1
    _futures: Dict[Tuple[str, int], asyncio.Future] = {}
    _sn_map = {}

    @classmethod
    def set_sn(cls, self_id: str, sn: int) -> None:
        cls._sn_map[self_id] = sn

    @classmethod
    def get_sn(cls, self_id: str) -> int:
        return cls._sn_map.get(self_id, 0)


class AttrDict(UserDict):
    def __init__(self, data=None):
        initial = dict(data)  # type: ignore
        for k in initial:
            if isinstance(initial[k], dict):
                initial[k] = AttrDict(initial[k])  # type: ignore

        super().__init__(initial)

    def __getattr__(self, name):
        return self[name]


class PermissionOverwrite(BaseModel):
    role_id: Optional[int] = None
    allow: Optional[int] = None
    deny: Optional[int] = None


class PermissionUser(BaseModel):
    user: Optional[User] = None
    allow: Optional[int] = None
    deny: Optional[int] = None


class ChannelRoleInfo(BaseModel):
    """频道角色权限详情"""

    permission_overwrites: Optional[List[PermissionOverwrite]] = None
    """针对角色在该频道的权限覆写规则组成的列表"""
    permission_users: Optional[List[PermissionUser]] = None
    """针对用户在该频道的权限覆写规则组成的列表"""
    permission_sync: Optional[int] = None
    """权限设置是否与分组同步, 1 or 0"""


class Quote(BaseModel):
    """引用消息"""

    id_: Optional[str] = Field(None, alias="id")
    """引用消息 id"""
    type: Optional[int] = None
    """引用消息类型"""
    content: Optional[str] = None
    """引用消息内容"""
    create_at: Optional[int] = None
    """引用消息创建时间（毫秒）"""
    author: Optional[User] = None
    """作者的用户信息"""


class Attachments(BaseModel):
    """附加的多媒体数据"""

    type: Optional[str] = None
    """多媒体类型"""
    url: Optional[str] = None
    """多媒体地址"""
    name: Optional[str] = None
    """多媒体名"""
    size: Optional[int] = None
    """大小 单位（B）"""


class URL(BaseModel):
    url: Optional[str] = None
    """资源的 url"""


class Meta(BaseModel):
    page: Optional[int] = None
    page_total: Optional[int] = None
    page_size: Optional[int] = None
    total: Optional[int] = None


class ListReturn(BaseModel):
    meta: Optional[Meta] = None
    sort: Optional[Dict[str, Any]] = None


class BlackList(BaseModel):
    """黑名单"""

    user_id: Optional[str] = None
    """用户 id"""
    created_time: Optional[int] = None
    """加入黑名单的时间戳(毫秒)"""
    remark: Optional[str] = None
    """加入黑名单的原因"""
    user: Optional[User] = None
    """用户"""


class BlackListsReturn(ListReturn):
    """获取黑名单列表返回信息"""

    blacklists: Optional[List[BlackList]] = Field(None, alias="items")
    """黑名单列表"""


class MessageCreateReturn(BaseModel):
    """发送频道消息返回信息"""

    msg_id: Optional[str] = None
    """服务端生成的消息 id"""
    msg_timestamp: Optional[int] = None
    """消息发送时间(服务器时间戳)"""
    nonce: Optional[str] = None
    """随机字符串"""


class ChannelRoleReturn(BaseModel):
    """创建或更新频道角色权限返回信息"""

    role_id: Optional[int] = None
    user_id: Optional[str] = None
    allow: Optional[int] = None
    deny: Optional[int] = None


class GuildsReturn(ListReturn):
    guilds: Optional[List[Guild]] = Field(None, alias="items")


class ChannelsReturn(ListReturn):
    channels: Optional[List[Channel]] = Field(None, alias="items")


class GuildUsersRetrun(ListReturn):
    """服务器中的用户列表"""

    users: Optional[List[User]] = Field(None, alias="items")
    """用户列表"""
    user_count: Optional[int] = None
    """用户数量"""
    online_count: Optional[int] = None
    """在线用户数量"""
    offline_count: Optional[int] = None
    """离线用户数量"""


class Reaction(BaseModel):
    emoji: Optional[Emoji] = None
    count: Optional[int] = None
    me: Optional[bool] = None


class MentionInfo(BaseModel):
    mention_part: Optional[List[dict]] = None
    mention_role_part: Optional[List[dict]] = None
    channel_part: Optional[List[dict]] = None
    item_part: Optional[List[dict]] = None


class BaseMessage(BaseModel):
    id_: Optional[str] = Field(None, alias="id")
    """消息 ID"""
    type: Optional[int] = None
    """消息类型"""
    content: Optional[str] = None
    """消息内容"""
    embeds: Optional[List[dict]] = None
    """超链接解析数据"""
    attachments: Optional[Union[bool, Attachments]] = None
    """附加的多媒体数据"""
    create_at: Optional[int] = None
    """创建时间"""
    updated_at: Optional[int] = None
    """更新时间"""
    reactions: Optional[List[Reaction]] = None
    """回应数据"""
    image_name: Optional[str] = None
    """"""
    read_status: Optional[bool] = None
    """是否已读"""
    quote: Optional[Quote] = None
    """引用数据"""
    mention_info: Optional[MentionInfo] = None
    """引用特定用户或特定角色的信息"""


class ChannelMessage(BaseMessage):
    """频道消息"""

    author: Optional[User] = None
    mention: Optional[List[Any]] = None
    mention_all: Optional[bool] = None
    mention_roles: Optional[List[Any]] = None
    mention_here: Optional[bool] = None


class DirectMessage(BaseMessage):
    """私聊消息"""

    author_id: Optional[str] = None
    """作者的用户 ID"""
    from_type: Optional[int] = None
    """from_type"""
    msg_icon: Optional[str] = None
    """msg_icon"""


class ChannelMessagesReturn(BaseModel):
    """获取私信聊天消息列表返回信息"""

    direct_messages: Optional[List[ChannelMessage]] = Field(None, alias="items")


class DirectMessagesReturn(BaseModel):
    """获取私信聊天消息列表返回信息"""

    direct_messages: Optional[List[DirectMessage]] = Field(None, alias="items")


class ReactionUser(User):
    reaction_time: Optional[int] = None


class TargetInfo(BaseModel):
    """私聊会话 目标用户信息"""

    id_: Optional[str] = Field(None, alias="id")
    """目标用户 ID"""
    username: Optional[str] = None
    """目标用户名"""
    online: Optional[bool] = None
    """是否在线"""
    avatar: Optional[str] = None
    """头像图片链接"""


class UserChat(BaseModel):
    """私聊会话"""

    code: Optional[str] = None
    """私信会话 Code"""
    last_read_time: Optional[int] = None
    """上次阅读消息的时间 (毫秒)"""
    latest_msg_time: Optional[int] = None
    """最新消息时间 (毫秒)"""
    unread_count: Optional[int] = None
    """未读消息数"""
    target_info: Optional[TargetInfo] = None
    """目标用户信息"""


class UserChatsReturn(ListReturn):
    """获取私信聊天会话列表返回信息"""

    user_chats: Optional[List[UserChat]] = Field(None, alias="items")
    """私聊会话列表"""


class RolesReturn(ListReturn):
    """获取服务器角色列表返回信息"""

    roles: Optional[List[Role]] = Field(None, alias="items")
    """服务器角色列表"""


class GuilRoleReturn(BaseModel):
    """赋予或删除用户角色返回信息"""

    user_id: Optional[str] = None
    """用户 id"""
    guild_id: Optional[str] = None
    """服务器 id"""
    roles: Optional[List[int]] = None
    """角色 id 的列表"""


class IntimacyImg(BaseModel):
    """形象图片的总列表"""

    id_: Optional[str] = Field(None, alias="id")
    """	形象图片的 id"""
    url: Optional[str] = None
    """形象图片的地址"""


class IntimacyIndexReturn(BaseModel):
    """获取用户亲密度返回信息"""

    img_url: Optional[str] = None
    """机器人给用户显示的形象图片地址"""
    social_info: Optional[str] = None
    """机器人显示给用户的社交信息"""
    last_read: Optional[int] = None
    """用户上次查看的时间戳"""
    score: Optional[int] = None
    """亲密度，0-2200"""
    img_list: Optional[List[IntimacyImg]] = None
    """形象图片的总列表"""


class GuildEmoji(BaseModel):
    """服务器表情"""

    name: Optional[str] = None
    """表情的名称"""
    id_: Optional[str] = Field(None, alias="id")
    """表情的 ID"""
    user_info: Optional[User] = None
    """上传用户"""


class GuildEmojisReturn(ListReturn):
    """获取服务器表情列表返回信息"""

    roles: Optional[List[GuildEmoji]] = Field(None, alias="items")
    """服务器表情列表"""


class Invite(BaseModel):
    """邀请信息"""

    guild_id: Optional[str] = None
    """服务器 id"""
    channel_id: Optional[str] = None
    """频道 id"""
    url_code: Optional[str] = None
    """url code"""
    url: Optional[str] = None
    """地址"""
    user: Optional[User] = None
    """用户"""


class InvitesReturn(ListReturn):
    """获取邀请列表返回信息"""

    roles: Optional[List[Invite]] = Field(None, alias="items")
    """邀请列表"""


class EventTypes(IntEnum):
    """
    事件主要格式
    Kook 协议事件，字段与 Kook 一致。各事件字段参考 `Kook 文档`

    .. Kook 文档:
        https://developer.kookapp.cn/doc/event/event-introduction#事件主要格式
    """

    text = 1
    image = 2
    video = 3
    file = 4
    audio = 8
    kmarkdown = 9
    card = 10
    sys = 255


class SignalTypes(IntEnum):
    """
    信令类型
    Kook 协议信令，字段与 Kook 一致。各事件字段参考 `Kook 文档`

    .. Kook 文档:
        https://developer.kookapp.cn/doc/websocket#信令格式
    """

    EVENT = 0
    HELLO = 1
    PING = 2
    PONG = 3
    RESUME = 4
    RECONNECT = 5
    RESUME_ACK = 6
    SYS = 255


class Attachment(BaseModel):
    type: str
    name: str
    url: HttpUrl
    file_type: Optional[str] = Field(None)
    size: Optional[int] = Field(None)
    duration: Optional[float] = Field(None)
    width: Optional[int] = Field(None)
    hight: Optional[int] = Field(None)


class Extra(BaseModel):
    type_: Union[int, str] = Field(None, alias="type")
    guild_id: Optional[str] = Field(None)
    channel_name: Optional[str] = Field(None)
    mention: Optional[List[str]] = Field(None)
    mention_all: Optional[bool] = Field(None)
    mention_roles: Optional[List[str]] = Field(None)
    mention_here: Optional[bool] = Field(None)
    author: Optional[User] = Field(None)
    body: Optional[AttrDict] = Field(None)
    attachments: Optional[Attachment] = Field(None)
    code: Optional[str] = Field(None)

    @validator("body", pre=True)
    def convert_body(cls, v):
        if v is None:
            return None

        if not isinstance(v, dict):
            raise TypeError("body must be dict")
        if not isinstance(v, AttrDict):
            v = AttrDict(v)
        return v

    class Config:
        arbitrary_types_allowed = True


class OriginEvent(Event["KookAdapter"]):
    """为了区分信令中非Event事件，增加了前置OriginEvent"""

    __event__ = ""

    post_type: str


class Kmarkdown(BaseModel):
    raw_content: str
    mention_part: list
    mention_role_part: list


class EventMessage(BaseModel):
    type: Union[int, str]
    guild_id: Optional[str]
    channel_name: Optional[str]
    mention: Optional[List]
    mention_all: Optional[bool]
    mention_roles: Optional[List]
    mention_here: Optional[bool]
    nav_channels: Optional[List]
    author: User

    kmarkdown: Optional[Kmarkdown]

    code: Optional[str] = None
    attachments: Optional[Attachment] = None

    content: KookMessage


class KookEvent(OriginEvent):
    """
    事件主要格式，来自 d 字段
    Kook 协议事件，字段与 Kook 一致。各事件字段参考 `Kook 文档`

    .. Kook 文档:
        https://developer.kookapp.cn/doc/event/event-introduction
    """

    __event__ = ""
    channel_type: Literal["PERSON", "GROUP"]
    type_: int = Field(alias="type")
    """1:文字消息\n2:图片消息\n3:视频消息\n4:文件消息\n8:音频消息\n9:KMarkdown\n10:card消息\n255:系统消息\n其它的暂未开放"""
    target_id: str
    """
    发送目的\n
    频道消息类时, 代表的是频道 channel_id\n
    如果 channel_type 为 GROUP 组播且 type 为 255 系统消息时，则代表服务器 guild_id"""
    author_id: Optional[str] = None
    content: KookMessage
    msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Extra
    user_id: str

    post_type: str
    self_id: Optional[str] = None  # onebot兼容


# Message Events
class MessageEvent(KookEvent):
    """消息事件"""

    __event__ = "message"

    post_type: Literal["message"] = "message"
    message_type: str  # group private 其实是person
    sub_type: str
    event: EventMessage

    def __repr__(self) -> str:
        return f'Event<{self.post_type}>: "{self.content}"'

    def get_plain_text(self) -> str:
        """获取消息的纯文本内容。

        Returns:
            消息的纯文本内容。
        """
        return self.content.get_plain_text()  # type: ignore

    async def reply(self, msg: "T_KookMSG") -> Dict[str, Any]:
        """回复消息。

        Args:
            msg: 回复消息的内容，同 `call_api()` 方法。

        Returns:
            API 请求响应。
        """
        raise NotImplementedError


class PrivateMessageEvent(MessageEvent):
    """私聊消息"""

    __event__ = "message.private"
    message_type: Literal["private"]

    async def reply(self, msg: "T_KookMSG") -> Dict[str, Any]:
        return await self.adapter.call_api(
            api="direct-message/create", target_id=self.author_id, content=msg
        )


class ChannelMessageEvent(MessageEvent):
    """公共频道消息"""

    __event__ = "message.group"
    message_type: Literal["group"]
    group_id: str

    async def reply(self, msg: "T_KookMSG") -> Dict[str, Any]:
        return await self.adapter.call_api(
            "message/create", target_id=self.target_id, content=msg
        )


# Notice Events
class NoticeEvent(KookEvent):
    """通知事件"""

    __event__ = "notice"
    post_type: Literal["notice"]
    notice_type: str

    def __repr__(self) -> str:
        return f'Event<{self.post_type}>: "{self.content}"'


# Channel Events
class ChannelNoticeEvent(NoticeEvent):
    """频道消息事件"""

    __event__ = "notice"
    group_id: int


class ChannelAddReactionEvent(ChannelNoticeEvent):
    """频道内用户添加 reaction"""

    __event__ = "notice.added_reaction"
    notice_type: Literal["added_reaction"]


class ChannelDeletedReactionEvent(ChannelNoticeEvent):
    """频道内用户删除 reaction"""

    __event__ = "notice.deleted_reaction"
    notice_type: Literal["deleted_reaction"]


class ChannelUpdatedMessageEvent(ChannelNoticeEvent):
    """频道消息更新"""

    __event__ = "notice.updated_message"
    notice_type: Literal["updated_message"]


class ChannelDeleteMessageEvent(ChannelNoticeEvent):
    """频道消息被删除"""

    __event__ = "notice.deleted_message"
    notice_type: Literal["deleted_message"]


class ChannelAddedEvent(ChannelNoticeEvent):
    """新增频道"""

    __event__ = "notice.added_channel"
    notice_type: Literal["added_channel"]


class ChannelUpdatedEvent(ChannelNoticeEvent):
    """修改频道信息"""

    __event__ = "notice.updated_channel"
    notice_type: Literal["updated_channel"]


class ChannelDeleteEvent(ChannelNoticeEvent):
    """删除频道"""

    __event__ = "notice.deleted_channel"
    notice_type: Literal["deleted_channel"]


class ChannelPinnedMessageEvent(ChannelNoticeEvent):
    """新增频道置顶消息"""

    __event__ = "notice.pinned_message"
    notice_type: Literal["pinned_message"]


class ChannelUnpinnedMessageEvent(ChannelNoticeEvent):
    """取消频道置顶消息"""

    __event__ = "notice.unpinned_message"
    notice_type: Literal["unpinned_message"]


# Private Events
class PrivateNoticeEvent(NoticeEvent):
    "私聊消息事件"


class PrivateUpdateMessageEvent(PrivateNoticeEvent):
    """私聊消息更新"""

    __event__ = "notice.updated_private_message"
    notice_type: Literal["updated_private_message"]


class PrivateDeleteMessageEvent(PrivateNoticeEvent):
    """私聊消息删除"""

    __event__ = "notice.deleted_private_message"
    notice_type: Literal["deleted_private_message"]


class PrivateAddReactionEvent(PrivateNoticeEvent):
    """私聊内用户添加 reaction"""

    __event__ = "notice.private_added_reaction"
    notice_type: Literal["private_added_reaction"]


class PrivateDeleteReactionEvent(PrivateNoticeEvent):
    """私聊内用户取消 reaction"""

    __event__ = "notice.private_deleted_reaction"
    notice_type: Literal["private_deleted_reaction"]


# Guild Events
class GuildNoticeEvent(NoticeEvent):
    """服务器相关事件"""

    group_id: int

    def get_guild_id(self):
        return self.target_id  # type: ignore


# Guild Member Events
class GuildMemberNoticeEvent(GuildNoticeEvent):
    """服务器成员相关事件"""

    pass


class GuildMemberIncreaseNoticeEvent(GuildMemberNoticeEvent):
    """新成员加入服务器"""

    __event__ = "notice.joined_guild"
    notice_type: Literal["joined_guild"]


class GuildMemberDecreaseNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员退出"""

    __event__ = "notice.exited_guild"
    notice_type: Literal["exited_guild"]


class GuildMemberUpdateNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员信息更新(修改昵称)"""

    __event__ = "notice.updated_guild_member"
    notice_type: Literal["updated_guild_member"]


class GuildMemberOnlineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员上线"""

    __event__ = "notice.guild_member_online"
    notice_type: Literal["guild_member_online"]


class GuildMemberOfflineNoticeEvent(GuildMemberNoticeEvent):
    """服务器成员下线"""

    __event__ = "notice.guild_member_offline"
    notice_type: Literal["guild_member_offline"]


# Guild Role Events
class GuildRoleNoticeEvent(GuildNoticeEvent):
    """服务器角色相关事件"""


class GuildRoleAddNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.added_role"
    notice_type: Literal["added_role"]


class GuildRoleDeleteNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.deleted_role"
    notice_type: Literal["deleted_role"]


class GuildRoleUpdateNoticeEvent(GuildRoleNoticeEvent):
    """服务器角色增加"""

    __event__ = "notice.updated_role"
    notice_type: Literal["updated_role"]


# Guild Events
class GuildUpdateNoticeEvent(GuildNoticeEvent):
    """服务器信息更新"""

    __event__ = "notice.updated_guild"
    notice_type: Literal["updated_guild"]


class GuildDeleteNoticeEvent(GuildNoticeEvent):
    """服务器删除"""

    __event__ = "notice.deleted_guild"
    notice_type: Literal["deleted_guild"]


class GuildAddBlockListNoticeEvent(GuildNoticeEvent):
    """服务器封禁用户"""

    __event__ = "notice.added_block_list"
    notice_type: Literal["added_block_list"]


class GuildDeleteBlockListNoticeEvent(GuildNoticeEvent):
    """服务器取消封禁用户"""

    __event__ = "notice.deleted_block_list"
    notice_type: Literal["deleted_block_list"]


# User Events
class UserNoticeEvent(NoticeEvent):
    """用户相关事件列表"""

    group_id: int


class UserJoinAudioChannelNoticeEvent(UserNoticeEvent):
    """用户加入语音频道"""

    __event__ = "notice.joined_channel"
    notice_type: Literal["joined_channel"]


class UserJoinAudioChannelEvent(UserNoticeEvent):
    """用户退出语音频道"""

    __event__ = "notice.exited_channel"
    notice_type: Literal["exited_channel"]


class UserInfoUpdateNoticeEvent(UserNoticeEvent):
    """
    用户信息更新

    该事件与服务器无关, 遵循以下条件:
        - 仅当用户的 用户名 或 头像 变更时
        - 仅通知与该用户存在关联的用户或 Bot
            a. 存在聊天会话
            b. 双方好友关系
    """

    __event__ = "notice.user_updated"
    notice_type: Literal["user_updated"]


class SelfJoinGuildNoticeEvent(NoticeEvent):
    """
    自己新加入服务器

    当自己被邀请或主动加入新的服务器时, 产生该事件
    """

    __event__ = "notice.self_joined_guild"
    notice_type: Literal["self_joined_guild"]
    user_id: str
    group_id: int


class SelfExitGuildNoticeEvent(NoticeEvent):
    """
    自己退出服务器

    当自己被踢出服务器或被拉黑或主动退出服务器时, 产生该事件
    """

    __event__ = "notice.self_exited_guild"
    notice_type: Literal["self_exited_guild"]
    user_id: str
    group_id: int


class CartBtnClickNoticeEvent(NoticeEvent):
    """
    Card 消息中的 Button 点击事件
    """

    __event__ = "notice.message_btn_click"
    notice_type: Literal["message_btn_click"]
    user_id: str
    group_id: int


# Meta Events
class MetaEvent(OriginEvent):
    """元事件"""

    __event__ = "meta_event"
    post_type: Literal["meta_event"]
    meta_event_type: str


class LifecycleMetaEvent(MetaEvent):
    """生命周期元事件"""

    __event__ = "meta_event.lifecycle"
    meta_event_type: Literal["lifecycle"]
    sub_type: str


class HeartbeatMetaEvent(MetaEvent):
    """心跳元事件"""

    __event__ = "meta_event.heartbeat"
    meta_event_type: Literal["heartbeat"]
    sub_type: str


# 事件类映射
_kook_events = {
    model.__event__: model
    for model in globals().values()
    if inspect.isclass(model) and issubclass(model, OriginEvent)
}


def get_event_class(
    post_type: str, event_type: str, sub_type: Optional[str] = None
) -> Type[T_KookEvent]:  # type: ignore
    """根据接收到的消息类型返回对应的事件类。

    Args:
        post_type: 请求类型。
        event_type: 事件类型。
        sub_type: 子类型。

    Returns:
        对应的事件类。
    """
    if sub_type is None:
        return _kook_events[".".join((post_type, event_type))]  # type: ignore
    return (
        _kook_events.get(".".join((post_type, event_type, sub_type)))
        or _kook_events[".".join((post_type, event_type))]
    )  # type: ignore
