"""red 适配器消息。"""
import random
from io import BytesIO
from pathlib import Path
from datetime import datetime
from dataclasses import field, dataclass
from typing import TYPE_CHECKING, Type, Union, Literal, Mapping, Iterable, Optional

from iamai.message import Message, MessageSegment

__all__ = ["T_RedMSG", "RedMessage", "RedMessageSegment"]

T_RedMSG = Union[str, Mapping, Iterable[Mapping], "RedMessageSegment", "RedMessage"]


class RedMessage(Message["RedMessageSegment"]):
    """Red 消息"""

    @property
    def _message_segment_class(self) -> Type["RedMessageSegment"]:
        return RedMessageSegment

    def _str_to_message_segment(self, msg: str) -> "RedMessageSegment":
        return RedMessageSegment.text(msg)


class RedMessageSegment(MessageSegment["RedMessage"]):
    @property
    def _message_class(self) -> Type["RedMessage"]:
        return RedMessage

    def __str__(self) -> str:
        shown_data = {k: v for k, v in self.data.items() if not k.startswith("_")}
        return self.data["text"] if self.is_text() else f"[{self.type}: {shown_data}]"

    def is_text(self) -> bool:
        # 判断该消息段是否为纯文本
        return self.type == "text"

    @classmethod
    def text(cls, text: str) -> "RedMessageSegment":
        return cls(type="text", data={"text": text})

    @classmethod
    def at(cls, user_id: str, user_name: Optional[str] = None) -> "RedMessageSegment":
        return cls(type="at", data={"user_id": user_id, "user_name": user_name})

    @classmethod
    def at_all(cls) -> "RedMessageSegment":
        return cls("at_all")

    @classmethod
    def image(cls, file: Union[str, Path, BytesIO, bytes]) -> "RedMessageSegment":
        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            file = file.read_bytes()
        elif isinstance(file, BytesIO):
            file = file.getvalue()
        return cls(type="image", data={"file": file})

    @classmethod
    def file(cls, file: Union[str, Path, BytesIO, bytes]) -> "RedMessageSegment":
        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            file = file.read_bytes()
        elif isinstance(file, BytesIO):
            file = file.getvalue()
        return cls(type="file", data={"file": file})

    @classmethod
    def voice(
        cls, file: Union[str, Path, BytesIO, bytes], duration: int = 1
    ) -> "RedMessageSegment":
        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            file = file.read_bytes()
        elif isinstance(file, BytesIO):
            file = file.getvalue()
        return cls(type="voice", data={"file": file, "duration": duration})

    @classmethod
    def video(cls, file: Union[str, Path, BytesIO, bytes]) -> "RedMessageSegment":
        if isinstance(file, str):
            file = Path(file)
        if isinstance(file, Path):
            file = file.read_bytes()
        elif isinstance(file, BytesIO):
            file = file.getvalue()
        return cls(type="video", data={"file": file})

    @classmethod
    def face(cls, face_id: str) -> "RedMessageSegment":
        return cls(type="face", data={"face_id": face_id})

    @classmethod
    def reply(
        cls,
        message_seq: str,
        message_id: Optional[str] = None,
        sender_uin: Optional[str] = None,
    ) -> "RedMessageSegment":
        return cls(
            type="reply",
            data={
                "msg_id": message_id,
                "msg_seq": message_seq,
                "sender_uin": sender_uin,
            },
        )

    @classmethod
    def ark(cls, data: str) -> "RedMessageSegment":
        return cls(type="ark", data={"data": data})

    @classmethod
    def market_face(
        cls, package_id: str, emoji_id: str, face_name: str, key: str, face_path: str
    ) -> "RedMessageSegment":
        return cls(
            type="market_face",
            data={
                "package_id": package_id,
                "emoji_id": emoji_id,
                "face_name": face_name,
                "key": key,
                "face_path": face_path,
            },
        )

    @classmethod
    def forward(cls, xml: str, id: str, file_name: str) -> "RedMessageSegment":
        return cls(
            type="forward",
            data={"xml": xml, "id": id, "name": file_name},
        )


@dataclass
class ForwardNode:
    uin: str
    name: str
    group: Union[int, str]
    message: Message
    time: datetime = field(default_factory=datetime.now)

    async def export(self, seq: int) -> dict:
        elems = []
        for seg in self.message:
            if seg.type == "text":
                elems.append({"text": {"str": seg.data["text"]}})
            elif seg.type == "at":
                elems.append({"text": {"str": f"@{seg.data['user_id']}"}})
            elif seg.type == "at_all":
                elems.append({"text": {"str": "@全体成员"}})
            elif seg.type == "image":
                resp = await seg.upload()
                md5 = resp.md5
                file = Path(resp.ntFilePath)
                pid = f"{{{md5[:8].upper()}-{md5[8:12].upper()}-{md5[12:16].upper()}-{md5[16:20].upper()}-{md5[20:].upper()}}}{file.suffix}"  # noqa: E501
                elems.append(
                    {
                        "customFace": {
                            "filePath": pid,
                            "fileId": random.randint(0, 65535),
                            "serverIp": -1740138629,
                            "serverPort": 80,
                            "fileType": 1001,
                            "useful": 1,
                            "md5": [int(md5[i : i + 2], 16) for i in range(0, 32, 2)],
                            "imageType": 1001,
                            "width": resp.imageInfo and resp.imageInfo.width,
                            "height": resp.imageInfo and resp.imageInfo.height,
                            "size": resp.fileSize,
                            "origin": 0,
                            "thumbWidth": 0,
                            "thumbHeight": 0,
                            "pbReserve": [2, 0],
                        }
                    }
                )
            else:
                elems.append({"text": {"str": f"[{seg.type}]"}})
        return {
            "head": {
                "field2": self.uin,
                "field8": {
                    "field1": int(self.group),
                    "field4": self.name,
                },
            },
            "content": {
                "field1": 82,
                "field4": random.randint(0, 4294967295),
                "field5": seq,
                "field6": int(self.time.timestamp()),
                "field7": 1,
                "field8": 0,
                "field9": 0,
                "field15": {"field1": 0, "field2": 0},
            },
            "body": {"richText": {"elems": elems}},
        }
