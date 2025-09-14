"""
类型注解定义模块
"""
from typing import Any, Dict, List, Optional, Union, Callable, Type, TypeVar, Generic, Awaitable, TYPE_CHECKING
from typing_extensions import Literal, TypedDict
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 基础类型
T = TypeVar('T')
ConfigT = TypeVar('ConfigT')
EventT = TypeVar('EventT', bound='Event')
MessageT = TypeVar('MessageT', bound='Message')
MiddlewareT = TypeVar('MiddlewareT', bound='Middleware')
PluginT = TypeVar('PluginT', bound='Plugin')

# 网络连接类型
ConnectType = Literal["ws", "reverse_ws", "http", "direct", "polling"]

# 日志级别
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 规则条件类型
RuleCondition = Union[str, Callable[['RuleContext'], bool]]

# 规则动作类型
RuleAction = Union[Callable[['RuleContext'], Any], Callable[['RuleContext'], Awaitable[Any]]]

# 事件类型
EventType = Literal["message", "join", "leave", "ready", "error", "custom"]

# 配置字典类型
ConfigDict = Dict[str, Any]

# 中间件配置
class MiddlewareConfig(TypedDict, total=False):
    middleware_connect_type: ConnectType
    enabled: bool
    bot_name: str

# 插件配置
class PluginConfig(TypedDict, total=False):
    enabled: bool
    priority: int

# 规则上下文
@dataclass
class RuleContext:
    """规则执行上下文"""
    event: EventT
    bot: 'Bot'
    middleware: Optional[MiddlewareT] = None
    plugin: Optional[PluginT] = None
    facts: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.facts is None:
            self.facts = {}

# 规则定义
# @dataclass
# class RuleDefinition:
#     """规则定义"""
#     name: str
#     condition: RuleCondition
#     action: RuleAction
#     priority: int = 0
#     enabled: bool = True
#     plugin: Optional[str] = None

# 抽象基类类型
class AbstractEvent(ABC):
    """事件抽象基类"""
    type: EventType
    timestamp: float
    platform: str
    raw_data: Any
    fields: Dict[str, Any]

class AbstractMessage(ABC):
    """消息抽象基类"""
    content: str
    user_id: str
    channel_id: str
    platform: str
    raw_data: Any
    fields: Dict[str, Any]

class AbstractMiddleware(ABC):
    """中间件抽象基类"""
    name: str
    config: MiddlewareConfig
    bot: 'Bot'
    connect_type: ConnectType

class AbstractPlugin(ABC):
    """插件抽象基类"""
    name: str
    config: PluginConfig
    bot: 'Bot'
    enabled: bool

# 为了向后兼容，导出Event类型
if TYPE_CHECKING:
    from .event import Event as EventType
else:
    # 运行时导入
    try:
        from .event import Event
    except ImportError:
        Event = None

# 前向引用，避免循环导入
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event
    from .message import Message
    from .plugin import Plugin
    from .bot import Bot
