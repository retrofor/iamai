from typing import Any, Dict, Tuple, Callable


def make_sender(api: str, method: str, payload: dict | None) -> Callable:
    """
    生成发送请求的函数
    """

    def sender(data: Dict[str, Any]) -> Tuple[str, str, dict]:
        if payload is None:
            return api, method, {}
        formatted_payload = {
            key: value.format(**data) if isinstance(value, str) else value
            for key, value in payload.items()
        }
        return api, method, formatted_payload

    return sender


HANDLE = {
    "send_message": make_sender(
        "message/send",
        "POST",
        {
            "peer": {"chatType": "{chat_type}", "peerUin": "{target}", "guildId": None},
            "elements": "{elements}",
        },
    ),
    "get_self_profile": make_sender("getSelfProfile", "GET", {}),
    "get_friends": make_sender("bot/friends", "GET", {}),
    "get_groups": make_sender("bot/groups", "GET", {}),
    "mute_member": make_sender(
        "group/muteMember",
        "POST",
        {
            "group": "{group}",
            "memList": [{"uin": i, "timeStamp": "{duration}"} for i in "{members}"],
        },
    ),
    "unmute_member": make_sender(
        "group/muteMember",
        "POST",
        {
            "group": "{group}",
            "memList": [{"uin": i, "timeStamp": 0} for i in "{members}"],
        },
    ),
    "mute_everyone": make_sender(
        "group/muteEveryone",
        "POST",
        {
            "group": "{group}",
            "enable": True,
        },
    ),
    "unmute_everyone": make_sender(
        "group/muteEveryone",
        "POST",
        {
            "group": "{group}",
            "enable": False,
        },
    ),
    "kick": make_sender(
        "group/kick",
        "POST",
        {
            "uidList": "{members}",
            "group": "{group}",
            "refuseForever": "{refuse_forever}",
            "reason": "{reason}",
        },
    ),
    "get_announcements": make_sender(
        "group/getAnnouncements",
        "POST",
        {
            "group": "{group}",
        },
    ),
    "get_members": make_sender(
        "group/getMemberList",
        "POST",
        {
            "group": "{group}",
            "size": "{size}",
        },
    ),
    "fetch_media": make_sender(
        "message/fetchRichMedia",
        "POST",
        {
            "msgId": "{msg_id}",
            "chatType": "{chat_type}",
            "peerUid": "{target}",
            "elementId": "{element_id}",
            "thumbSize": "{thumb_size}",
            "downloadType": "{download_type}",
        },
    ),
    "upload": make_sender("upload", "POST", "{file}"),
    "recall_message": make_sender(
        "message/recall",
        "POST",
        {
            "msgIds": "{msg_ids}",
            "peer": {"chatType": "{chat_type}", "peerUin": "{target}", "guildId": None},
        },
    ),
    "get_history_messages": make_sender(
        "message/getHistory",
        "POST",
        {
            "peer": {"chatType": "{chat_type}", "peerUin": "{target}", "guildId": None},
            "offsetMsgId": "{offset_msg_id}",
            "count": "{count}",
        },
    ),
    "send_fake_forward": make_sender(
        "message/unsafeSendForward",
        "POST",
        {
            "dstContact": {
                "chatType": "{chat_type}",
                "peerUin": "{target}",
                "guildId": None,
            },
            "srcContact": {
                "chatType": "{source_chat_type}",
                "peerUin": "{source_target}",
                "guildId": None,
            },
            "msgElements": "{elements}",
        },
    ),
}
