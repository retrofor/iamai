"""
WebSocket中间件模块
"""
import asyncio
import json
from typing import Any, Dict, Optional
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from . import Middleware, register_middleware, MiddlewareConfig
from ..event import Event, MessageEvent
from ..message import Message, WebSocketMessage, MessageBuilder
from ..logger import get_logger
from ..config import WebSocketMiddlewareConfig

logger = get_logger(__name__)

@register_middleware("iamai.middleware.websocket")
class WebSocketMiddleware(Middleware):
    """WebSocket中间件"""
    
    def __init__(self, name: str, config: WebSocketMiddlewareConfig, bot: 'Bot'):
        super().__init__(name, config, bot)
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server: Optional[websockets.WebSocketServer] = None
    
    async def start(self) -> None:
        """启动中间件"""
        if not self.enabled:
            return
        
        logger.info(f"启动WebSocket中间件: {self.name}")
        
        if self.connect_type == "ws":
            await self.connect_ws()
        elif self.connect_type == "reverse_ws":
            await self.connect_reverse_ws()
        else:
            logger.error(f"不支持的连接类型: {self.connect_type}")
    
    async def stop(self) -> None:
        """停止中间件"""
        logger.info(f"停止WebSocket中间件: {self.name}")
        
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        for client in self.clients.values():
            await client.close()
        
        self.connected = False
        logger.info("WebSocket中间件已停止")
    
    async def connect_ws(self) -> None:
        """WebSocket服务器连接"""
        try:
            self.server = await websockets.serve(
                self._handle_client,
                self.config.host,
                self.config.port
            )
            self.connected = True
            logger.info(f"WebSocket服务器已启动: ws://{self.config.host}:{self.config.port}")
        except Exception as e:
            logger.error(f"启动WebSocket服务器失败: {e}")
    
    async def connect_reverse_ws(self) -> None:
        """反向WebSocket连接"""
        try:
            uri = f"ws://{self.config.host}:{self.config.port}{self.config.url}"
            self.websocket = await websockets.connect(uri)
            self.connected = True
            logger.info(f"反向WebSocket已连接: {uri}")
            
            # 启动消息接收任务
            asyncio.create_task(self._receive_messages())
        except Exception as e:
            logger.error(f"反向WebSocket连接失败: {e}")
    
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str) -> None:
        """处理客户端连接"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket
        
        logger.info(f"新客户端连接: {client_id}")
        
        try:
            async for message in websocket:
                await self._process_message(message, client_id)
        except ConnectionClosed:
            logger.info(f"客户端断开连接: {client_id}")
        except Exception as e:
            logger.error(f"处理客户端消息时出错: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
    
    async def _receive_messages(self) -> None:
        """接收消息（反向WebSocket）"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                await self._process_message(message, "server")
        except ConnectionClosed:
            logger.info("反向WebSocket连接已关闭")
            if self.config.auto_reconnect:
                await self._reconnect()
        except Exception as e:
            logger.error(f"接收消息时出错: {e}")
    
    async def _process_message(self, message: str, client_id: str) -> None:
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            
            # 创建消息对象
            ws_message = MessageBuilder.create_websocket_message(
                content=data.get('content', ''),
                user_id=data.get('user_id', client_id),
                channel_id=data.get('channel_id', 'default'),
                session_id=client_id,
                **data.get('fields', {})
            )
            
            # 创建事件
            event = ws_message.to_event()
            
            # 处理事件
            await self.handle_event(event)
            
        except json.JSONDecodeError:
            logger.error(f"无效的JSON消息: {message}")
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
    
    async def send_message(self, content: str, channel_id: str, **kwargs) -> None:
        """发送消息"""
        message_data = {
            'content': content,
            'channel_id': channel_id,
            'timestamp': asyncio.get_event_loop().time(),
            **kwargs
        }
        
        try:
            if self.connect_type == "ws":
                # 服务器模式：发送给所有客户端
                disconnected_clients = []
                for client_id, client in self.clients.items():
                    try:
                        await client.send(json.dumps(message_data))
                    except ConnectionClosed:
                        disconnected_clients.append(client_id)
                
                # 清理断开的客户端
                for client_id in disconnected_clients:
                    del self.clients[client_id]
            
            elif self.connect_type == "reverse_ws" and self.websocket:
                # 客户端模式：发送给服务器
                await self.websocket.send(json.dumps(message_data))
            
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
    
    async def _reconnect(self) -> None:
        """重新连接"""
        if not self.config.auto_reconnect:
            return
        
        logger.info("尝试重新连接...")
        
        for attempt in range(5):  # 最多重试5次
            try:
                await asyncio.sleep(self.config.reconnect_interval)
                await self.connect_reverse_ws()
                logger.info("重新连接成功")
                return
            except Exception as e:
                logger.warning(f"重连尝试 {attempt + 1} 失败: {e}")
        
        logger.error("重连失败，停止尝试")
    
    def create_event(self, raw_data: Any, **fields) -> Event:
        """创建事件"""
        if isinstance(raw_data, dict) and 'content' in raw_data:
            # 创建消息事件
            message = MessageBuilder.create_websocket_message(
                content=raw_data['content'],
                user_id=raw_data.get('user_id', 'unknown'),
                channel_id=raw_data.get('channel_id', 'default'),
                session_id=raw_data.get('session_id', ''),
                **fields
            )
            return message.to_event()
        else:
            # 创建通用事件
            return Event(
                type='custom',
                platform='websocket',
                raw_data=raw_data,
                **fields
            )
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
        
        for client in self.clients.values():
            await client.close()
        
        self.connected = False
        logger.info("WebSocket连接已断开")
