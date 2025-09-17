"""
消息系统模块
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import time
from .typing import Event


@dataclass
class Message:
    """消息基类"""

    content: str
    user_id: str
    channel_id: str
    platform: str
    raw_data: Any
    timestamp: float = field(default_factory=time.time)
    fields: Dict[str, Any] = field(default_factory=dict)
    message_id: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.fields:
            self.fields = {}
        if not self.message_id:
            self.message_id = f"{self.platform}_{self.user_id}_{self.timestamp}"

    def get_field(self, key: str, default: Any = None) -> Any:
        """获取字段值"""
        return self.fields.get(key, default)

    def set_field(self, key: str, value: Any) -> None:
        """设置字段值"""
        self.fields[key] = value

    def has_field(self, key: str) -> bool:
        """检查字段是否存在"""
        return key in self.fields

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "platform": self.platform,
            "message_id": self.message_id,
            "timestamp": self.timestamp,
            "fields": self.fields,
            "raw_data": self.raw_data,
        }

    def to_event(self) -> Event:
        """转换为消息事件

        将消息的关键信息复制到事件的 fields 中，便于规则条件使用 event.fields.get(...)
        """
        from .event import MessageEvent

        fields = {
            "content": self.content,
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            **(self.fields or {}),
        }

        return MessageEvent(
            type="message",
            platform=self.platform,
            raw_data=self.raw_data,
            message=self,
            fields=fields,
        )


@dataclass
class ConsoleMessage(Message):
    """控制台消息"""

    user_name: str = "User"

    def __post_init__(self):
        super().__post_init__()
        self.platform = "console"
        self.fields["user_name"] = self.user_name


@dataclass
class WebSocketMessage(Message):
    """WebSocket消息"""

    session_id: str = ""

    def __post_init__(self):
        super().__post_init__()
        self.platform = "websocket"
        self.fields["session_id"] = self.session_id


@dataclass
class HTTPMessage(Message):
    """HTTP消息"""

    request_id: str = ""
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        super().__post_init__()
        self.platform = "http"
        self.fields["request_id"] = self.request_id
        self.fields["headers"] = self.headers


# 消息构建器


class MessageBuilder:
    """消息构建器"""

    @staticmethod
    def create_console_message(
        content: str,
        user_id: str = "console_user",
        channel_id: str = "console_channel",
        user_name: str = "User",
        **fields,
    ) -> ConsoleMessage:
        """创建控制台消息"""
        msg = ConsoleMessage(
            content=content,
            user_id=user_id,
            channel_id=channel_id,
            platform="console",
            raw_data={"content": content, "user_id": user_id, "channel_id": channel_id},
            user_name=user_name,
        )
        for key, value in fields.items():
            msg.set_field(key, value)
        return msg

    @staticmethod
    def create_websocket_message(
        content: str, user_id: str, channel_id: str, session_id: str, **fields
    ) -> WebSocketMessage:
        """创建WebSocket消息"""
        msg = WebSocketMessage(
            content=content,
            user_id=user_id,
            channel_id=channel_id,
            platform="websocket",
            raw_data={"content": content, "user_id": user_id, "channel_id": channel_id},
            session_id=session_id,
        )
        for key, value in fields.items():
            msg.set_field(key, value)
        return msg

    @staticmethod
    def create_http_message(
        content: str,
        user_id: str,
        channel_id: str,
        request_id: str,
        headers: Optional[Dict[str, str]] = None,
        **fields,
    ) -> HTTPMessage:
        """创建HTTP消息"""
        msg = HTTPMessage(
            content=content,
            user_id=user_id,
            channel_id=channel_id,
            platform="http",
            raw_data={"content": content, "user_id": user_id, "channel_id": channel_id},
            request_id=request_id,
            headers=headers or {},
        )
        for key, value in fields.items():
            msg.set_field(key, value)
        return msg
