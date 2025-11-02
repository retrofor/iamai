import json
import asyncio
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.server import WebSocketServerProtocol

from . import Middleware, MiddlewareConfig, MappedObject, ConnectType
from ..logger import get_logger

logger = get_logger(__name__)

ONEBOT11_FIELD_MAPPING = {
    "post_type": "post_type",
    "time": "timestamp",
    "self_id": "self_id",
    "message_type": "message_type",
    "sub_type": "sub_type",
    "message_id": "message_id",
    "user_id": "user_id",
    "message": "message",
    "raw_message": "raw_message",
    "font": "font",
    "sender": "sender",
    "group_id": "group_id",
    "anonymous": "anonymous",
    "notice_type": "notice_type",
    "operator_id": "operator_id",
    "duration": "duration",
    "request_type": "request_type",
    "comment": "comment",
    "flag": "flag",
    "meta_event_type": "meta_event_type",
    "status": "status",
    "interval": "interval",
    "retcode": "retcode",
    "data": "data",
    "echo": "echo",
}


@dataclass
class OneBot11MiddlewareConfig(MiddlewareConfig):
    """OneBot 11 中间件配置"""
    host: str = "127.0.0.1"
    port: int = 3001
    token: str = ""
    middleware_connect_type: ConnectType = "websocket"
    reconnect_interval: int = 3
    max_reconnect_attempts: int = 10
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 10
    field_mapping: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.field_mapping is None:
            self.field_mapping = ONEBOT11_FIELD_MAPPING.copy()


class OneBot11Middleware(Middleware):
    def __init__(self, name: str, config: OneBot11MiddlewareConfig, bot: 'Bot'):
        super().__init__(name, config, bot)
        self.config: OneBot11MiddlewareConfig = config
        self.field_mapping = config.field_mapping
        
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.ws_url = f"ws://{config.host}:{config.port}"
        self.reconnect_attempts = 0
        self.running = False
        
    async def start(self) -> None:
        logger.info(f"启动 OneBot11 中间件: {self.name}")
        self.running = True
        
        if self.connect_type == "websocket":
            await self.connect_ws()
        elif self.connect_type == "reverse_websocket":
            await self.connect_reverse_ws()
        else:
            logger.error(f"不支持的连接类型: {self.connect_type}")
    
    async def stop(self) -> None:
        """停止中间件"""
        logger.info(f"停止 OneBot11 中间件: {self.name}")
        self.running = False
        await self.disconnect()
    
    async def connect_ws(self) -> None:
        """WebSocket 正向连接"""
        logger.info(f"连接到 OneBot11 服务器: {self.ws_url}")
        
        while self.running and self.reconnect_attempts < self.config.max_reconnect_attempts:
            try:
                connect_kwargs = {
                    "ping_interval": self.config.heartbeat_interval,
                    "ping_timeout": self.config.heartbeat_timeout,
                }
                
                if self.config.token:
                    connect_kwargs["extra_headers"] = {
                        "Authorization": f"Bearer {self.config.token}"
                    }
                
                self.websocket = await websockets.connect(
                    self.ws_url,
                    **connect_kwargs
                )
                
                self.connected = True
                self.reconnect_attempts = 0
                logger.info(f"OneBot11 连接成功: {self.ws_url}")
                
                # 监听消息
                await self._listen()
                
            except Exception as e:
                self.connected = False
                self.reconnect_attempts += 1
                logger.error(f"OneBot11 连接失败 (尝试 {self.reconnect_attempts}/{self.config.max_reconnect_attempts}): {e}")
                
                if self.running and self.reconnect_attempts < self.config.max_reconnect_attempts:
                    await asyncio.sleep(self.config.reconnect_interval)
        
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error(f"OneBot11 连接失败，已达到最大重连次数")
    
    async def connect_reverse_ws(self) -> None:
        """WebSocket 反向连接（作为服务器）"""
        logger.info(f"启动 OneBot11 反向 WebSocket 服务器: {self.config.host}:{self.config.port}")
        
        async def handler(websocket: WebSocketServerProtocol, path: str):
            """处理客户端连接"""
            logger.info(f"OneBot11 客户端已连接: {websocket.remote_address}")
            self.websocket = websocket
            self.connected = True
            
            try:
                await self._listen()
            except Exception as e:
                logger.error(f"处理 OneBot11 连接时出错: {e}")
            finally:
                self.connected = False
                logger.info(f"OneBot11 客户端已断开: {websocket.remote_address}")
        
        async with websockets.serve(
            handler,
            self.config.host,
            self.config.port
        ):
            logger.info(f"OneBot11 反向 WebSocket 服务器已启动")
            await asyncio.Future()  # 保持运行
    
    async def _listen(self) -> None:
        """监听 WebSocket 消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"收到非 JSON 消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息时出错: {e}", exc_info=True)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("OneBot11 连接已关闭")
            self.connected = False
    
    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """处理接收到的消息 - 直接打印原始数据"""
        # 打印原始数据字典
        self.print_data(data)
    
    def map_data(self, raw_data: Dict[str, Any]) -> MappedObject:
        """
        映射 OneBot 11 数据（映射器功能）
        
        Args:
            raw_data: OneBot 11 原始数据
            
        Returns:
            映射后的对象
        """
        return MappedObject(raw_data, self.field_mapping)
    
    async def send_message(self, content: str, channel_id: str, **kwargs) -> None:
        """发送消息"""
        if not self.connected or not self.websocket:
            logger.error("OneBot11 未连接，无法发送消息")
            return
        
        # 判断是群聊还是私聊
        message_type = kwargs.get("message_type", "private")
        
        if message_type == "group":
            api_call = self._build_api_call(
                "send_group_msg",
                group_id=int(channel_id),
                message=content
            )
        else:
            api_call = self._build_api_call(
                "send_private_msg",
                user_id=int(channel_id),
                message=content
            )
        
        try:
            await self.websocket.send(json.dumps(api_call))
            logger.debug(f"发送消息: {api_call}")
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
    
    async def call_api(self, action: str, **params) -> Any:
        """调用 OneBot 11 API"""
        if not self.connected or not self.websocket:
            logger.error("OneBot11 未连接，无法调用 API")
            return None
        
        api_call = self._build_api_call(action, **params)
        
        try:
            await self.websocket.send(json.dumps(api_call))
            logger.debug(f"调用 API: {api_call}")
            # TODO: 实现异步等待响应
        except Exception as e:
            logger.error(f"调用 API 失败: {e}")
            return None
    
    def _build_api_call(self, action: str, **params) -> Dict[str, Any]:
        """
        构建 OneBot 11 API 调用请求
        
        Args:
            action: API 动作名称
            **params: API 参数
            
        Returns:
            API 请求数据
        """
        return {
            "action": action,
            "params": params
        }
    
    def parse_message_segments(self, message: Any) -> List[Dict[str, Any]]:
        """
        解析 OneBot 11 消息段
        
        Args:
            message: 消息数据（可能是字符串或数组）
            
        Returns:
            消息段列表
        """
        if isinstance(message, str):
            return [{"type": "text", "data": {"text": message}}]
        elif isinstance(message, list):
            return message
        else:
            return []
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False
