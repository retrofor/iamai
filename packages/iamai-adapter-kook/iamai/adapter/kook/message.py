"""Kook 适配器消息。"""
import json
from io import StringIO
from dataclasses import dataclass
from typing_extensions import override, deprecated
from typing import (  # type: ignore
    Any,
    Dict,
    Type,
    Tuple,
    Union,
    Mapping,
    Iterable,
    Optional,
    cast,
)

from iamai.log import logger
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


class KookMessage(Message["KookMessageSegment"]):
    """
    Kook v3 协议 Message 适配。
    """

    @property
    def _message_segment_class(self) -> Type["KookMessageSegment"]:
        return KookMessageSegment

    def _str_to_message_segment(self, msg) -> "KookMessageSegment":
        return KookMessageSegment(type="text", data={"content": msg})

    def _mapping_to_message_segment(self, msg: Mapping) -> "KookMessageSegment":
        return KookMessageSegment(type=msg["type"], data=msg.get("content") or {})


class KookMessageSegment(MessageSegment["KookMessage"]):
    """Kook 消息字段。"""

    """
    Kook 协议 MessageSegment 适配。具体方法参考协议消息段类型或源码。

    https://developer.kookapp.cn/doc/event/message
    """

    @property
    def _message_class(self) -> Type["KookMessage"]:
        return KookMessage

    def __str__(self) -> str:
        if self.type in ["text", "kmarkdown"]:
            return str(self.data["content"])
        elif self.type == "at":
            return str(f"@{self.data['user_name']}")
        else:
            return segment_text.get(self.type, "[未知类型消息]")

    @classmethod
    @deprecated("用 KMarkdown 语法 (met)用户id/here/all(met) 代替")
    def at(cls, user_id: str) -> "KookMessageSegment":
        return KookMessageSegment.KMarkdown(f"(met){user_id}(met)", user_id)

    @classmethod
    def text(cls, text: str) -> "KookMessageSegment":
        return cls(type="text", data={"content": text})

    @classmethod
    def image(cls, file_key: str) -> "KookMessageSegment":
        return cls(type="image", data={"file_key": file_key})

    @classmethod
    def video(cls, file_key: str, title: Optional[str] = None) -> "KookMessageSegment":
        return cls(
            type="video",
            data={
                "file_key": file_key,
                "title": title,
            },
        )

    @classmethod
    def file(cls, file_key: str, title: Optional[str] = None) -> "KookMessageSegment":
        return cls(
            "file",
            {
                "file_key": file_key,
                "title": title,
            },
        )

    @classmethod
    def audio(
        cls,
        file_key: str,
        title: Optional[str] = None,
        cover_file_key: Optional[str] = None,
    ) -> "KookMessageSegment":
        return cls(
            type="audio",
            data={
                "file_key": file_key,
                "title": title,
                "cover_file_key": cover_file_key,
            },
        )

    @classmethod
    def KMarkdown(
        cls, content: str, raw_content: Optional[str] = None
    ) -> "KookMessageSegment":
        """
        构造KMarkdown消息段

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/kmarkdown）
        @param raw_content: （可选）消息段的纯文本内容
        """
        if raw_content is None:
            raw_content = ""

        return cls(
            type="kmarkdown", data={"content": content, "raw_content": raw_content}
        )

    @classmethod
    def Card(cls, content: Any) -> "KookMessageSegment":
        """
        构造卡片消息

        @param content: KMarkdown消息内容（语法参考：https://developer.kookapp.cn/doc/cardmessage）
        """
        if not isinstance(content, str):
            content = json.dumps(content)

        return cls(type="card", data={"content": content})

    @classmethod
    def quote(cls, msg_id: str) -> "KookMessageSegment":
        return cls(type="quote", data={"msg_id": msg_id})


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
    Kook 协议 Message 序列化器。
    """

    message: KookMessage

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
    Kook 协议 Message 反序列化器。
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
            raw_content = self.data["extra"]["kmarkdown"]["raw_content"]

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
