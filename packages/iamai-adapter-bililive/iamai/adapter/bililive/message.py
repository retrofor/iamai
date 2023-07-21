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


class BililiveMessageSegment(MessageSegment["BililiveMessage"]):
    @property
    def _message_class(cls) -> Type["BililiveMessage"]:
        return BililiveMessage


class BililiveMessage(Message[MessageSegment]):
    @property
    def _message_segment_class(self) -> Type["BililiveMessageSegment"]:
        return BililiveMessageSegment
