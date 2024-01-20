from .model import *

class ApiClient:
    async def asset_create(self, *, file) -> URL: ...
    async def blacklist_create(
        self,
        *,
        guild_id: str,
        target_id: str,
        remark: Optional[str] = ...,
        del_msg_days: Optional[str] = ...,
    ) -> None: ...
    async def blacklist_delete(self, *, guild_id: str, target_id: str) -> None: ...
    async def blacklist_list(self, *, guild_id: str) -> BlackListsReturn: ...
    async def channelRole_create(
        self, *, channel_id: str, type: Optional[str] = ..., value: Optional[str] = ...
    ) -> ChannelRoleReturn: ...
    async def channelRole_delete(
        self,
        *,
        channel_id: str,
        type: Optional[str] = ...,
        value: Optional[str] = ...,
    ) -> None: ...
    async def channelRole_index(self, *, channel_id: str) -> ChannelRoleInfo:
        """获取频道角色权限详情

        Args:
            channel_id (str): 频道ID

        Returns:
            ChannelRoleInfo: 频道角色权限详情
        """
        ...
    async def channelRole_update(
        self,
        *,
        channel_id: str,
        type: Optional[str] = ...,
        value: Optional[str] = ...,
        allow: Optional[int] = ...,
        deny: Optional[int] = ...,
    ) -> ChannelRoleReturn: ...
    async def channel_create(
        self,
        *,
        guild_id: str,
        name: str,
        parent_id: Optional[str] = ...,
        type: Optional[int] = ...,
        limit_amount: Optional[int] = ...,
        voice_quality: Optional[str] = ...,
        is_category: Optional[int] = ...,
    ) -> Channel: ...
    async def channel_delete(self, *, channel_id: str) -> None: ...
    async def channel_update(
        self,
        *,
        channel_id: str,
        name: Optional[str] = ...,
        topic: Optional[str] = ...,
        slow_mode: Optional[int] = ...,
    ) -> Channel: ...
    async def channel_list(
        self,
        *,
        guild_id: str,
        type: Optional[int] = ...,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
    ) -> ChannelsReturn: ...
    async def channel_moveUser(
        self,
        *,
        target_id: str,
        user_ids: List[int],
    ) -> None: ...
    async def channel_userList(self, *, channel_id: str) -> List[User]: ...
    async def channel_view(self, *, target_id: str) -> Channel: ...
    async def directMessage_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def directMessage_create(
        self,
        *,
        content: str,
        type: Optional[int] = ...,
        target_id: Optional[str] = ...,
        chat_code: Optional[str] = ...,
        quote: Optional[str] = ...,
        nonce: Optional[str] = ...,
    ) -> MessageCreateReturn: ...
    async def directMessage_delete(self, *, msg_id: str) -> None:
        """删除私信聊天消息

        Args:
            msg_id (str): 消息 id
        """
        ...
    async def directMessage_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: Optional[str] = ...
    ) -> None: ...
    async def directMessage_list(
        self,
        *,
        chat_code: Optional[str] = ...,
        target_id: Optional[str] = ...,
        msg_id: Optional[str] = ...,
        flag: Optional[str] = ...,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
    ) -> DirectMessagesReturn:
        """获取私信聊天消息列表

        Args:
            chat_code (str, optional):
                私信会话 Code,chat_code与target_id必须传一个.
            target_id (str, optional):
                目标用户 id,后端会自动创建会话. 有此参数之后可不传chat_code参数.
            msg_id (str, optional):
                参考消息 id,不传则查询最新消息.
            flag (str, optional):
                查询模式,有三种模式可以选择. 不传则默认查询最新的消息.
            page (int, optional): 目标页数.
            page_size (int, optional): 当前分页消息数量, 默认 `50`.

        Returns:
            DirectMessagesReturn：获取私信聊天消息列表返回信息
        """
        ...
    async def directMessage_reactionList(
        self, *, msg_id: str, emoji: str
    ) -> List[ReactionUser]: ...
    async def directMessage_update(
        self, *, content: str, msg_id: Optional[str] = ..., quote: Optional[str] = ...
    ) -> None:
        """更新私信聊天消息

        Args:
            content (str):
                消息 id
            msg_id (str, optional):
                消息内容
            quote (str, optional):
                回复某条消息的msgId. 如果为空,则代表删除回复,不传则无影响.
        """
        ...
    async def directMessage_view(
        self, *, chat_code: str, msg_id: str
    ) -> DirectMessage: ...
    async def gateway_index(self, *, compress: Optional[int] = ...) -> URL: ...
    async def guildEmoji_create(
        self, *, guild_id: str, emoji: Optional[bytes] = ..., name: Optional[str] = ...
    ) -> GuildEmoji: ...
    async def guildEmoji_delete(self, *, id: str) -> None: ...
    async def guildEmoji_list(
        self,
        *,
        guild_id: str,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
    ) -> GuildEmojisReturn: ...
    async def guildEmoji_update(self, *, id: str, name: str) -> None: ...
    async def guildMute_create(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_delete(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_list(
        self, *, guild_id: str, return_type: Optional[str] = ...
    ) -> None: ...
    async def guildRole_create(
        self, *, guild_id: str, name: Optional[str] = ...
    ) -> Role: ...
    async def guildRole_delete(self, *, guild_id: str, role_id: int) -> None: ...
    async def guildRole_grant(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuilRoleReturn: ...
    async def guildRole_list(
        self,
        *,
        guild_id: str,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
    ) -> RolesReturn: ...
    async def guildRole_revoke(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuilRoleReturn: ...
    async def guildRole_update(
        self,
        *,
        guild_id: str,
        role_id: int,
        name: Optional[str] = ...,
        color: Optional[int] = ...,
        hoist: Optional[int] = ...,
        mentionable: Optional[int] = ...,
        permissions: Optional[int] = ...,
    ) -> Role: ...
    async def guild_kickout(self, *, guild_id: str, target_id: str) -> None: ...
    async def guild_leave(self, *, guild_id: str) -> None: ...
    async def guild_list(
        self,
        *,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
        sort: Optional[str] = ...,
    ) -> GuildsReturn:
        """获取当前用户加入的服务器列表

        Args:
            page (Optional[int], optional): 目标页数
            page_size (Optional[int], optional): 每页数据数量
            sort (Optional[str], optional): 代表排序的字段

        Returns:
            GuildsReturn: 当前用户加入的服务器列表返回信息
        """
        ...
    async def guild_nickname(
        self,
        *,
        guild_id: str = ...,
        nickname: Optional[str] = ...,
        user_id: Optional[str] = ...,
    ) -> None: ...
    async def guild_userList(
        self,
        *,
        guild_id: str,
        channel_id: Optional[str] = ...,
        search: Optional[str] = ...,
        role_id: Optional[int] = ...,
        mobile_verified: Optional[int] = ...,
        active_time: Optional[int] = ...,
        joined_at: Optional[int] = ...,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
        filter_user_id: Optional[str] = ...,
    ) -> GuildUsersRetrun:
        """获取服务器中的用户列表

        Args:
            guild_id (str): 服务器 id
            channel_id (Optional[str], optional): 频道 id
            search (Optional[str], optional): 搜索关键字，在用户名或昵称中搜索
            role_id (Optional[int], optional): 角色 ID，获取特定角色的用户列表
            mobile_verified (Optional[int], optional): 只能为0或1，0是未认证，1是已认证
            active_time (Optional[int], optional): 根据活跃时间排序，0是顺序排列，1是倒序排列
            joined_at (Optional[int], optional): 根据加入时间排序，0是顺序排列，1是倒序排列
            page (Optional[int], optional): 目标页数
            page_size (Optional[int], optional): 每页数据数量
            filter_user_id (Optional[str], optional): 获取指定 id 所属用户的信息
        Returns:
            GuildsReturn: 服务器中的用户列表返回信息
        """
        ...
    async def guild_view(self, *, guild_id: str) -> Guild:
        """获取服务器详情

        Args:
            guild_id (str): 服务器id

        Returns:
            Guild: 服务器详情
        """
        ...
    async def intimacy_index(self, *, user_id: str) -> IntimacyIndexReturn: ...
    async def intimacy_update(
        self,
        *,
        user_id: str,
        score: Optional[int] = ...,
        social_info: Optional[str] = ...,
        img_id: Optional[str] = ...,
    ) -> None: ...
    async def invite_create(
        self,
        *,
        guild_id: Optional[str] = ...,
        channel_id: Optional[str] = ...,
        duration: Optional[int] = ...,
        setting_times: Optional[int] = ...,
    ) -> URL: ...
    async def invite_delete(
        self,
        *,
        url_code: str,
        guild_id: Optional[str] = ...,
        channel_id: Optional[str] = ...,
    ) -> None: ...
    async def invite_list(
        self,
        *,
        guild_id: Optional[str] = ...,
        channel_id: Optional[str] = ...,
        page: Optional[int] = ...,
        page_size: Optional[int] = ...,
    ) -> InvitesReturn: ...
    async def message_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def message_create(
        self,
        *,
        content: str,
        target_id: str,
        type: Optional[int] = ...,
        quote: Optional[str] = ...,
        nonce: Optional[str] = ...,
        temp_target_id: Optional[str] = ...,
    ) -> MessageCreateReturn: ...
    async def message_delete(self, *, msg_id: str) -> None: ...
    async def message_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: Optional[str] = ...
    ) -> None: ...
    async def message_list(
        self,
        *,
        target_id: str,
        msg_id: Optional[str] = ...,
        pin: Optional[int] = ...,
        flag: Optional[str] = ...,
        page_size: Optional[int] = ...,
    ) -> ChannelMessagesReturn: ...
    async def message_reactionList(
        self, *, msg_id: str, emoji: str
    ) -> List[ReactionUser]: ...
    async def message_update(
        self,
        *,
        msg_id: str,
        content: str,
        quote: Optional[str] = ...,
        temp_target_id: Optional[str] = ...,
    ) -> None: ...
    async def message_view(self, *, msg_id: str) -> ChannelMessage: ...
    async def userChat_create(self, *, target_id: str) -> UserChat: ...
    async def userChat_delete(self, *, chat_code: str) -> None: ...
    async def userChat_list(
        self, *, page: Optional[int] = ..., page_size: Optional[int] = ...
    ) -> UserChatsReturn: ...
    async def userChat_view(self, *, chat_code: str) -> UserChat: ...
    async def user_me(self) -> User: ...
    async def user_offline(self) -> None:
        """下线机器人"""
        ...
    async def user_view(
        self, *, user_id: str, guild_id: Optional[str] = ...
    ) -> User: ...
