"""
中间件系统模块
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, Union
from dataclasses import dataclass
import asyncio
from ..typing import ConnectType, MiddlewareConfig, Event
from ..logger import get_logger
from ..config import MiddlewareConfig as BaseMiddlewareConfig

logger = get_logger(__name__)

class MiddlewareConfig(BaseMiddlewareConfig):
    """中间件配置"""
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

class Middleware(ABC):
    """中间件抽象基类"""
    
    def __init__(self, name: str, config: MiddlewareConfig, bot: 'Bot'):
        self.name = name
        self.config = config
        self.bot = bot
        self.connect_type = config.middleware_connect_type
        self.enabled = config.enabled
        self.connected = False
        
    @abstractmethod
    async def start(self) -> None:
        """启动中间件"""w
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止中间件"""
        pass
    
    @abstractmethod
    async def send_message(self, content: str, channel_id: str, **kwargs) -> None:
        """发送消息"""
        pass
    
    @abstractmethod
    def create_event(self, raw_data: Any, **fields) -> Event:
        """创建事件"""
        pass
    
    # 网络连接方法（根据connect_type实现）
    async def connect_ws(self) -> None:
        """WebSocket连接"""
        raise NotImplementedError(f"中间件 {self.name} 不支持WebSocket连接")
    
    async def connect_reverse_ws(self) -> None:
        """反向WebSocket连接"""
        raise NotImplementedError(f"中间件 {self.name} 不支持反向WebSocket连接")
    
    async def connect_http(self) -> None:
        """HTTP连接"""
        raise NotImplementedError(f"中间件 {self.name} 不支持HTTP连接")
    
    async def connect_direct(self) -> None:
        """直接连接"""
        raise NotImplementedError(f"中间件 {self.name} 不支持直接连接")
    
    async def connect_polling(self) -> None:
        """轮询连接"""
        raise NotImplementedError(f"中间件 {self.name} 不支持轮询连接")
    
    async def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        logger.info(f"中间件 {self.name} 已断开连接")
    
    async def handle_event(self, event: Event) -> None:
        """处理事件"""
        if not self.enabled:
            return
        
        try:
            await self.bot.process_event(event, self)
        except Exception as e:
            logger.error(f"处理事件时出错: {e}")
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return getattr(self.config, key, default)

# 中间件注册表
class MiddlewareRegistry:
    """中间件注册表"""
    
    def __init__(self):
        self._middlewares: Dict[str, Type[Middleware]] = {}
    
    def register(self, name: str, middleware_class: Type[Middleware]) -> None:
        """注册中间件"""
        self._middlewares[name] = middleware_class
        logger.debug(f"注册中间件: {name}")
    
    def get(self, name: str) -> Optional[Type[Middleware]]:
        """获取中间件类"""
        return self._middlewares.get(name)
    
    def list_middlewares(self) -> Dict[str, Type[Middleware]]:
        """列出所有中间件"""
        return self._middlewares.copy()
    
    def create_middleware(self, name: str, config: MiddlewareConfig, bot: 'Bot') -> Optional[Middleware]:
        """创建中间件实例"""
        middleware_class = self.get(name)
        if middleware_class:
            return middleware_class(name, config, bot)
        return None

# 全局中间件注册表
middleware_registry = MiddlewareRegistry()

def register_middleware(name: str):
    """中间件注册装饰器"""
    def decorator(middleware_class: Type[Middleware]):
        middleware_registry.register(name, middleware_class)
        return middleware_class
    return decorator

# 导入所有中间件以确保注册
from . import console, websockets
