from .model import *  # noqa: F403

class ApiClient:
    async def asset_create(self, *, file) -> URL: ...  # noqa: F405
    async def blacklist_create(
        self,
        *,
        guild_id: str,
        target_id: str,
        remark: Optional[str] = ...,  # noqa: F405
        del_msg_days: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def blacklist_delete(self, *, guild_id: str, target_id: str) -> None: ...
    async def blacklist_list(self, *, guild_id: str) -> BlackListsReturn: ...  # noqa: F405
    async def channelRole_create(
        self, *, channel_id: str, type: Optional[str] = ..., value: Optional[str] = ...  # noqa: F405
    ) -> ChannelRoleReturn: ...  # noqa: F405
    async def channelRole_delete(
        self,
        *,
        channel_id: str,
        type: Optional[str] = ...,  # noqa: F405
        value: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def channelRole_index(self, *, channel_id: str) -> ChannelRoleInfo:  # noqa: F405
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
        type: Optional[str] = ...,  # noqa: F405
        value: Optional[str] = ...,  # noqa: F405
        allow: Optional[int] = ...,  # noqa: F405
        deny: Optional[int] = ...,  # noqa: F405
    ) -> ChannelRoleReturn: ...  # noqa: F405
    async def channel_create(
        self,
        *,
        guild_id: str,
        name: str,
        parent_id: Optional[str] = ...,  # noqa: F405
        type: Optional[int] = ...,  # noqa: F405
        limit_amount: Optional[int] = ...,  # noqa: F405
        voice_quality: Optional[str] = ...,  # noqa: F405
        is_category: Optional[int] = ...,  # noqa: F405
    ) -> Channel: ...  # noqa: F405
    async def channel_delete(self, *, channel_id: str) -> None: ...
    async def channel_update(
        self,
        *,
        channel_id: str,
        name: Optional[str] = ...,  # noqa: F405
        topic: Optional[str] = ...,  # noqa: F405
        slow_mode: Optional[int] = ...,  # noqa: F405
    ) -> Channel: ...  # noqa: F405
    async def channel_list(
        self,
        *,
        guild_id: str,
        type: Optional[int] = ...,  # noqa: F405
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> ChannelsReturn: ...  # noqa: F405
    async def channel_moveUser(
        self,
        *,
        target_id: str,
        user_ids: List[int],  # noqa: F405
    ) -> None: ...
    async def channel_userList(self, *, channel_id: str) -> List[User]: ...  # noqa: F405
    async def channel_view(self, *, target_id: str) -> Channel: ...  # noqa: F405
    async def directMessage_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def directMessage_create(
        self,
        *,
        content: str,
        type: Optional[int] = ...,  # noqa: F405
        target_id: Optional[str] = ...,  # noqa: F405
        chat_code: Optional[str] = ...,  # noqa: F405
        quote: Optional[str] = ...,  # noqa: F405
        nonce: Optional[str] = ...,  # noqa: F405
    ) -> MessageCreateReturn: ...  # noqa: F405
    async def directMessage_delete(self, *, msg_id: str) -> None:
        """删除私信聊天消息

        Args:
            msg_id (str): 消息 id
        """
        ...

    async def directMessage_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: Optional[str] = ...  # noqa: F405
    ) -> None: ...
    async def directMessage_list(
        self,
        *,
        chat_code: Optional[str] = ...,  # noqa: F405
        target_id: Optional[str] = ...,  # noqa: F405
        msg_id: Optional[str] = ...,  # noqa: F405
        flag: Optional[str] = ...,  # noqa: F405
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> DirectMessagesReturn:  # noqa: F405
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
    ) -> List[ReactionUser]: ...  # noqa: F405
    async def directMessage_update(
        self, *, content: str, msg_id: Optional[str] = ..., quote: Optional[str] = ...  # noqa: F405
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
    ) -> DirectMessage: ...  # noqa: F405
    async def gateway_index(self, *, compress: Optional[int] = ...) -> URL: ...  # noqa: F405
    async def guildEmoji_create(
        self, *, guild_id: str, emoji: Optional[bytes] = ..., name: Optional[str] = ...  # noqa: F405
    ) -> GuildEmoji: ...  # noqa: F405
    async def guildEmoji_delete(self, *, id: str) -> None: ...
    async def guildEmoji_list(
        self,
        *,
        guild_id: str,
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> GuildEmojisReturn: ...  # noqa: F405
    async def guildEmoji_update(self, *, id: str, name: str) -> None: ...
    async def guildMute_create(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_delete(
        self, *, guild_id: str = ..., target_id: str = ..., type: int = ...
    ) -> None: ...
    async def guildMute_list(
        self, *, guild_id: str, return_type: Optional[str] = ...  # noqa: F405
    ) -> None: ...
    async def guildRole_create(
        self, *, guild_id: str, name: Optional[str] = ...  # noqa: F405
    ) -> Role: ...  # noqa: F405
    async def guildRole_delete(self, *, guild_id: str, role_id: int) -> None: ...
    async def guildRole_grant(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuilRoleReturn: ...  # noqa: F405
    async def guildRole_list(
        self,
        *,
        guild_id: str,
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> RolesReturn: ...  # noqa: F405
    async def guildRole_revoke(
        self, *, guild_id: str, user_id: str, role_id: int
    ) -> GuilRoleReturn: ...  # noqa: F405
    async def guildRole_update(
        self,
        *,
        guild_id: str,
        role_id: int,
        name: Optional[str] = ...,  # noqa: F405
        color: Optional[int] = ...,  # noqa: F405
        hoist: Optional[int] = ...,  # noqa: F405
        mentionable: Optional[int] = ...,  # noqa: F405
        permissions: Optional[int] = ...,  # noqa: F405
    ) -> Role: ...  # noqa: F405
    async def guild_kickout(self, *, guild_id: str, target_id: str) -> None: ...
    async def guild_leave(self, *, guild_id: str) -> None: ...
    async def guild_list(
        self,
        *,
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
        sort: Optional[str] = ...,  # noqa: F405
    ) -> GuildsReturn:  # noqa: F405
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
        nickname: Optional[str] = ...,  # noqa: F405
        user_id: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def guild_userList(
        self,
        *,
        guild_id: str,
        channel_id: Optional[str] = ...,  # noqa: F405
        search: Optional[str] = ...,  # noqa: F405
        role_id: Optional[int] = ...,  # noqa: F405
        mobile_verified: Optional[int] = ...,  # noqa: F405
        active_time: Optional[int] = ...,  # noqa: F405
        joined_at: Optional[int] = ...,  # noqa: F405
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
        filter_user_id: Optional[str] = ...,  # noqa: F405
    ) -> GuildUsersRetrun:  # noqa: F405
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

    async def guild_view(self, *, guild_id: str) -> Guild:  # noqa: F405
        """获取服务器详情

        Args:
            guild_id (str): 服务器id

        Returns:
            Guild: 服务器详情
        """
        ...

    async def intimacy_index(self, *, user_id: str) -> IntimacyIndexReturn: ...  # noqa: F405
    async def intimacy_update(
        self,
        *,
        user_id: str,
        score: Optional[int] = ...,  # noqa: F405
        social_info: Optional[str] = ...,  # noqa: F405
        img_id: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def invite_create(
        self,
        *,
        guild_id: Optional[str] = ...,  # noqa: F405
        channel_id: Optional[str] = ...,  # noqa: F405
        duration: Optional[int] = ...,  # noqa: F405
        setting_times: Optional[int] = ...,  # noqa: F405
    ) -> URL: ...  # noqa: F405
    async def invite_delete(
        self,
        *,
        url_code: str,
        guild_id: Optional[str] = ...,  # noqa: F405
        channel_id: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def invite_list(
        self,
        *,
        guild_id: Optional[str] = ...,  # noqa: F405
        channel_id: Optional[str] = ...,  # noqa: F405
        page: Optional[int] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> InvitesReturn: ...  # noqa: F405
    async def message_addReaction(self, *, msg_id: str, emoji: str) -> None: ...
    async def message_create(
        self,
        *,
        content: str,
        target_id: str,
        type: Optional[int] = ...,  # noqa: F405
        quote: Optional[str] = ...,  # noqa: F405
        nonce: Optional[str] = ...,  # noqa: F405
        temp_target_id: Optional[str] = ...,  # noqa: F405
    ) -> MessageCreateReturn: ...  # noqa: F405
    async def message_delete(self, *, msg_id: str) -> None: ...
    async def message_deleteReaction(
        self, *, msg_id: str, emoji: str, user_id: Optional[str] = ...  # noqa: F405
    ) -> None: ...
    async def message_list(
        self,
        *,
        target_id: str,
        msg_id: Optional[str] = ...,  # noqa: F405
        pin: Optional[int] = ...,  # noqa: F405
        flag: Optional[str] = ...,  # noqa: F405
        page_size: Optional[int] = ...,  # noqa: F405
    ) -> ChannelMessagesReturn: ...  # noqa: F405
    async def message_reactionList(
        self, *, msg_id: str, emoji: str
    ) -> List[ReactionUser]: ...  # noqa: F405
    async def message_update(
        self,
        *,
        msg_id: str,
        content: str,
        quote: Optional[str] = ...,  # noqa: F405
        temp_target_id: Optional[str] = ...,  # noqa: F405
    ) -> None: ...
    async def message_view(self, *, msg_id: str) -> ChannelMessage: ...  # noqa: F405
    async def userChat_create(self, *, target_id: str) -> UserChat: ...  # noqa: F405
    async def userChat_delete(self, *, chat_code: str) -> None: ...
    async def userChat_list(
        self, *, page: Optional[int] = ..., page_size: Optional[int] = ...  # noqa: F405
    ) -> UserChatsReturn: ...  # noqa: F405
    async def userChat_view(self, *, chat_code: str) -> UserChat: ...  # noqa: F405
    async def user_me(self) -> User: ...  # noqa: F405
    async def user_offline(self) -> None:
        """下线机器人"""
        ...

    async def user_view(
        self, *, user_id: str, guild_id: Optional[str] = ...  # noqa: F405
    ) -> User: ...  # noqa: F405
