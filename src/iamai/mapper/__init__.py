from abc import ABC, abstractmethod
from typing import Dict, Any

class Mapper(ABC):
    """Mapper 链接器基类，用于接收和发送数据。"""

    @abstractmethod
    async def start(self, host: str, port: int) -> None:
        """启动服务器并监听指定的主机和端口。"""
        pass

    @abstractmethod
    async def send(self, websocket, data: Dict[str, Any]) -> None:
        """发送数据。"""
        pass

    @abstractmethod
    async def receive(self, websocket) -> Dict[str, Any]:
        """接收数据。"""
        pass
