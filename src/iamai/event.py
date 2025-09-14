"""
事件系统模块
"""
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import time
from .typing import EventType

@dataclass
class Event:
    """事件基类"""
    type: EventType
    platform: str
    raw_data: Any
    timestamp: float = field(default_factory=time.time)
    fields: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.fields:
            self.fields = {}
    
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
            'type': self.type,
            'platform': self.platform,
            'timestamp': self.timestamp,
            'fields': self.fields,
            'handled': self.handled,
            'raw_data': self.raw_data
        }

@dataclass
class MessageEvent(Event):
    """消息事件"""
    message: 'Message' = None
    
    def __post_init__(self):
        super().__post_init__()
        self.type = 'message'

@dataclass
class JoinEvent(Event):
    """加入事件"""
    user_id: str = ""
    channel_id: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = 'join'

@dataclass
class LeaveEvent(Event):
    """离开事件"""
    user_id: str = ""
    channel_id: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = 'leave'

@dataclass
class ReadyEvent(Event):
    """就绪事件"""
    def __post_init__(self):
        super().__post_init__()
        self.type = 'ready'

@dataclass
class ErrorEvent(Event):
    """错误事件"""
    error: Exception = None
    error_msg: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = 'error'

@dataclass
class CustomEvent(Event):
    """自定义事件"""
    event_name: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.type = 'custom'
