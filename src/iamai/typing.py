from typing import Literal, Dict, Any, Callable, TypeVar, Union
from dataclasses import dataclass

# 连接类型
ConnectType = Literal["websocket", "reverse_websocket", "http", "direct", "polling"]

# 日志级别
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# 配置字典类型
ConfigDict = Dict[str, Any]

# 中间件配置
MiddlewareConfig = Dict[str, Any]