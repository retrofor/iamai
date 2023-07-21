"""Kook 适配器消息。"""

import json
from io import StringIO
from dataclasses import dataclass
from typing_extensions import override, deprecated
from typing import Any, Dict, Type, Tuple, Union, Mapping, Iterable, Optional, cast

from iamai.message import Message, MessageSegment

from .exceptions import UnsupportedMessageType, UnsupportedMessageOperation

__all__ = [
    "T_KookMSG",
    "KookMessage",
    "KookMessageSegment",
    "escape_kmarkdown",
    "unescape_kmarkdown",
]

T_KookMSG = Union[str, Mapping, Iterable[Mapping], "KookMessageSegment", "KookMessage"]

ESCAPE_CHAR = "!()*-.:>[\]`~"

msg_type_map = {
    "text": 1,
    "image": 2,
    "video": 3,
    "file": 4,
    "audio": 8,
    "kmarkdown": 9,
    "card": 10,
}

rev_msg_type_map = {code: msg_type for msg_type, code in msg_type_map.items()}
# 根据协议消息段类型显示消息段内容
segment_text = {
    "text": "[文字]",
    "image": "[图片]",
    "video": "[视频]",
    "file": "[文件]",
    "audio": "[音频]",
    "kmarkdown": "[KMarkdown消息]",
    "card": "[卡片消息]",
}


class KookMessageSegment(MessageSegment["KookMessage"]):
    """Kook 消息字段。"""

    """
    开黑啦 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。

    https://developer.kaiheila.cn/doc/event/message
    """

    # 已知：
    # command/shell_command使用message_seg = Message[0]; str(message_seg) if message_seg.is_text()
    # startswith/endswith/keyword使用event.get_plaintext()
    # regex使用str(Message)

    @property
    def _message_class(cls) -> Type["KookMessage"]:
        return KookMessage

    def __str__(self) -> str:
        if self.type in ["text", "kmarkdown"]:
            return str(self.data["content"])
        elif self.type == "at":
            return str(f"@{self.data['user_name']}")
        else:
            return segment_text.get(self.type, "[未知类型消息]")

    @property
    def get_plain_text(self):
        if self.type == "text":
            return self.data["content"]
        elif self.type == "kmarkdown":
            return self.data["raw_content"]
        else:
            return ""

    # @overrides(MessageSegment)
    def __add__(
        self, other: Union[str, "KookMessageSegment", Iterable["KookMessageSegment"]]
    ) -> "KookMessage":
        return KookMessage(self.conduct(other))

    # @overrides(MessageSegment)
    def __radd__(
        self, other: Union[str, "MessageSegment", Iterable["MessageSegment"]]
    ) -> "Message":
        if isinstance(other, str):
            other = MessageSegment(self.type, {"content": other})
        return KookMessage(other.conduct(self))  # type: ignore

    def conduct(
        self, other: Union[str, "KookMessageSegment", Iterable["KookMessageSegment"]]
    ) -> "KookMessageSegment":
        """
        连接两个或多个 MessageSegment，必须为纯文本段或 KMarkdown 段
        """

        if isinstance(other, (str, KookMessageSegment)):
            other = [other]  # type: ignore
        msg = KookMessage([self, *other])
        msg.reduce()  # type: ignore

        if len(msg) != 1:
            raise UnsupportedMessageOperation("必须为纯文本段或 KMarkdown 段")
        else:
            return msg[0]  # type: ignore

    # @overrides(MessageSegment)
    def is_text(self) -> bool:
        if self.type == "kmarkdown":
            return self.data["raw_content"] == self.data["content"]
        else:
            return self.type == "text"

    @staticmethod
    @deprecated("用 KMarkdown 语法 (met)用户id/here/all(met) 代替")
    def at(user_id: str) -> "KookMessageSegment":
        return KookMessageSegment.KMarkdown(f"(met){user_id}(met)", user_id)

    @staticmethod
    def text(text: str) -> "KookMessageSegment":
        return KookMessageSegment("text", {"content": text})

    @staticmethod
    def image(file_key: str) -> "KookMessageSegment":
        return KookMessageSegment("image", {"file_key": file_key})

    @staticmethod
    def video(file_key: str, title: Optional[str] = None) -> "KookMessageSegment":
        return KookMessageSegment(
            "video",
            {
                "file_key": file_key,
                "title": title,
            },
        )

    @staticmethod
    def file(file_key: str, title: Optional[str] = None) -> "KookMessageSegment":
        return KookMessageSegment(
            "file",
            {
                "file_key": file_key,
                "title": title,
            },
        )

    @staticmethod
    def audio(
        file_key: str, title: Optional[str] = None, cover_file_key: Optional[str] = None
    ) -> "KookMessageSegment":
        return KookMessageSegment(
            "audio",
            {"file_key": file_key, "title": title, "cover_file_key": cover_file_key},
        )

    @staticmethod
    def KMarkdown(
        content: str, raw_content: Optional[str] = None
    ) -> "KookMessageSegment":
        """
        构造KMarkdown消息段

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/kmarkdown）
        @param raw_content: （可选）消息段的纯文本内容
        """
        if raw_content is None:
            raw_content = ""

        return KookMessageSegment(
            "kmarkdown", {"content": content, "raw_content": raw_content}
        )

    @staticmethod
    def Card(content: Any) -> "KookMessageSegment":
        """
        构造卡片消息

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/cardmessage）
        """
        if not isinstance(content, str):
            content = json.dumps(content)

        return KookMessageSegment("card", {"content": content})

    @staticmethod
    def quote(msg_id: str) -> "KookMessageSegment":
        return KookMessageSegment("quote", {"msg_id": msg_id})


class KookMessage(Message[MessageSegment]):
    """
    开黑啦 v3 协议 Message 适配。
    """

    @property
    def _message_segment_class(self) -> Type["KookMessageSegment"]:
        return KookMessageSegment

    @staticmethod
    def _str_to_message_segment(
        msg: Union[str, Mapping, Iterable[Mapping]]
    ) -> Iterable[KookMessageSegment]:
        if isinstance(msg, Mapping):
            msg = cast(Mapping[str, Any], msg)
            yield KookMessageSegment(msg["type"], msg.get("content") or {})
        elif isinstance(msg, Iterable) and not isinstance(msg, str):
            for seg in msg:
                yield KookMessageSegment(seg["type"], seg.get("content") or {})
        elif isinstance(msg, str):
            yield KookMessageSegment("text", {"content": msg})

    def get_plain_text(self) -> str:
        return "".join(seg.get_plain_text() for seg in self)  # type: ignore

    def reduce(self) -> None:
        """合并消息内连续的纯文本段和 KMarkdown 段。"""
        index = 1
        while index < len(self):
            prev = self[index - 1]
            cur = self[index]
            if prev.type == "text" and cur.type == "text":
                self[index - 1] = MessageSegment(
                    prev.type, {"content": prev.data["content"] + cur.data["content"]}
                )
                del self[index]
            elif prev.type == "kmarkdown" and cur.type == "kmarkdown":
                self[index - 1] = MessageSegment(
                    prev.type,
                    {
                        "content": prev.data["content"] + cur.data["content"],
                        "raw_content": prev.data["raw_content"]
                        + cur.data["raw_content"],
                    },
                )
                del self[index]
            elif prev.type == "kmarkdown" and cur.type == "text":
                self[index - 1] = MessageSegment(
                    prev.type,
                    {
                        "content": prev.data["content"]
                        + escape_kmarkdown(cur.data["content"]),
                        "raw_content": prev.data["raw_content"] + cur.data["content"],
                    },
                )
                del self[index]
            elif prev.type == "text" and cur.type == "kmarkdown":
                self[index - 1] = MessageSegment(
                    prev.type,
                    {
                        "content": escape_kmarkdown(prev.data["content"])
                        + cur.data["content"],
                        "raw_content": prev.data["content"] + cur.data["raw_content"],
                    },
                )
                del self[index]
            else:
                index += 1


def _convert_to_card_message(msg: KookMessage) -> KookMessageSegment:
    cards = []
    modules = []

    for seg in msg:
        if seg.type == "card":
            if len(modules) != 0:
                cards.append(
                    {"type": "card", "theme": "none", "size": "lg", "modules": modules}
                )
                modules = []
            cards.extend(json.loads(seg.data["content"]))
        elif seg.type == "text":
            modules.append(
                {
                    "type": "section",
                    "text": {"type": "plain-text", "content": seg.data["content"]},
                }
            )
        elif seg.type == "kmarkdown":
            modules.append(
                {
                    "type": "section",
                    "text": {"type": "kmarkdown", "content": seg.data["content"]},
                }
            )
        elif seg.type == "image":
            modules.append(
                {
                    "type": "container",
                    "elements": [{"type": "image", "src": seg.data["file_key"]}],
                }
            )
        elif seg.type in ("audio", "video", "file"):
            mod = {
                "type": seg.type,
                "src": seg.data["file_key"],
            }
            if seg.data.get("title") is not None:
                mod["title"] = seg.data["title"]
            if seg.data.get("cover_file_key") is not None:
                mod["cover"] = seg.data["cover_file_key"]
            modules.append(mod)
        else:
            raise UnsupportedMessageType(seg.type)

    if len(modules) != 0:
        cards.append(
            {"type": "card", "theme": "none", "size": "lg", "modules": modules}
        )

    return KookMessageSegment.Card(cards)


@dataclass
class MessageSerializer:
    """
    开黑啦 协议 Message 序列化器。
    """

    message: Message

    def serialize(self, for_send: bool = True) -> Tuple[int, str]:
        if len(self.message) != 1:
            self.message = self.message.copy()
            self.message.reduce()  # type: ignore

        if len(self.message) != 1:
            # 转化为卡片消息发送
            return MessageSerializer(KookMessage(_convert_to_card_message(self.message))).serialize()  # type: ignore

        msg_type = self.message[0].type
        msg_type_code = msg_type_map[msg_type]
        # bot 发送消息只支持"text", "kmarkdown", "card"
        # 经测试还支持"image", "video", "file"
        if msg_type in ("text", "kmarkdown", "card"):
            return msg_type_code, self.message[0].data["content"]
        elif msg_type in ("image", "video", "file"):
            return msg_type_code, self.message[0].data["file_key"]
        elif msg_type == "audio":
            if not for_send:
                return msg_type_code, self.message[0].data["file_key"]
            else:
                # 转化为卡片消息发送
                return MessageSerializer(
                    KookMessage(_convert_to_card_message(self.message))
                ).serialize()
        else:
            raise UnsupportedMessageType(msg_type)


@dataclass
class MessageDeserializer:
    """
    开黑啦 协议 Message 反序列化器。
    """

    type_code: int
    data: Dict

    def __post_init__(self):
        self.type = rev_msg_type_map.get(self.type_code, "")

    def deserialize(self) -> KookMessage:
        if self.type == "text":
            return KookMessage(KookMessageSegment.text(self.data["content"]))
        elif self.type == "image":
            return KookMessage(KookMessageSegment.image(self.data["content"]))
        elif self.type == "video":
            return KookMessage(
                KookMessageSegment.video(self.data["attachments"]["url"])
            )
        elif self.type == "file":
            return KookMessage(KookMessageSegment.file(self.data["attachments"]["url"]))
        elif self.type == "kmarkdown":
            content = self.data["content"]
            raw_content = self.data["kmarkdown"]["raw_content"]

            # raw_content默认strip掉首尾空格，但是开黑啦本体的聊天界面中不会strip，所以这里还原了
            unescaped = unescape_kmarkdown(content)
            is_plain_text = unescaped.strip() == raw_content
            if not is_plain_text:
                return KookMessage(KookMessageSegment.KMarkdown(content, raw_content))
            raw_content = unescaped

            return KookMessage(KookMessageSegment.text(raw_content))
        elif self.type == "card":
            return KookMessage(KookMessageSegment.Card(self.data["content"]))
        else:
            return KookMessage(KookMessageSegment(self.type, self.data))


def escape_kmarkdown(content: str):
    """
    将文本中的kmarkdown标识符进行转义
    """
    with StringIO() as f:
        for c in content:
            if c in ESCAPE_CHAR:
                f.write("\\")
            f.write(c)
        return f.getvalue()


def unescape_kmarkdown(content: str):
    """
    去除kmarkdown中的转义字符
    """
    with StringIO() as f:
        i = 0
        while i < len(content):
            if content[i] == "\\":
                if i + 1 < len(content) and content[i + 1] in ESCAPE_CHAR:
                    f.write(content[i + 1])
                    i += 2
                    continue

            f.write(content[i])
            i += 1
        return f.getvalue()
