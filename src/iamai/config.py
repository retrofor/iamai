"""
配置系统模块
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import toml
import json
import yaml
from .typing import ConnectType, LogLevel, ConfigDict
from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class LoggerConfig:
    """日志配置"""
    level: LogLevel = "INFO"
    log_file: Optional[str] = None
    console: bool = True
    format_string: Optional[str] = None

@dataclass
class MiddlewareConfig:
    """中间件配置基类"""
    middleware_connect_type: ConnectType = "direct"
    enabled: bool = True

@dataclass
class WebSocketMiddlewareConfig(MiddlewareConfig):
    """WebSocket中间件配置"""
    middleware_connect_type: ConnectType = "ws"
    host: str = "127.0.0.1"
    port: int = 8080
    url: str = "/ws"
    auto_reconnect: bool = True
    reconnect_interval: int = 5

@dataclass
class PluginConfig:
    """插件配置基类"""
    enabled: bool = True
    priority: int = 0

@dataclass
class BotConfig:
    """机器人配置"""
    bot_name: str = "Bot"
    plugins: List[str] = field(default_factory=list)
    plugin_dir: List[str] = field(default_factory=lambda: ["plugins"])
    middlewares: List[str] = field(default_factory=lambda: ["iamai.middleware.console"])
    log: LoggerConfig = field(default_factory=LoggerConfig)
    hot_reload: bool = False
    debug: bool = False

class Config:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self.config_path = Path(config_path) if config_path else None
        self.bot_config = BotConfig()
        self.middleware_configs: Dict[str, Dict[str, Any]] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        
        if self.config_path and self.config_path.exists():
            self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        if not self.config_path or not self.config_path.exists():
            logger.warning("配置文件不存在")
            return
        
        try:
            if self.config_path.suffix == '.toml':
                self._load_toml()
            elif self.config_path.suffix == '.json':
                self._load_json()
            elif self.config_path.suffix in ['.yaml', '.yml']:
                self._load_yaml()
            else:
                logger.error(f"不支持的配置文件格式: {self.config_path.suffix}")
                return
            
            logger.info(f"成功加载配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    def _load_toml(self) -> None:
        """加载TOML配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)
        self._parse_config_data(data)
    
    def _load_json(self) -> None:
        """加载JSON配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self._parse_config_data(data)
    
    def _load_yaml(self) -> None:
        """加载YAML配置"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self._parse_config_data(data)
    
    def _parse_config_data(self, data: Dict[str, Any]) -> None:
        """解析配置数据"""
        # 解析bot配置
        if 'bot' in data:
            bot_data = data['bot']
            self.bot_config.bot_name = bot_data.get('bot_name', 'Bot')
            self.bot_config.plugins = bot_data.get('plugins', [])
            self.bot_config.plugin_dir = bot_data.get('plugin_dir', ['plugins'])
            self.bot_config.middlewares = bot_data.get('middlewares', ['iamai.middleware.console'])
            self.bot_config.hot_reload = bot_data.get('hot_reload', False)
            self.bot_config.debug = bot_data.get('debug', False)
            
            # 解析日志配置
            if 'log' in bot_data:
                log_data = bot_data['log']
                self.bot_config.log = LoggerConfig(
                    level=log_data.get('level', 'INFO'),
                    log_file=log_data.get('log_file'),
                    console=log_data.get('console', True),
                    format_string=log_data.get('format_string')
                )
        
        # 解析中间件配置
        if 'middleware' in data:
            for middleware_name, middleware_data in data['middleware'].items():
                self.middleware_configs[middleware_name] = middleware_data
        
        # 解析插件配置
        for key, value in data.items():
            if key not in ['bot', 'middleware']:
                self.plugin_configs[key] = value
    
    def get_middleware_config(self, middleware_name: str) -> Dict[str, Any]:
        """获取中间件配置"""
        return self.middleware_configs.get(middleware_name, {})
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件配置"""
        return self.plugin_configs.get(plugin_name, {})
    
    def save_config(self) -> None:
        """保存配置"""
        if not self.config_path:
            logger.error("未指定配置文件路径")
            return
        
        data = {
            'bot': {
                'plugins': self.bot_config.plugins,
                'plugin_dir': self.bot_config.plugin_dir,
                'middlewares': self.bot_config.middlewares,
                'hot_reload': self.bot_config.hot_reload,
                'debug': self.bot_config.debug,
                'log': {
                    'level': self.bot_config.log.level,
                    'log_file': self.bot_config.log.log_file,
                    'console': self.bot_config.log.console,
                    'format_string': self.bot_config.log.format_string
                }
            },
            'middleware': self.middleware_configs,
            **self.plugin_configs
        }
        
        try:
            if self.config_path.suffix == '.toml':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    toml.dump(data, f)
            elif self.config_path.suffix == '.json':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif self.config_path.suffix in ['.yaml', '.yml']:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"成功保存配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

# 默认配置
def get_default_config() -> Config:
    """获取默认配置"""
    return Config()
