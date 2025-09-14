"""
iamai - 现代异步规则驱动机器人框架
"""

__version__ = "4.0.0"
__author__ = "iamai Team"
__description__ = "现代异步规则驱动机器人框架"

# 核心导入
from .bot import Bot
from .event import Event, MessageEvent, JoinEvent, LeaveEvent, ReadyEvent, ErrorEvent, CustomEvent
from .message import Message, ConsoleMessage, WebSocketMessage, HTTPMessage, MessageBuilder
from .rule import RuleEngine, RuleDefinition, rule, when_all, when_any, Conditions
from .plugin import Plugin, BasePlugin, PluginManager, PluginConfig
from .middleware import Middleware, MiddlewareConfig, MiddlewareRegistry, middleware_registry, register_middleware
from .config import Config, BotConfig, LoggerConfig, MiddlewareConfig as ConfigMiddlewareConfig, PluginConfig as ConfigPluginConfig
from .logger import get_logger, setup_logger
from .typing import (
    ConnectType, LogLevel, RuleCondition, RuleAction, RuleContext,
    EventType, ConfigDict, MiddlewareConfig as TypingMiddlewareConfig,
    PluginConfig as TypingPluginConfig
)

# 导出所有公共API
__all__ = [
    # 核心类
    "Bot",
    
    # 事件系统
    "Event", "MessageEvent", "JoinEvent", "LeaveEvent", "ReadyEvent", "ErrorEvent", "CustomEvent",
    
    # 消息系统
    "Message", "ConsoleMessage", "WebSocketMessage", "HTTPMessage", "MessageBuilder",
    
    # 规则引擎
    "RuleEngine", "RuleDefinition", "rule", "when_all", "when_any", "Conditions",
    
    # 插件系统
    "Plugin", "BasePlugin", "PluginManager", "PluginConfig",
    
    # 中间件系统
    "Middleware", "MiddlewareConfig", "MiddlewareRegistry", "middleware_registry", "register_middleware",
    
    # 配置系统
    "Config", "BotConfig", "LoggerConfig", "ConfigMiddlewareConfig", "ConfigPluginConfig",
    
    # 日志系统
    "get_logger", "setup_logger",
    
    # 类型注解
    "ConnectType", "LogLevel", "RuleCondition", "RuleAction", "RuleContext",
    "EventType", "ConfigDict", "TypingMiddlewareConfig", "TypingPluginConfig",
    
    # 版本信息
    "__version__", "__author__", "__description__"
]
