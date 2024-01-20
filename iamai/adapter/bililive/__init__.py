"""bililive 协议适配器。

本适配器适配了 bililive 协议。
协议详情请参考: [xfgryujk/blivedm](https://github.com/xfgryujk/blivedm) 。

TODO:
    - [x] 扫码登录
    - [x] 本地缓存cookie登录
    - [ ] onebot 适配
    - [ ] api
"""
import os
import re
import sys
import json
import time
import zlib
import struct
import asyncio
from math import log
from functools import partial
from abc import abstractmethod
from collections import namedtuple
from os.path import join, split, abspath, dirname
from typing import TYPE_CHECKING, Any, Dict, NamedTuple

import qrcode
import aiohttp
from genericpath import exists
from aiohttp.client import ClientSession

from iamai.utils import DataclassEncoder
from iamai.adapter.utils import WebSocketAdapter
from iamai.log import logger, error_or_exception

from .event import *
from .message import *
from .config import Config
from .event import get_event_class

if TYPE_CHECKING:
    from .message import T_BililiveMSG

__all__ = ["BililiveAdapter"]

ROOM_INIT_URL = "https://api.live.bilibili.com/xlive/web-room/v1/index/getInfoByRoom"
DANMAKU_SERVER_CONF_URL = (
    "https://api.live.bilibili.com/xlive/web-room/v1/index/getDanmuInfo"
)
DEFAULT_DANMAKU_SERVER_LIST = [
    {
        "host": "broadcastlv.chat.bilibili.com",
        "port": 2243,
        "wss_port": 443,
        "ws_port": 2244,
    }
]
QRCODE_REQUEST_URL = "http://passport.bilibili.com/qrcode/getLoginUrl"
CHECK_LOGIN_RESULT = "http://passport.bilibili.com/qrcode/getLoginInfo"
SEND_URL = "https://api.live.bilibili.com/msg/send"
MUTE_USER_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/AddSilentUser"
)
ROOM_SLIENT_URL = "https://api.live.bilibili.com/xlive/web-room/v1/banned/RoomSilent"
ADD_BADWORD_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/AddShieldKeyword"
)
DEL_BADWORD_URL = (
    "https://api.live.bilibili.com/xlive/web-ucenter/v1/banned/DelShieldKeyword"
)
HEADER_STRUCT = struct.Struct(">I2H2I")
HeaderTuple = namedtuple(
    "HeaderTuple", ("pack_len", "raw_header_size", "ver", "operation", "seq_id")
)
WS_BODY_PROTOCOL_VERSION_INFLATE = 0
WS_BODY_PROTOCOL_VERSION_NORMAL = 1
WS_BODY_PROTOCOL_VERSION_DEFLATE = 2

user_cookies = aiohttp.cookiejar.CookieJar()


class BililiveAdapter(WebSocketAdapter[BililiveEvent, Config]):
    """bililive 协议适配器。"""

    name: str = "bililive"
    Config = Config
    _gateway_response = {}  # type: ignore
    _host_server_list = DEFAULT_DANMAKU_SERVER_LIST
    _api_response: Dict[Any, Any]
    _api_response_cond: asyncio.Condition = None  # type: ignore
    _api_id: int = 0
    _heartbeat_interval = 30
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
        self.session_data_path = self.config.session_data_path  # type: ignore
        self._api_response_cond = asyncio.Condition()
        self.jct: str = ""
        self.cookies = {}
        _path = f"{dirname(abspath(sys.argv[0]))}/{self.session_data_path}"
        if not os.path.exists(_path):
            os.mkdir(dirname(_path))
        if exists(_path):
            with open(_path) as f:
                self.cookies = json.load(f)
        user_cookies.update_cookies(self.cookies)
        if self.config.login:  # type: ignore
            logger.debug(f"Login enabled!")
            try:
                # 尝试登陆
                async with ClientSession(cookie_jar=user_cookies) as self.session:
                    success = await login(self.session)

                    if success:
                        self._uid = get_cookies("DedeUserID")
                        self.jct = get_cookies("bili_jct")

                        if self._uid == None or self.jct == None:
                            logger.error(
                                f"Unable to get cookies, please check your cookies."
                            )
                            return
                        if not exists(_path):
                            for cookie in user_cookies:
                                self.cookies[cookie.key] = cookie.value

                            logger.debug(f"Stored cookies: {self.cookies}")
                            with open(_path, mode="w") as f:
                                json.dump(self.cookies, f)

                        await super().startup()
            except Exception as e:
                logger.error(e)
                return
        else:
            logger.debug(f"Login disabled!")
            await super().startup()

    async def websocket_connect(self):
        """创建正向 WebSocket 连接。"""

        logger.info("Trying to connect to WebSocket server...")
        host_server = self._host_server_list[
            self._retry_count % len(self._host_server_list)
        ]
        try:
            async with self.session.ws_connect(
                f'wss://{host_server["host"]}:{host_server["wss_port"]}/sub',
                receive_timeout=self._heartbeat_interval + 5,
            ) as self.websocket:
                await self._send_auth()
                self._heartbeat_timer_handle = asyncio.ensure_future(
                    self._start_heartbeat()
                )
                logger.success(f"Success to be invited to room {self.room_id}.")
                await self.handle_websocket()
        except Exception as e:
            logger.error(e)
            self._retry_count += 1
            await asyncio.sleep(self.reconnect_interval)
            await self.websocket_connect()

    async def handle_websocket_msg(self, msg: aiohttp.WSMessage):
        """处理 WebSocket 消息。"""
        logger.info(msg)
        if msg.type == aiohttp.WSMsgType.BINARY:
            try:
                data = msg.data  # await self.websocket.receive_bytes()
                logger.info(data)
                offset = 0
                while offset < len(data):
                    try:
                        header = HeaderTuple(*HEADER_STRUCT.unpack_from(data, offset))
                    except struct.error:
                        break
                    if header.operation == Operation.HEARTBEAT_REPLY:
                        popularity = int.from_bytes(
                            data[
                                offset
                                + HEADER_STRUCT.size : offset
                                + HEADER_STRUCT.size
                                + 4
                            ],
                            "big",
                        )
                        await self._on_receive_popularity(popularity)
                    elif header.operation == Operation.SEND_MSG_REPLY:
                        body = data[
                            offset + HEADER_STRUCT.size : offset + header.pack_len
                        ]
                        if header.ver == WS_BODY_PROTOCOL_VERSION_DEFLATE:
                            self._loop = asyncio.get_event_loop()
                            body = await self._loop.run_in_executor(
                                None, zlib.decompress, body
                            )
                            # await self.handle_websocket_msg(body)
                            return
                        else:
                            try:
                                body = json.loads(body.decode("utf-8"))
                                data = body
                                logger.info(data)
                                data["post_type"] = data["cmd"].lower().split("_")[0]
                                data["message"] = data.get("msg_common") or ""
                                data["message_id"] = data.get("msg_id") or 0
                                data["group_id"] = data.get("roomid") or 0
                                data["time"] = data.get("send_time") or 0
                                await self.handle_bililive_event(data)  # type: ignore
                            except Exception:
                                logger.debug(f"body: {body}")
                                raise

                    elif header.operation == Operation.AUTH_REPLY:
                        await self.websocket.send_bytes(
                            self._make_packet({}, Operation.HEARTBEAT)
                        )

                    else:
                        body = data[
                            offset + HEADER_STRUCT.size : offset + header.pack_len
                        ]
                        logger.warning(
                            f"room {self.room_id,} 未知包类型：operation={header.operation, header, body}"
                        )

                    offset += header.pack_len
            except Exception as e:
                error_or_exception(
                    "WebSocket message parsing error, not BINARY:",
                    e,
                    self.bot.config.bot.log.verbose_exception,
                )
                async with self._api_response_cond:
                    self._api_response = msg.data
                    logger.warning(msg.data)
                    self._api_response_cond.notify_all()
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(
                f"WebSocket connection closed "
                f"with exception {self.websocket.exception()!r}"
            )

    async def handle_bililive_event(self, data: Dict[str, Any]):
        logger.info(str(data))
        post_type = data.get("post_type")
        event_type = data.get(f"{post_type}_type")
        sub_type = data.get("sub_type", None)

        event_class = get_event_class(post_type, event_type, sub_type)
        bililive_event = event_class(adapter=self, **data)

        await self.handle_event(bililive_event)

    # 发送登录包
    async def _send_auth(self):
        auth_params = {
            "uid": self._uid or 0,  # 0: 游客
            "roomid": self.room_id,
            "protover": 2,
            "platform": "web",
            "clientver": "1.14.3",
            "type": 2,
        }
        await self.websocket.send_bytes(self._make_packet(auth_params, Operation.AUTH))

    @staticmethod
    def _make_packet(data, operation):
        body = json.dumps(data).encode("utf-8")
        header = HEADER_STRUCT.pack(
            HEADER_STRUCT.size + len(body), HEADER_STRUCT.size, 1, operation, 1
        )
        return header + body

    async def _start_heartbeat(self) -> None:
        """
        每30s一次心跳
        :return:
        """
        hb = "0000001f0010000100000002000000015b6f626a656374204f626a6563745d"
        try:
            while not self.bot.should_exit.is_set():
                if self.websocket.closed:
                    break
                await self.websocket.send_bytes(bytes.fromhex(hb))
                logger.debug(f"HeartBeat sent!")
                await asyncio.sleep(29)
        except Exception as e:
            logger.error(e)

    async def call_api(self, api: str, **params):
        """调用 bililive API。

        TODO: 因为基于OlivOS的那个OlivaBiliLive插件架构其实相当于一个小框架的缘故,
        所以要改的东西太多了，这里插个保留的接口...
        """

        ...

    async def send_danmu(self, **fields) -> bool:
        token = get_cookies("bili_jct")
        async with ClientSession(cookie_jar=user_cookies) as session:
            try:
                res = await _post(
                    session,
                    SEND_URL,
                    rnd=time.time(),
                    csrf=token,
                    csrf_token=token,
                    **fields,
                )
                return "data" in res
            except Exception as e:
                logger.warning(f"Send danmu failed: {e}")
                return False

    async def send(
        self,
        danmaku: str,
        fontsize: int = 25,
        color: int = 0xFFFFFF,
        pos: DanmakuPosition = DanmakuPosition.NORMAL,
    ) -> bool:
        # don't know what the hell is bubble
        return await self.send_danmu(
            msg=danmaku,
            fontsize=fontsize,
            color=color,
            pos=pos,
            roomid=self.room_id,
            bubble=0,
        )

    @abstractmethod
    async def _on_receive_popularity(self, popularity: int):
        pass


def rawData_to_jsonData(data: bytes):
    packetLen = int(data[:4].hex(), 16)
    ver = int(data[6:8].hex(), 16)
    op = int(data[8:12].hex(), 16)

    if len(data) > packetLen:  # 防止
        rawData_to_jsonData(data[packetLen:])
        data = data[:packetLen]

    if ver == 2:
        data = zlib.decompress(data[16:])
        return rawData_to_jsonData(data)

    if op == 5:
        try:
            jd = json.loads(data[16:].decode("utf-8", errors="ignore"))
            return jd
        except Exception as e:
            pass


async def login(session: ClientSession) -> bool:
    if get_cookies("bili_jct") != None:
        logger.info(f"Aleady login!")
        return True
    try:
        res = await _get(session, QRCODE_REQUEST_URL)
        ts = res["ts"]
        outdated = ts + 180 * 1000  # 180 秒後逾時
        authKey = res["data"]["oauthKey"]
        url = res["data"]["url"]
        qr = qrcode.QRCode()
        logger.info("请扫描下面的二维码进行登录... (或者到目录下寻找 qrcode.png)")
        qr.add_data(url)
        qr.print_ascii(invert=True)
        qr.make_image().save("qrcode.png")
        while True:
            await asyncio.sleep(5)
            if time.time() > outdated:
                logger.warning("Timeout!")
                return False  # 登入失敗
            res = await _post(session, CHECK_LOGIN_RESULT, oauthKey=authKey)
            if res["status"]:
                logger.success("login success!")
                return True
            else:
                code = res["data"]
                if code in [-1, -2]:
                    logger.warning(f'login failed: {res["message"]}')
                    return False
    except Exception as e:
        logger.warning(f"Something went wrong: {e}")
        return False
    finally:
        os.remove("qrcode.png")


def get_cookies(name: str) -> any:  # type: ignore
    for cookie in user_cookies:
        if cookie.key == name:
            return cookie.value
    return None


async def _get(session: ClientSession, url: str):
    async with session.get(url) as resp:
        resp.raise_for_status()
        data = await resp.json()
        logger.debug(data)
        if "code" in data and data["code"] != 0:
            raise Exception(data["message"] if "message" in data else data["code"])
        return data


async def _post(session: ClientSession, url: str, **data):
    form = aiohttp.FormData()
    for k, v in data.items():
        form.add_field(k, v)
    logger.debug(f"Sending POST: {url}, content: {data}")
    async with session.post(url, data=form) as resp:
        resp.raise_for_status()
        data = await resp.json()
        logger.debug(data)
        if "code" in data and data["code"] != 0:
            raise Exception(data["message"] if "message" in data else data["code"])
        return data
