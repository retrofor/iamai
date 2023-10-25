"""OneBot11 适配器消息。"""
from typing import Type, Union, Literal, Mapping, Iterable, Optional

from iamai.message import Message, MessageSegment

__all__ = ["T_CQMSG", "OneBot11Message", "OneBot11MessageSegment", "escape"]

T_CQMSG = Union[
    str, Mapping, Iterable[Mapping], "OneBot11MessageSegment", "OneBot11Message"
]


class OneBot11Message(Message["OneBot11MessageSegment"]):
    """OneBot11 消息。"""

    @property
    def _message_segment_class(self) -> Type["OneBot11MessageSegment"]:
        return OneBot11MessageSegment

    def _str_to_message_segment(self, msg) -> "OneBot11MessageSegment":
        return OneBot11MessageSegment.text(msg)


class OneBot11MessageSegment(MessageSegment["OneBot11Message"]):
    """OneBot11 消息字段。"""

    @property
    def _message_class(self) -> Type["OneBot11Message"]:
        return OneBot11Message

    def __str__(self) -> str:
        return self.data.get("text", "") if self.type == "text" else self.get_cqcode()

    def get_cqcode(self) -> str:
        """
        Returns:
            此消息字段的 CQ 码形式。
        """
        if self.type == "text":
            return escape(self.data.get("text", ""), escape_comma=False)

        params = ",".join(
            [f"{k}={escape(str(v))}" for k, v in self.data.items() if v is not None]
        )
        return f'[CQ:{self.type}{"," if params else ""}{params}]'

    @classmethod
    def text(cls, text: str) -> "OneBot11MessageSegment":
        """纯文本"""
        return cls(type="text", data={"text": text})

    @classmethod
    def face(cls, id_: int) -> "OneBot11MessageSegment":
        """QQ 表情"""
        return cls(type="face", data={"id": str(id_)})

    @classmethod
    def image(
        cls,
        file: str,
        type_: Optional[Literal["flash"]] = None,
        cache: bool = True,
        proxy: bool = True,
        timeout: Optional[int] = None,
    ) -> "OneBot11MessageSegment":
        """图片"""
        return cls(
            type="image",
            data={
                "file": file,
                "type": type_,
                "cache": cache,
                "proxy": proxy,
                "timeout": timeout,
            },
        )

    @classmethod
    def record(
        cls,
        file: str,
        magic: bool = False,
        cache: bool = True,
        proxy: bool = True,
        timeout: Optional[int] = None,
    ) -> "OneBot11MessageSegment":
        """语音"""
        return cls(
            type="record",
            data={
                "file": file,
                "magic": magic,
                "cache": cache,
                "proxy": proxy,
                "timeout": timeout,
            },
        )

    @classmethod
    def video(
        cls,
        file: str,
        cache: bool = True,
        proxy: bool = True,
        timeout: Optional[int] = None,
    ) -> "OneBot11MessageSegment":
        """短视频"""
        return cls(
            type="video",
            data={"file": file, "cache": cache, "proxy": proxy, "timeout": timeout},
        )

    @classmethod
    def at(cls, qq: Union[int, Literal["all"]]) -> "OneBot11MessageSegment":
        """@某人"""
        return cls(type="at", data={"qq": str(qq)})

    @classmethod
    def rps(cls) -> "OneBot11MessageSegment":
        """猜拳魔法表情"""
        return cls(type="rps", data={})

    @classmethod
    def dice(cls) -> "OneBot11MessageSegment":
        """掷骰子魔法表情"""
        return cls(type="dice", data={})

    @classmethod
    def shake(cls) -> "OneBot11MessageSegment":
        """窗口抖动（戳一戳）"""
        return cls(type="shake", data={})

    @classmethod
    def poke(cls, type_: str, id_: int) -> "OneBot11MessageSegment":
        """戳一戳"""
        return cls(type="poke", data={"type": type_, "id": str(id_)})

    @classmethod
    def anonymous(cls, ignore: Optional[bool] = None) -> "OneBot11MessageSegment":
        """匿名发消息"""
        return cls(type="anonymous", data={"ignore": ignore})

    @classmethod
    def share(
        cls,
        url: str,
        title: str,
        content: Optional[str] = None,
        image: Optional[str] = None,
    ) -> "OneBot11MessageSegment":
        """链接分享"""
        return cls(
            type="share",
            data={"url": url, "title": title, "content": content, "image": image},
        )

    @classmethod
    def contact(
        cls, type_: Literal["qq", "group"], id_: int
    ) -> "OneBot11MessageSegment":
        """推荐好友/推荐群"""
        return cls(type="contact", data={"type": type_, "id": str(id_)})

    @classmethod
    def contact_friend(cls, id_: int) -> "OneBot11MessageSegment":
        """推荐好友"""
        return cls(type="contact", data={"type": "qq", "id": str(id_)})

    @classmethod
    def contact_group(cls, id_: int) -> "OneBot11MessageSegment":
        """推荐好友"""
        return cls(type="contact", data={"type": "group", "id": str(id_)})

    @classmethod
    def location(
        cls, lat: float, lon: float, title: Optional[str], content: Optional[str] = None
    ) -> "OneBot11MessageSegment":
        """位置"""
        return cls(
            type="location",
            data={"lat": str(lat), "lon": str(lon), "title": title, "content": content},
        )

    @classmethod
    def music(
        cls, type_: Literal["qq", "163", "xm"], id_: int
    ) -> "OneBot11MessageSegment":
        """音乐分享"""
        return cls(type="music", data={"type": type_, "id": str(id_)})

    @classmethod
    def music_custom(
        cls,
        url: str,
        audio: str,
        title: str,
        content: Optional[str] = None,
        image: Optional[str] = None,
    ) -> "OneBot11MessageSegment":
        """音乐自定义分享"""
        return cls(
            type="music",
            data={
                "type": "custom",
                "url": url,
                "audio": audio,
                "title": title,
                "content": content,
                "image": image,
            },
        )

    @classmethod
    def reply(cls, id_: int) -> "OneBot11MessageSegment":
        """回复"""
        return cls(type="reply", data={"id": str(id_)})

    @classmethod
    def node(cls, id_: int) -> "OneBot11MessageSegment":
        """合并转发节点"""
        return cls(type="node", data={"id": str(id_)})

    @classmethod
    def node_custom(
        cls, user_id: int, nickname, content: "OneBot11Message"
    ) -> "OneBot11MessageSegment":
        """合并转发自定义节点"""
        return cls(
            type="node",
            data={
                "user_id": str(user_id),
                "nickname": str(nickname),
                "content": content,
            },
        )

    @classmethod
    def xml_message(cls, data: str) -> "OneBot11MessageSegment":
        """XML 消息"""
        return cls(type="xml", data={"data": data})

    @classmethod
    def json_message(cls, data: str) -> "OneBot11MessageSegment":
        """JSON 消息"""
        return cls(type="json", data={"data": data})


def escape(s: str, *, escape_comma: bool = True) -> str:
    """对 CQ 码中的特殊字符进行转义。

    Args:
        s: 待转义的字符串。
        escape_comma: 是否转义 `,`。

    Returns:
        转义后的字符串。
    """
    s = s.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
    if escape_comma:
        s = s.replace(",", "&#44;")
    return s
