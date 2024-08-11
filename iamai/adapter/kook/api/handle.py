from .model import *  # noqa: F403

api_method_map = {
    "asset/create": {"method": "POST", "type": URL},  # noqa: F405
    "blacklist/create": {"method": "POST", "type": None},
    "blacklist/delete": {"method": "POST", "type": None},
    "blacklist/list": {"method": "GET", "type": BlackListsReturn},  # noqa: F405
    "channel-role/create": {"method": "POST", "type": ChannelRoleReturn},  # noqa: F405
    "channel-role/delete": {"method": "POST", "type": None},
    "channel-role/index": {"method": "GET", "type": ChannelRoleInfo},  # noqa: F405
    "channel-role/update": {"method": "POST", "type": ChannelRoleReturn},  # noqa: F405
    "channel/create": {"method": "POST", "type": Channel},  # noqa: F405
    "channel/delete": {"method": "POST", "type": None},
    "channel/update": {"method": "POST", "type": Channel},  # noqa: F405
    "channel/list": {"method": "GET", "type": ChannelsReturn},  # noqa: F405
    "channel/move-user": {"method": "POST", "type": None},
    "channel/user-list": {"method": "POST", "type": List[User]},  # noqa: F405
    "channel/view": {"method": "GET", "type": Channel},  # noqa: F405
    "direct-message/add-reaction": {"method": "POST", "type": None},
    "direct-message/create": {"method": "POST", "type": MessageCreateReturn},  # noqa: F405
    "direct-message/delete": {"method": "POST", "type": None},
    "direct-message/delete-reaction": {"method": "POST", "type": None},
    "direct-message/list": {"method": "GET", "type": DirectMessagesReturn},  # noqa: F405
    "direct-message/reaction-list": {"method": "GET", "type": List[ReactionUser]},  # noqa: F405
    "direct-message/update": {"method": "POST", "type": None},
    "direct-message/view": {"method": "GET", "type": DirectMessage},  # noqa: F405
    "gateway/index": {"method": "GET", "type": URL},  # noqa: F405
    "guild-emoji/create": {"method": "POST", "type": None},
    "guild-emoji/delete": {"method": "POST", "type": None},
    "guild-emoji/list": {"method": "GET", "type": GuildEmojisReturn},  # noqa: F405
    "guild-emoji/update": {"method": "POST", "type": None},
    "guild-mute/create": {"method": "POST", "type": None},
    "guild-mute/delete": {"method": "POST", "type": None},
    "guild-mute/list": {"method": "GET", "type": None},
    "guild-role/create": {"method": "POST", "type": Role},  # noqa: F405
    "guild-role/delete": {"method": "POST", "type": None},
    "guild-role/grant": {"method": "POST", "type": GuilRoleReturn},  # noqa: F405
    "guild-role/list": {"method": "GET", "type": RolesReturn},  # noqa: F405
    "guild-role/revoke": {"method": "POST", "type": GuilRoleReturn},  # noqa: F405
    "guild-role/update": {"method": "POST", "type": Role},  # noqa: F405
    "guild/kickout": {"method": "POST", "type": None},
    "guild/leave": {"method": "POST", "type": None},
    "guild/list": {"method": "GET", "type": GuildsReturn},  # noqa: F405
    "guild/nickname": {"method": "POST", "type": None},
    "guild/user-list": {"method": "GET", "type": GuildUsersRetrun},  # noqa: F405
    "guild/view": {"method": "GET", "type": Guild},  # noqa: F405
    "intimacy/index": {"method": "GET", "type": IntimacyIndexReturn},  # noqa: F405
    "intimacy/update": {"method": "POST", "type": None},
    "invite/create": {"method": "POST", "type": URL},  # noqa: F405
    "invite/delete": {"method": "POST", "type": None},
    "invite/list": {"method": "GET", "type": InvitesReturn},  # noqa: F405
    "message/add-reaction": {"method": "POST", "type": None},
    "message/create": {"method": "POST", "type": MessageCreateReturn},  # noqa: F405
    "message/delete": {"method": "POST", "type": None},
    "message/delete-reaction": {"method": "POST", "type": None},
    "message/list": {"method": "GET", "type": ChannelMessagesReturn},  # noqa: F405
    "message/reaction-list": {"method": "GET", "type": List[ReactionUser]},  # noqa: F405
    "message/update": {"method": "POST", "type": None},
    "message/view": {"method": "GET", "type": ChannelMessage},  # noqa: F405
    "user-chat/create": {"method": "POST", "type": UserChat},  # noqa: F405
    "user-chat/delete": {"method": "POST", "type": None},
    "user-chat/list": {"method": "GET", "type": UserChatsReturn},  # noqa: F405
    "user-chat/view": {"method": "GET", "type": UserChat},  # noqa: F405
    "user/me": {"method": "GET", "type": User},  # noqa: F405
    "user/offline": {"method": "POST", "type": None},
    "user/view": {"method": "GET", "type": User},  # noqa: F405
}


def get_api_method(api: str) -> str:
    return api_method_map.get(api, {}).get("method", "POST")


def get_api_restype(api: str) -> Any:  # noqa: F405
    return api_method_map.get(api, {}).get("type")
