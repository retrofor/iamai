"""Kook Adapter

This adapter is adapted to the Kook Platform.
For details of the agreement, please refer to: [Kook Developer Platform](https://developer.kookapp.cn/)
"""

import re
import sys  # noqa: F401
import json
import time  # noqa: F401
import zlib
import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any, Dict, Literal, Mapping, Optional

import aiohttp
import requests
from pydantic import parse_obj_as

from iamai.adapter.utils import WebSocketAdapter
from iamai.log import logger, error_or_exception

from .config import Config
from .message import MessageDeserializer, rev_msg_type_map  # noqa: F401
from .api.handle import User, get_api_method, get_api_restype
from .exceptions import (
    ApiTimeout,  # noqa: F401
    TokenError,
    ActionFailed,
    NetworkError,  # noqa: F401
    ReconnectError,
    ApiNotAvailable,  # noqa: F401
)
from .event import (
    KookEvent,
    EventTypes,  # noqa: F401
    OriginEvent,  # noqa: F401
    ResultStore,
    SignalTypes,
    _kook_events,  # noqa: F401
    get_event_class,  # noqa: F401
)

if TYPE_CHECKING:
    from .message import T_KookMSG

__all__ = ["KookAdapter"]

BASE_URL = "https://www.kookapp.cn/api"


class KookAdapter(WebSocketAdapter[KookEvent, Config]):
    """Kook Adapter."""

    name: str = "kook"
    Config = Config

    _gateway_response: dict = {}
    _api_response: Dict[Any, Any]
    _api_response_cond: asyncio.Condition
    _api_id: int = 0

    def __getattr__(self, item):
        return partial(self.call_api, item)

    def get_api_protocol(self, version_number: int | str = 3) -> str:
        """API version management
        KOOK may have different versions of API in the future. You can pass it like ``https://www.kookapp.cn/api/v{version_number}``
        This explicitly specifies the API version to use in the request path. If version_number is omitted, it will point to the default version.

            Specific reference: https://developer.kookapp.cn/doc/reference

        Args:
            version_number (int, optional): version code. Defaults to 3.

        Returns:
            str: KOOK API URL of the corresponding version
        """
        return f"{BASE_URL}/v{version_number}"

    def build_url(self, args) -> str:
        return "/".join(args)

    async def startup(self):
        """Initialize the adapter."""
        self.adapter_type = self.config.adapter_type
        if self.adapter_type == "websocket":
            self.adapter_type = "ws"
        self.bot.global_state["adapter"] = self.bot.global_state.get("adapter", {})
        self.bot.global_state["adapter"]["kook"] = {}
        self.reconnect_interval = self.config.reconnect_interval
        self._api_response_cond = asyncio.Condition()
        await super().startup()

    async def websocket_connect(self) -> None:
        """Create a forward WebSocket connection."""
        logger.info("Trying to GET the GateWay...")
        url = self.build_url([self.get_api_protocol(), "gateway", "index"])
        headers = {
            "Authorization": f"Bot {self.config.access_token}",
        }
        # Get The Gateway URL
        # https://developer.kookapp.cn/doc/http/gateway
        response = requests.get(
            url, headers=headers, params={"compress": self.config.compress}
        )
        if response.status_code == 200:
            logger.success("Successed to get GateWay.")
            self._gateway_response = response.json()
            self.bot.global_state["adapter"]["kook"][
                "bot_info"
            ] = await self._get_self_data(self.config.access_token)
            self.self_id = self.bot.global_state["adapter"]["kook"]["bot_info"].id_
            self.self_name = self.bot.global_state["adapter"]["kook"][
                "bot_info"
            ].username
            logger.success(f"Bot<{self.self_name}> self id: {self.self_id}")
        else:
            logger.error(f"Failed to get GateWay, status_code: {response.status_code}")
            return

        logger.info("Trying to connect to WebSocket server...")

        # start connection
        async with self.session.ws_connect(
            self._gateway_response["data"]["url"]
        ) as self.websocket:
            await self.handle_websocket()

    async def handle_websocket_msg(self, msg: aiohttp.WSMessage):
        """Handle Websocket Message."""
        msg_dict: dict
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                msg_dict = msg.json()
                logger.debug(msg_dict)
            except json.JSONDecodeError as e:
                error_or_exception(
                    "WebSocket message parsing error, not json:",
                    e,
                    self.bot.config.bot.log.verbose_exception,
                )
                return

        elif msg.type == aiohttp.WSMsgType.BINARY:
            try:
                msg_dict: dict = zlib.decompress(msg.data).decode("utf-8")  # type: ignore[dict]
                logger.debug(msg_dict)
            except zlib.error as e:
                error_or_exception(
                    "WebSocket message decoding error, not binary:",
                    e,
                    self.bot.config.bot.log.verbose_exception,
                )
                return

        elif msg.type == aiohttp.WSMsgType.ERROR:
            logger.error(
                f"WebSocket connection closed "
                f"with exception {self.websocket.exception()!r}"  # type: ignore
            )
            return
        else:
            return

        # reveive hello package
        if msg_dict.get("s") == SignalTypes.HELLO:
            data: dict = msg_dict["d"]
            if data.get("code") == 0:
                try:
                    logger.success(
                        f"WebSocket connection verified, "
                        f"Session key: {data['session_id'][:7]}"
                    )
                    # Call start_heartbeat to send heartbeats at intervals of 30 (+5,-5)
                    self.bot.global_state["adapter"]["kook"]["session"] = data.get(
                        "session_id"
                    )
                    ResultStore.set_sn(
                        self.bot.global_state["adapter"]["kook"]["session"], 0
                    )
                    asyncio.ensure_future(
                        self.start_heartbeat(
                            self.bot.global_state["adapter"]["kook"]["session"]
                        )
                    )
                    logger.debug("HeartBeat task started!")
                    await self.handle_kook_event(data)
                except Exception as e:
                    logger.error(f"WebSocket connection verified failed!\n{e}")
                    raise ReconnectError from e
            elif data.get("code") == 40103:
                raise ReconnectError
            elif data.get("code") == 40101:
                raise TokenError("Invalid Token!")
            elif data.get("code") == 40102:
                raise TokenError("Token verification failed")
            else:
                logger.warning(
                    f"Websocket connection failed with code {msg_dict['d'].get('code') or msg_dict}, "
                    f"retrying..."
                )
                await asyncio.sleep(self.reconnect_interval)
        elif msg_dict.get("s") == SignalTypes.PONG:
            data = {
                "self_id": self.self_id,
                "post_type": "meta_event",
                "meta_event_type": "heartbeat",
            }
            logger.info(f"HeartBeat received!{data}")
            logger.info(
                f"Bot {self.bot.global_state['kook']['bot_info'].username} HeartBeat",
            )
            await self.handle_kook_event(data)
        elif msg_dict.get("s") == SignalTypes.EVENT:
            ResultStore.set_sn(self.bot.global_state["kook"]["session"], msg_dict["sn"])
            try:
                data = msg_dict["d"]
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

    async def handle_kook_event(self, data: Dict[str, Any]):
        """Handle kook events.

        Args:
            msg: received message.
        """
        post_type = data.get("type")  # noqa: F841

        kook_event = KookEvent(adapter=self, **data)

        if self.config.show_raw:
            logger.debug(data)

        if kook_event.post_type == "meta_event":
            if (
                kook_event.meta_event_type == "lifecycle"
                and kook_event.sub_type == "connect"
            ):
                logger.success(
                    f"WebSocket connection "
                    f"from Kook Bot {self.bot.global_state['kook']['bot_info'].username} accepted!"
                )
        else:
            if (
                not self.config.report_self_message
                and kook_event.user_id == kook_event.self_id
            ):
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

        method = data.get("method") if data.get("method") else get_api_method(api)
        headers = data.get("headers", {})

        files = None
        query = None
        body = None

        if "files" in data:
            files = data["files"]
            del data["files"]
        elif "file" in data:
            files = {"file": data["file"]}
            del data["file"]

        if method == "GET":
            query = data
        elif method == "POST":
            body = data

        if token is not None:
            headers["Authorization"] = f"Bot {self.config.access_token}"

        result_type = get_api_restype(api)
        try:
            resp = requests.request(
                method=method,
                url=self.build_url([self.get_api_protocol(), api]),
                headers=headers,
                params=query,
                data=body,
                files=files,
                timeout=self.config.api_timeout,
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
        token = token or self.config.access_token
        return await self._call_api("user/me", token=token)

    async def start_heartbeat(self, session: str) -> None:
        """
        每30s一次心跳
        :return:
        """
        while not self.bot.should_exit.is_set() and not self.websocket.closed:
            await self.websocket.send_json(
                json.dumps({"s": 2, "sn": ResultStore.get_sn(session)})
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
                api="direct-message/create", target_id=id_, content=message_
            )
        elif message_type == "GROUP":
            return await self.call_api(
                api="message/create", target_id=id_, content=message_
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
