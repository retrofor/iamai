"""Kook Adapter Events"""

import asyncio
import inspect
from enum import IntEnum
from collections import UserDict
from typing import (  # type: ignore
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    Literal,
    TypeVar,
    Optional,
)

from pydantic import Field, HttpUrl, BaseModel, validator, root_validator

from iamai.event import Event

from .api import Role, User, Emoji, Guild, Channel
from .message import KookMessage, MessageDeserializer

if TYPE_CHECKING:
    from . import KookAdapter
    from .message import T_KookMSG

T_KookEvent = TypeVar("T_KookEvent", bound="KookEvent")


class ResultStore:
    _seq = 1
    _futures: Dict[Tuple[str, int], asyncio.Future] = {}
    _sn_map = {}

    @classmethod
    def set_sn(cls, self_id: str, sn: int) -> None:
        cls._sn_map[self_id] = sn

    @classmethod
    def get_sn(cls, self_id: str) -> int:
        return cls._sn_map.get(self_id, 0)


class AttrDict(UserDict):
    def __init__(self, data=None):
        initial = dict(data)  # type: ignore
        for k in initial:
            if isinstance(initial[k], dict):
                initial[k] = AttrDict(initial[k])  # type: ignore

        super().__init__(initial)

    def __getattr__(self, name):
        return self[name]


class EventTypes(IntEnum):
    """
    Main event format
    Kook protocol event, the fields are consistent with Kook. Please refer to `Kook Document` for each event field.

    .. Kook Documentation:
        https://developer.kookapp.cn/doc/event/event-introduction#Main format of events.
    """

    text = 1
    image = 2
    video = 3
    file = 4
    audio = 8
    kmarkdown = 9
    card = 10
    sys = 255


class SignalTypes(IntEnum):
    """
    Signaling type
    Kook protocol signaling, the fields are consistent with Kook. Please refer to `Kook Document` for each event field.

    .. Kook Documentation:
        https://developer.kookapp.cn/doc/websocket#Signaling format.
    """

    EVENT = 0
    HELLO = 1
    PING = 2
    PONG = 3
    RESUME = 4
    RECONNECT = 5
    RESUME_ACK = 6
    SYS = 255


class Extra(BaseModel):
    type_: Union[int, str] = Field(alias="type")
    guild_id: Optional[str]
    channel_name: Optional[str]
    mention: Optional[List[str]]
    mention_all: Optional[bool]
    mention_roles: Optional[List[str]]
    mention_here: Optional[bool]
    author: Optional[User]
    body: Optional[AttrDict]


class OriginEvent(Event["KookAdapter"]):
    """In order to distinguish non-Event events in signaling, the preceding OriginEvent is added."""

    __event__ = ""

    post_type: str


class KookEvent(OriginEvent):
    """
    Event main format, from d field
    Kook protocol event, the fields are consistent with Kook. Please refer to `Kook Document` for each event field.

    .. Kook Documentation:
        https://developer.kookapp.cn/doc/event/event-introduction
    """

    __event__ = ""
    channel_type: Literal["PERSON", "GROUP", "BROADCAST"]
    type_: int = Field(alias="type")
    target_id: str
    author_id: Optional[str] = None
    content: KookMessage
    msg_id: str
    msg_timestamp: int
    nonce: str
    extra: Extra
    user_id: str

    post_type: str


class MessageEvent(KookEvent):
    """Message Events"""

    __event__ = "message"
    post_type: Literal["message"] = "message"
    message_type: str
    sub_type: str
    event: EventMessage

    def __repr__(self) -> str:
        return f'Event<{self.post_type}>: "{self.content}>"'

    def get_plain_text(self) -> str:
        return self.content.get_plain_text()

    async def reply(self, msg: "T_KookMSG"):
        raise NotImplementedError


class PrivateMessageEvent(MessageEvent):
    __event__ = "message.