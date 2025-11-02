from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Literal
import asyncio
from ..logger import get_logger

logger = get_logger(__name__)

ConnectType = Literal["websocket", "reverse_websocket", "http", "direct"]


class MiddlewareConfig:
    """中间件配置基类"""

    enabled: bool = True
    middleware_connect_type: ConnectType = "direct"

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class MappedObject:
    def __init__(self, data: Dict[str, Any], mapping: Optional[Dict[str, str]] = None):
        self._data = data
        self._mapping = mapping or {}
        self._reverse_mapping = (
            {v: k for k, v in self._mapping.items()} if mapping else {}
        )

    def __getattr__(self, name: str) -> Any:
        """通过属性名获取值"""
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        if name in self._reverse_mapping:
            original_name = self._reverse_mapping[name]
            if original_name in self._data:
                value = self._data[original_name]
                return self._wrap_value(value)

        if name in self._data:
            value = self._data[name]
            return self._wrap_value(value)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def __getitem__(self, key: str) -> Any:
        """字典式访问"""
        try:
            return self.__getattr__(key)
        except AttributeError:
            raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        """安全获取值"""
        try:
            return self.__getattr__(key)
        except AttributeError:
            return default

    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self._data or key in self._reverse_mapping

    def __repr__(self) -> str:
        return f"MappedObject({self._data})"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()

    def _wrap_value(self, value: Any) -> Any:
        """包装值，递归处理字典和列表"""
        if isinstance(value, dict):
            return MappedObject(value, self._mapping)
        elif isinstance(value, list):
            return [self._wrap_value(item) for item in value]
        return value


class Middleware(ABC):
    def __init__(self, name: str, config: MiddlewareConfig, bot: Any):
        self.name = name
        self.config = config
        self.bot = bot
        self.connect_type = getattr(config, "middleware_connect_type", "direct")
        self.enabled = getattr(config, "enabled", True)
        self.connected = False

    @abstractmethod
    async def start(self) -> None:
        """启动中间件"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """停止中间件"""
        pass

    def map_data(self, raw_data: Dict[str, Any]) -> MappedObject:
        """
        映射数据（映射器功能）

        Args:
            raw_data: 原始数据

        Returns:
            映射后的对象
        """
        return MappedObject(raw_data)

    async def disconnect(self) -> None:
        """断开连接"""
        self.connected = False
        logger.info(f"中间件 {self.name} 已断开连接")

    def print_data(self, data: Dict[str, Any]) -> None:
        """打印接收到的数据"""
        if self.bot:
            self.bot.print_event(data, source=self.name)


__all__ = [
    "Middleware",
    "MiddlewareConfig",
    "MappedObject",
    "ConnectType",
]
