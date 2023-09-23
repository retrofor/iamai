from typing import Any, Dict, List, Union, Optional

from pydantic import Field, BaseModel


class User(BaseModel):
    """
    开黑啦 User 字段

    https://developer.kaiheila.cn/doc/objects
    """

    id_: Optional[str] = Field(None, alias="id")
    """用户的 id"""
    username: Optional[str] = None
    """用户的名称"""
    nickname: Optional[str] = None
    """用户在当前服务器的昵称"""
    identify_num: Optional[str] = None
    """用户名的认证数字，用户名正常为：user_name#identify_num"""
    online: Optional[bool] = None
    """当前是否在线"""
    bot: Optional[bool] = None
    """是否为机器人"""
    os: Optional[str] = None
    """os"""
    status: Optional[int] = None
    """用户的状态,`0`和`1`代表正常，`10`代表被封禁"""
    avatar: Optional[str] = None
    """用户的头像的 url 地址"""
    vip_avatar: Optional[str] = None
    """	vip 用户的头像的 url 地址，可能为 gif 动图"""
    mobile_verified: Optional[bool] = None
    """是否手机号已验证"""
    roles: Optional[List[int]] = None
    """用户在当前服务器中的角色 id 组成的列表"""
    joined_at: Optional[int] = None
    """加入服务器时间"""
    active_time: Optional[int] = None
    """上次在线时间"""


class Role(BaseModel):
    """角色"""

    role_id: Optional[int] = None
    """角色 id"""
    name: Optional[str] = None
    """角色名称"""
    color: Optional[int] = None
    """颜色色值"""
    position: Optional[int] = None
    """顺序位置"""
    hoist: Optional[int] = None
    """是否为角色设定(与普通成员分开显示)"""
    mentionable: Optional[int] = None
    """是否允许任何人@提及此角色"""
    permissions: Optional[int] = None
    """权限码"""


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


class Channel(ChannelRoleInfo):
    """开黑啦 频道 字段"""

    id_: Optional[str] = Field(None, alias="id")
    """频道 id"""
    name: Optional[str] = None
    """频道名称"""
    user_id: Optional[str] = None
    """创建者 id"""
    master_id: Optional[str] = None
    """master id """
    guild_id: Optional[str] = None
    """服务器 id"""
    topic: Optional[str] = None
    """频道简介"""
    is_category: Optional[bool] = None
    """是否为分组，事件中为 int 格式"""
    parent_id: Optional[str] = None
    """上级分组的 id"""
    level: Optional[int] = None
    """排序 level"""
    slow_mode: Optional[int] = None
    """慢速模式下限制发言的最短时间间隔, 单位为秒(s)"""
    type: Optional[int] = None
    """频道类型: 1 文字频道, 2 语音频道"""
    has_password: Optional[bool] = None
    """是否有密码"""
    limit_amount: Optional[int] = None
    """人数限制"""


class Guild(BaseModel):
    """服务器"""

    id_: Optional[str] = Field(None, alias="id")
    """服务器 id"""
    name: Optional[str] = None
    """服务器名称"""
    topic: Optional[str] = None
    """服务器主题"""
    user_id: Optional[str] = None
    """服务器主的 id"""
    icon: Optional[str] = None
    """服务器 icon 的地址"""
    notify_type: Optional[int] = None
    """通知类型\n
    `0`代表默认使用服务器通知设置\n 
    `1`代表接收所有通知\n 
    `2`代表仅@被提及\n 
    `3`代表不接收通知
    """
    region: Optional[str] = None
    """服务器默认使用语音区域"""
    enable_open: Optional[bool] = None
    """是否为公开服务器"""
    open_id: Optional[str] = None
    """公开服务器 id"""
    default_channel_id: Optional[str] = None
    """默认频道 id"""
    welcome_channel_id: Optional[str] = None
    """欢迎频道 id"""
    roles: Optional[List[Role]] = None
    """角色列表"""
    channels: Optional[List[Channel]] = None
    """频道列表"""


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


class Emoji(BaseModel):
    id_: Optional[str] = Field(None, alias="id")
    name: Optional[str] = None

    # 转义 unicdoe 为 emoji表情
    # @root_validator(pre=True)
    # def parse_emoji(cls, values: dict):
    #     values['id'] = chr(int(values['id'][2:-2]))
    #     values['name'] = chr(int(values['name'][2:-2]))
    #     return values


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
