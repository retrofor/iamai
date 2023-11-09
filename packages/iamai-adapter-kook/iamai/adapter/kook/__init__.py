"""Kook 协议适配器。

本适配器适配了 Kook 协议。
协议详情请参考: [Kook 开发者平台](https://developer.kookapp.cn/) 。
"""
import re
import sys
import json
import time
import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any, Dict, Literal, Mapping, Optional

import aiohttp
import requests
from pydantic import parse_obj_as

from iamai.adapter.utils import WebSocketAdapter
from iamai.log import logger, error_or_exception

from .config import Config
from .message import MessageDeserializer, rev_msg_type_map
from .api.handle import User, get_api_method, get_api_restype
from .exceptions import (
    ApiTimeout,
    TokenError,
    ActionFailed,
    NetworkError,
    ReconnectError,
    ApiNotAvailable,
)
from .event import (
    KookEvent,
    EventTypes,
    OriginEvent,
    ResultStore,
    SignalTypes,
    _kook_events,
    get_event_class,
)

if TYPE_CHECKING:
    from .message import T_KookMSG

__all__ = ["KookAdapter"]


class KookAdapter(WebSocketAdapter[KookEvent, Config]):
    """Kook 协议适配器。"""

    name: str = "kook"
    Config = Config
    _gateway_response: dict = {}
    api_root = "https://www.kookapp.cn/api/v3/"
    _api_response: Dict[Any, Any]
    _api_response_cond: asyncio.Condition = None  # type: ignore
    _api_id: int = 0

    def __getattr__(self, item):  # type: ignore
        return partial(self.call_api, item)

    async def startup(self):
        """初始化适配器。"""
        self.adapter_type = self.config.adapter_type  # type: ignore
        if self.adapter_type == "websocket":  # type: ignore
            self.adapter_type = "ws"  # type: ignore
        if self.adapter_type == "webhook":  # type: ignore
            self.adapter_type = "wb"  # type: ignore
        self.bot.global_state["kook"] = {}
        self.reconnect_interval = self.config.reconnect_interval  # type: ignore
        self._api_response_cond = asyncio.Condition()
        await super().startup()

    async def websocket_connect(self):
        """创建正向 WebSocket 连接。"""

        logger.info("Trying to GET the GateWay...")
        url = f"{self.api_root}gateway/index"
        headers = {
            "Authorization": f"Bot {self.config.access_token}",  # type: ignore
        }
        try:
            self._gateway_response = requests.get(url, headers=headers).json()
            logger.success("GateWay GET success!")
            self.bot.global_state["kook"]["bot_info"] = await self._get_self_data(self.config.access_token)  # type: ignore
            self.self_id = self.bot.global_state["kook"]["bot_info"].id_
        except Exception as e:
            logger.error(f"GateWay GET failed!\n{e}")

        logger.info("Trying to connect to WebSocket server...")

        async with self.session.ws_connect(
            self._gateway_response["data"]["url"].replace("compress=1", "compress=0")
            if self.config.compress == 0  # type: ignore
            else self._gateway_response["data"]["url"]  # type: ignore
        ) as self.websocket:
            await self.handle_websocket()

    async def handle_websocket_msg(self, msg: aiohttp.WSMessage):
        """处理 WebSocket 消息。"""
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                msg_dict = msg.json()
            except json.JSONDecodeError as e:
                error_or_exception(
                    "WebSocket message parsing error, not json:",
                    e,
                    self.bot.config.bot.log.verbose_exception,
                )
                return

            if msg_dict.get("s") == SignalTypes.HELLO:
                data = msg_dict.get("d")
                if data.get("code") == 0:
                    try:
                        data["post_type"] = "meta_event"
                        data["sub_type"] = "connect"
                        data["meta_event_type"] = "lifecycle"
                        logger.success(
                            f"WebSocket connection verified, "
                            f"Session key: {data.get('session_id')[:7]}"
                        )
                        # 调用 start_heartbeat 间隔30(+5,-5)发送心跳
                        self.bot.global_state["kook"]["session"] = data.get(
                            "session_id"
                        )
                        ResultStore.set_sn(self.bot.global_state["kook"]["session"], 0)
                        asyncio.ensure_future(
                            self.start_heartbeat(
                                self.bot.global_state["kook"]["session"]
                            )
                        )
                        logger.debug("HeartBeat task started!")
                        await self.handle_kook_event(data)
                    except Exception as e:
                        logger.error(f"WebSocket connection verified failed!\n{e}")
                        raise ReconnectError
                elif data.get("code") == 40103:
                    raise ReconnectError
                elif data.get("code") == 40101:
                    raise TokenError("无效的 token")
                elif data.get("code") == 40102:
                    raise TokenError("token 验证失败")
                else:
                    logger.warning(
                        f"Websocket connection failed with code {msg_dict.get('d').get('code') or msg_dict}, "
                        f"retrying..."
                    )
                    await asyncio.sleep(self.reconnect_interval)  # type: ignore
            elif msg_dict.get("s") == SignalTypes.PONG:
                data = {
                    "self_id": self.self_id,
                    "post_type": "meta_event",
                    "meta_event_type": "heartbeat",
                }
                logger.info(f"HeartBeat received!{data}")
                logger.warning(
                    f"Bot {self.bot.global_state['kook']['bot_info'].username} HeartBeat",
                )
                await self.handle_kook_event(data)
            elif msg_dict.get("s") == SignalTypes.EVENT:
                ResultStore.set_sn(
                    self.bot.global_state["kook"]["session"], msg_dict["sn"]
                )
                try:
                    data = msg_dict.get("d")
                    extra = data.get("extra")
                    logger.info(f"\n{data}")
                    data["self_id"] = self.self_id
                    data["group_id"] = (
                        data.get("target_id")
                        if data.get("channel_type") == "GROUP"
                        else None
                    )
                    data["time"] = data.get("msg_timestamp")
                    data["user_id"] = (
                        data.get("author_id")
                        if data.get("author_id") != "1"
                        else "SYSTEM"
                    )
                    content = MessageDeserializer(
                        data["type"],
                        data,
                    ).deserialize()

                    if data["type"] == EventTypes.sys:
                        data["post_type"] = "notice"
                        data["message"] = content
                        data["notice_type"] = data.get("channel_type").lower()
                        data["notice_type"] = (
                            "private"
                            if data["notice_type"] == "person"
                            else data["notice_type"]
                        )
                    else:
                        data["post_type"] = "message"
                        data["sub_type"] = [
                            i.name.lower()
                            for i in EventTypes
                            if i.value == extra.get("type")
                        ][0]
                        data["message_type"] = data.get("channel_type").lower()
                        data["message_type"] = (
                            "private"
                            if data["message_type"] == "person"
                            else data["message_type"]
                        )
                        data["raw_message"] = data.get("content")
                        data["message"] = content
                        # data['type'] = rev_msg_type_map.get(data['type'], "")
                        data["extra"]["content"] = content
                        data["event"] = data["extra"]

                    data["type"] = extra.get("type")
                    logger.debug(data)
                    data["message_id"] = data.get("msg_id")
                    await self.handle_kook_event(data)
                except Exception as e:
                    logger.error(f"Event handle failed!\n{e!r}")
            elif msg_dict.get("s") == SignalTypes.RECONNECT:
                raise ReconnectError
            elif msg_dict.get("s") == SignalTypes.RESUME_ACK:
                return
            else:
                async with self._api_response_cond:
                    self._api_response = msg_dict
                    self._api_response_cond.notify_all()

        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(
                f"WebSocket connection closed "
                f"with exception {self.websocket.exception()!r}"
            )

    async def handle_kook_event(self, data: Dict[str, Any]):
        """处理 kook 事件。

        Args:
            msg: 接收到的信息。
        """
        post_type = data.get("post_type")
        event_type = data.get(f"{post_type}_type")
        sub_type = data.get("sub_type")
        event_class = get_event_class(post_type, event_type, sub_type)  # type: ignore

        kook_event = event_class(adapter=self, **data)
        # 便于检查事件类型
        if self.config.show_raw:  # type: ignore
            logger.debug(data)

        if kook_event.post_type == "meta_event":
            # meta_event 不交由插件处理
            if (
                kook_event.meta_event_type == "lifecycle"
                and kook_event.sub_type == "connect"
            ):
                logger.success(
                    f"WebSocket connection "
                    f"from Kook Bot {self.bot.global_state['kook']['bot_info'].username} accepted!"
                )
        else:
            # 屏蔽bot自身消息
            if not self.config.report_self_message:  # type: ignore
                if kook_event.user_id == kook_event.self_id:
                    return
            await self.handle_event(kook_event)

    async def call_api(self, api: str, **data: dict) -> Any:
        match = re.findall(r"[A-Z]", api)
        if len(match) > 0:
            for m in match:
                api = api.replace(m, f"-{m.lower()}")
        api = api.replace("_", "/")

        if api.startswith("/api/v3/"):
            api = api[len("/api/v3/") :]
        elif api.startswith("api/v3"):
            api = api[len("api/v3") :]
        api = api.strip("/")
        return await self._call_api(api, data, self.config.access_token)  # type: ignore

    async def _call_api(
        self,
        api: str,
        data: Optional[Mapping[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Any:
        data = dict(data) if data is not None else {}

        # 判断 POST 或 GET
        method = get_api_method(api) if not data.get("method") else data.get("method")
        headers = data.get("headers", {})

        files = None
        query = None
        body = None

        if "files" in data:
            files = data["files"]
            del data["files"]
        elif "file" in data:  # 目前只有asset/create接口需要上传文件（大概）
            files = {"file": data["file"]}
            del data["file"]

        if method == "GET":
            query = data
        elif method == "POST":
            body = data

        if token is not None:
            headers["Authorization"] = f"Bot {self.config.access_token}"  # type: ignore

        result_type = get_api_restype(api)
        try:
            resp = requests.request(
                method=method,  # type: ignore
                url=self.api_root + api,
                headers=headers,
                params=query,
                data=body,
                files=files,
                timeout=self.config.api_timeout,  # type: ignore
            )
            result = _handle_api_result(resp)
            logger.debug(f"API {api} called with result {result}")
            return parse_obj_as(result_type, result) if result_type else None
        except Exception as e:
            raise e

    async def _get_self_data(self, token: str) -> User:
        """获取当前机器人的信息。

        Returns:
            Optional[dict]: 当前机器人的信息。
        """
        return await self._call_api("user/me", token=self.config.access_token)  # type: ignore

    async def start_heartbeat(self, session: str) -> None:
        """
        每30s一次心跳
        :return:
        """
        while not self.bot.should_exit.is_set():
            if self.websocket.closed:
                break
            await self.websocket.send_json(
                json.dumps(
                    {"s": 2, "sn": ResultStore.get_sn(session)}  # 客户端目前收到的最新的消息 sn
                )
            )
            logger.debug(f"HeartBeat sent {ResultStore.get_sn(session)} times!")
            await asyncio.sleep(26)

    async def send(
        self, message_: "T_KookMSG", message_type: Literal["GROUP", "PERSON"], id_: int
    ) -> Dict[str, Any]:
        """发送消息，调用 message/create 或 direct-message/create API 发送消息。

        Args:
            message_: 消息内容，可以是 str, Mapping, Iterable[Mapping],
                'KookMessageSegment', 'KookMessage'。
                将使用 `KookMessage` 进行封装。
            message_type: 消息类型。应该是 GROUP 或者 PERSON。
            id_: 发送对象的 ID ，Kook 用户码或者Kook频道码。

        Returns:
            API 响应。

        Raises:
            TypeError: message_type 不是 'PERSON' 或 'GROUP'。
            ...: 同 `call_api()` 方法。
        """
        if message_type == "PERSON":
            return await self.call_api(
                api="direct-message/create", target_id=id_, content=message_  # type: ignore
            )
        elif message_type == "GROUP":
            return await self.call_api(
                api="message/create", target_id=id_, content=message_  # type: ignore
            )
        else:
            raise TypeError('message_type must be "PERSON" or "GROUP"')


def _handle_api_result(response: Any) -> Any:
    """
    :说明:

      处理 API 请求返回值。

    :参数:

      * ``response: Response``: API 响应体

    :返回:

        - ``T``: API 调用返回数据

    :异常:

        - ``ActionFailed``: API 调用失败
    """
    result = json.loads(response.content)
    if isinstance(result, dict):
        if result.get("code") != 0:
            raise ActionFailed(response)
        else:
            return result.get("data")
