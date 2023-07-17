"""Bililive 适配器事件。"""
import asyncio
import inspect
from enum import IntEnum
from collections import UserDict
from typing import (
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

from .message import Message, BililiveMessage

if TYPE_CHECKING:
    from . import BililiveAdapter
    from .message import T_BililiveMSG

T_BililiveEvent = TypeVar("T_BililiveEvent", bound="BililiveEvent")


# go-common\app\service\main\broadcast\model\operation.go
class Operation(IntEnum):
    HANDSHAKE = 0
    HANDSHAKE_REPLY = 1
    HEARTBEAT = 2
    HEARTBEAT_REPLY = 3
    SEND_MSG = 4
    SEND_MSG_REPLY = 5
    DISCONNECT_REPLY = 6
    AUTH = 7
    AUTH_REPLY = 8
    RAW = 9
    PROTO_READY = 10
    PROTO_FINISH = 11
    CHANGE_ROOM = 12
    CHANGE_ROOM_REPLY = 13
    REGISTER = 14
    REGISTER_REPLY = 15
    UNREGISTER = 16
    UNREGISTER_REPLY = 17
    # B站业务自定义OP
    # MinBusinessOp = 1000
    # MaxBusinessOp = 10000


class BililiveEvent(Event["BililiveAdapter"]):
    """Blilive 适配器事件类。"""

    ...
