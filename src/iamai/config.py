from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class LoggerConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


@dataclass
class MiddlewareConfig:
    enabled: bool = True
    middleware_connect_type: str = "direct"


@dataclass
class BotConfig:
    name: str = "iamai"
    logger: LoggerConfig = field(default_factory=LoggerConfig)
    middlewares: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Config:
    """全局配置"""

    bot: BotConfig = field(default_factory=BotConfig)
    logger: LoggerConfig = field(default_factory=LoggerConfig)
    middlewares: List[Dict[str, Any]] = field(default_factory=list)
