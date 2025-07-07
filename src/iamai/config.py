from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Any


class BaseConfig(BaseModel):
    """所有配置类的基类，提供一些默认设置."""

    model_config = ConfigDict(
        extra="forbid",  # 禁止未定义的字段，保证配置的严格性
        frozen=True,  # 配置对象一旦创建，就不能修改，避免运行时意外更改
        populate_by_name=True,  # 允许通过别名 (alias) 填充字段
    )

    description: Optional[str] = None  # 可选的配置描述


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogConfig(BaseConfig):
    """日志配置."""

    level: LogLevel = LogLevel.INFO
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    output_file: Optional[str] = None  # 可以输出到文件， None 表示输出到控制台


class BotConfig(BaseConfig):
    """机器人核心配置."""

    name: str = "MyAwesomeBot"
    version: str = "1.0.0"
    debug: bool = False
    api_url: str = "https://api.example.com"


class PluginConfig(BaseConfig):
    """插件配置."""

    enabled_plugins: list[str] = []  # 启用的插件列表
    plugin_dir: str = "plugins"  # 插件目录


class ModelConfig(BaseConfig):
    """模型配置."""

    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2048


class MiddlewareConfig(BaseConfig):
    """中间件配置."""

    enabled_middleware: list[str] = []  # 启用的中间件列表
    middleware_settings: dict[
        str, Any
    ] = {}  # 中间件特定设置，key 是中间件的名字，value 是配置


class MainConfig(BaseConfig):
    """主配置类，包含所有子配置."""

    bot: BotConfig = BotConfig()
    log: LogConfig = LogConfig()
    plugin: PluginConfig = PluginConfig()
    model: ModelConfig = ModelConfig()
    middleware: MiddlewareConfig = MiddlewareConfig()
