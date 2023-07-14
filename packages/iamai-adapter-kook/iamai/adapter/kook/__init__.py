"""Kook 协议适配器。

本适配器适配了 Kook 协议。
协议详情请参考: [Kook 开发者平台](https://developer.kookapp.cn/) 。
"""
import sys
import json
import time
import asyncio
from functools import partial
from typing import TYPE_CHECKING, Any, Dict, Literal

import aiohttp,requests

from iamai.utils import DataclassEncoder
from iamai.adapter.utils import WebSocketAdapter
from iamai.log import logger, error_or_exception

from .config import Config
from .message import KookMessage
from .event import KookEvent, get_event_class, EventTypes, SignalTypes, ResultStore
from .exceptions import ApiTimeout, ActionFailed, NetworkError, ApiNotAvailable, TokenError, ReconnectError

if TYPE_CHECKING:
    from .message import T_KookMSG

__all__ = ["KookAdapter"]


class KookAdapter(WebSocketAdapter[KookEvent, Config]):
    """Kook 协议适配器。"""

    name = "kook"
    Config = Config
    _gateway_response = {} # type: ignore
    
    _api_response: Dict[Any, Any]
    _api_response_cond: asyncio.Condition = None # type: ignore
    _api_id: int = 0

    def __getattr__(self, item): # type: ignore
        return partial(self.call_api, item)

    async def startup(self):
        """初始化适配器。"""
        self.adapter_type = self.config.adapter_type # type: ignore
        if self.adapter_type == "websocket": # type: ignore
            self.adapter_type = "ws" # type: ignore
        if self.adapter_type == "webhook": # type: ignore
            self.adapter_type = "wb" # type: ignore
        self.reconnect_interval = self.config.reconnect_interval # type: ignore
        self._api_response_cond = asyncio.Condition() 
        await super().startup()
                
    async def websocket_connect(self):
        """创建正向 WebSocket 连接。"""
        
        logger.info("Trying to GET the GateWay...")
        url = "https://www.kookapp.cn/api/v3/gateway/index"
        headers = {
            "Authorization": f"Bot {self.config.access_token}", # type: ignore
        }
        try:
            self._gateway_response = requests.get(url, headers=headers).json()
            logger.success(f"GateWay GET success!")
        except Exception as e:
            logger.error(f"GateWay GET failed!\n{e}")
            
        logger.info("Trying to connect to WebSocket server...")
        
        async with self.session.ws_connect(
            self._gateway_response['data']['url'].replace("compress=1","compress=0") \
            if self.config.compress == 0 else self._gateway_response['data']['url'] # type: ignore
            ) as self.websocket:
            await self.handle_websocket()
    
    async def handle_websocket_msg(self, msg: aiohttp.WSMessage):
        """处理 WebSocket 消息。"""
        if msg.type == aiohttp.WSMsgType.TEXT:
            try:
                msg_dict = msg.json()
                logger.info(msg_dict)
            except json.JSONDecodeError as e:
                error_or_exception(
                    "WebSocket message parsing error, not json:",
                    e,
                    self.bot.config.bot.log.verbose_exception,
                )
                return
            
            if msg_dict.get('s') == SignalTypes.HELLO:
                if msg_dict.get('d').get("code") == 0:
                    data = msg_dict.get('d')
                    data["post_type"] = "meta_event"
                    data["sub_type"] = 'connect'
                    data["meta_event_type"] = "lifecycle"
                    logger.success(
                        f"WebSocket connection verified, "
                        f"Session key: {data.get('session_id')}"
                    )
                    # await self.handle_kook_event(data)
                    # 调用 start_heartbeat 间隔30(+5,-5)发送心跳 TO-DO
                    self.bot.global_state['session'] = data.get('session_id')
                    ResultStore.set_sn(self.bot.global_state['session'], 0)
                    heartbeat_task = asyncio.ensure_future(self.start_heartbeat(self.bot.global_state['session']))
                    logger.info("HeartBeat task started!")
                elif msg_dict.get('d').get("code") == 40103:
                    raise ReconnectError
                elif msg_dict.get('d').get("code") == 40101:
                    raise TokenError("无效的 token")
                elif msg_dict.get('d').get("code") == 40102:
                    raise TokenError("token 验证失败")
                else:
                    logger.warning(
                        f"Websocket connection failed with code {msg_dict.get('d').get('code') or msg_dict}, "
                        f"retrying..."
                    )
                    await asyncio.sleep(self.config.reconnect_interval) # type: ignore
            elif msg_dict.get('s') == SignalTypes.PONG:
                data = dict()
                data["post_type"] = "meta_event"
                data["meta_event_type"] = "heartbeat"
                logger.warning(
                    f"Bot {self.bot.global_state['session']} HeartBeat",
                )
            elif msg_dict.get('s') == SignalTypes.EVENT:
                ResultStore.set_sn(self.bot.global_state['session'], msg_dict["sn"])
                data = msg_dict.get('d')
                extra = data.get("extra")
                data['self_id'] = data.get('self_id')
                data['group_id'] = data.get('target_id')
                data['time'] = data.get('msg_timestamp')
                data['user_id'] = data.get('author_id') if data.get('author_id') != "1" else "SYSTEM"

                if data['type'] == EventTypes.sys:
                    data['post_type'] = "notice"
                    data['notice_type'] = extra.get('type')
                    message = KookMessage(("{}").format(data["content"]))
                    data['message'] = message
                    data['notice_type'] = data.get('channel_type').lower()
                    data['notice_type'] = 'private' if data['notice_type'] == 'person' else data['notice_type']
                else:
                    data['post_type'] = "message"
                    data['sub_type'] = [i.name.lower() for i in EventTypes if i.value == extra.get('type')][0]
                    data['message_type'] = data.get('channel_type').lower()
                    data['message_type'] = 'private' if data['message_type'] == 'person' else data['message_type']
                    data['extra']['content'] = data.get('content')
                    data['event'] = data['extra']

                data['message_id'] = data.get('msg_id')
                await self.handle_kook_event(data)
            elif msg_dict.get('s') == SignalTypes.RECONNECT:
                raise ReconnectError
            elif msg_dict.get('s') == SignalTypes.RESUME_ACK:
                # 不存在的signal，resume是不可能resume的，这辈子都不会resume的，出了问题直接重连
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
        """处理 Kook 事件。

        Args:
            msg: 接收到的信息。
        """
        post_type = data.get("post_type")
        event_type = data.get(f"{post_type}_type")
        sub_type = data.get('sub_type')
        logger.info(f"Received event: {data}")
        event_class = get_event_class(post_type, event_type, sub_type)
        kook_event = event_class(adatper=self,**data)
        
        # 便于检查事件类型
        if self.config.show_raw: # type: ignore
            logger.info(data)

        if kook_event.post_type == "meta_event":
            # meta_event 不交由插件处理
            if (
                kook_event.meta_event_type == "lifecycle"
                and kook_event.sub_type == "connect"
            ):
                logger.success(
                    f"WebSocket connection "
                    f"from Kook Bot {data.get('self_id')} accepted!"
                )
            # elif kook_event.meta_event_type == "heartbeat":
            #     if kook_event.status.good and kook_event.status.online:
            #         pass
            #     else:
            #         logger.error(
            #             f"Kook Bot status is not good: {kook_event.status.dict()}"
            #         )
        else:
            await self.handle_event(kook_event)
    
    async def start_heartbeat(self, session) -> None:
        """
        每30s一次心跳
        :return:
        """
        while not self.bot.should_exit.is_set():
            if self.websocket.closed:
                break
            await self.websocket.send_json(json.dumps({
                "s": 2,
                "sn": ResultStore.get_sn(session)  # 客户端目前收到的最新的消息 sn
            }))
            await asyncio.sleep(26)