"""bililive 协议适配器。

本适配器适配了 bililive 协议。
协议详情请参考: [xfgryujk/blivedm](https://github.com/xfgryujk/blivedm) 。
"""
import re
import sys
import json
import time
import asyncio
from genericpath import exists
from aiohttp.client import ClientSession
import json
from .utils.bilibili_bot import BiliLiveBot
from .utils.file_loader import load_default_config, make_folder
from .utils.plugins_loader import load_plugins
from .utils.bilibili_api import get_cookies, login, user_cookies
from functools import partial
from typing import TYPE_CHECKING, Any, Dict
from collections import namedtuple
import ssl as ssl_
import aiohttp

from iamai.utils import DataclassEncoder
from iamai.adapter.utils import WebSocketAdapter
from iamai.log import logger, error_or_exception

from .config import Config
import struct

from .event import *
from .message import *
# from .api.blivedm import BLiveClient

if TYPE_CHECKING:
    from .message import T_BililiveMSG

__all__ = ["BililiveAdapter"]
ROOM_INIT_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom'
DANMAKU_SERVER_CONF_URL = 'https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo'
DEFAULT_DANMAKU_SERVER_LIST = [
    {'host': 'broadcastlv.chat.bilibili.com', 'port': 2243, 'wss_port': 443, 'ws_port': 2244}
]

HEADER_STRUCT = struct.Struct('>I2H2I')
HeaderTuple = namedtuple('HeaderTuple', ('pack_len', 'raw_header_size', 'ver', 'operation', 'seq_id'))
WS_BODY_PROTOCOL_VERSION_INFLATE = 0
WS_BODY_PROTOCOL_VERSION_NORMAL = 1
WS_BODY_PROTOCOL_VERSION_DEFLATE = 2


class BililiveAdapter(WebSocketAdapter[BililiveEvent, Config]):
    """bililive 协议适配器。"""

    name: str = "bililive"
    Config = Config
    _gateway_response = {}  # type: ignore

    _api_response: Dict[Any, Any]
    _api_response_cond: asyncio.Condition = None  # type: ignore
    _api_id: int = 0
    _heartbeat_interval = 30
    _host_server_list = DEFAULT_DANMAKU_SERVER_LIST
    _retry_count = 0
    
    
    def __getattr__(self, item):  # type: ignore
        return partial(self.call_api, item)

    async def startup(self):
        """初始化适配器。"""
        self.adapter_type = self.config.adapter_type  # type: ignore
        if self.adapter_type == "websocket":  # type: ignore
            self.adapter_type = "ws"  # type: ignore
        self.reconnect_interval = self.config.reconnect_interval  # type: ignore
        self.room_id = self.config.room_id  # type: ignore
        self.bad_danmaku = self.config.bad_danmaku  # type: ignore
        self.session_data_path = self.config.session_data_path # type: ignore
        self._api_response_cond = asyncio.Condition()
        self._ssl = self.config.ssl if self.config.ssl else ssl_._create_unverified_context() # type: ignore
        await super().startup()

    async def websocket_connect(self):
        """创建正向 WebSocket 连接。"""
        
        logger.info("Trying to connect to WebSocket server...")
        # 连接
        host_server = self._host_server_list[self._retry_count % len(self._host_server_list)]
        try:
            async with self.session.ws_connect(
                f'wss://{host_server["host"]}:{host_server["wss_port"]}/sub',
                receive_timeout=self._heartbeat_interval + 5,
                ssl=self._ssl
            ) as self.websocket:
                await self.handle_websocket()
        except Exception as e:
            logger.error(e)
            self._retry_count += 1
            await asyncio.sleep(self.reconnect_interval)
            await self.websocket_connect()

    async def call_api(self, api: str, **params):
        """调用 bililive API。
        
        TODO: 因为基于OlivOS的那个OlivaBiliLive插件架构其实相当于一个小框架的缘故,
        所以要改的东西太多了，这里插个保留的接口...
        """
        
        ...
    
    async def _call_api(self):
        ...
        
    async def send(self, **params: Any) -> None:
        """发送消息。"""
        await self.call_api("send_msg", **params)