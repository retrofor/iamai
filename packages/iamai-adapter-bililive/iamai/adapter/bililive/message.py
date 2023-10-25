"""Bililive 适配器消息。"""
import json
from io import StringIO
from dataclasses import dataclass
from typing_extensions import deprecated
from typing import Any, Dict, Type, Tuple, Union, Mapping, Iterable, Optional, cast

from iamai.message import Message, MessageSegment

from .exceptions import *

__all__ = ["T_BililiveMSG", "BililiveMessage", "BililiveMessageSegment"]

T_BililiveMSG = Union[
    str, Mapping, Iterable[Mapping], "BililiveMessageSegment", "BililiveMessage"
]


class BililiveMessage(Message["BililiveMessageSegment"]):
    @property
    def _message_segment_class(self) -> Type["BililiveMessageSegment"]:
        return BililiveMessageSegment

    def _str_to_message_segment(self, msg: str) -> "BililiveMessageSegment":
        return BililiveMessageSegment.danmu(msg)


class BililiveMessageSegment(MessageSegment["BililiveMessage"]):
    @property
    def _message_class(cls) -> Type["BililiveMessage"]:
        return BililiveMessage

    def __str__(self) -> str:
        return self.data.get("danmu", "")

    @classmethod
    def danmu(cls, msg: str) -> "BililiveMessageSegment":
        return cls(type="danmu", data={"danmu": msg})
