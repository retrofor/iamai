"""
插件系统模块
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, Callable
from dataclasses import dataclass, field
import asyncio
import importlib
import inspect
from pathlib import Path

from .typing import PluginConfig, Event
from .rule import RuleDefinition
from .rule import rule, RuleEngine
from .logger import get_logger
from .config import PluginConfig as BasePluginConfig

logger = get_logger(__name__)

class PluginConfig(BasePluginConfig):
    """插件配置"""
    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

class Plugin(ABC):
    """插件抽象基类"""
    
    def __init__(self, bot: 'Bot', config: Optional[Dict[str, Any]] = None):
        self.bot = bot
        self.config = config or {}
        self.name = self.__class__.__name__
        self.enabled = self.config.get('enabled', True)
        self.priority = self.config.get('priority', 0)
        self.rules: List[RuleDefinition] = []
        
        # 自动注册规则
        self._register_rules()
    
    @abstractmethod
    async def on_load(self) -> None:
        """插件加载时调用"""
        pass
    
    @abstractmethod
    async def on_unload(self) -> None:
        """插件卸载时调用"""
        pass
    
    async def on_event(self, event: Event) -> None:
        """事件处理钩子"""
        pass
    
    async def before_event(self, event: Event) -> None:
        """事件处理前钩子"""
        pass
    
    async def after_event(self, event: Event) -> None:
        """事件处理后钩子"""
        pass
    
    async def on_error(self, error: Exception) -> None:
        """错误处理钩子"""
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config[key] = value
    
    def add_rule(self, rule_def: RuleDefinition) -> None:
        """添加规则"""
        rule_def.plugin = self.name
        self.rules.append(rule_def)
        logger.debug(f"插件 {self.name} 添加规则: {rule_def.name}")
    
    def _register_rules(self) -> None:
        """自动注册规则"""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_rule_metadata'):
                metadata = method._rule_metadata
                rule_def = RuleDefinition(
                    name=metadata['name'],
                    condition=metadata['condition'],
                    action=method,
                    priority=metadata['priority'],
                    enabled=metadata['enabled'],
                    plugin=self.name,
                    event_types=metadata['event_types']
                )
                self.add_rule(rule_def)

class PluginManager:
    """插件管理器"""
    
    def __init__(self, bot: 'Bot'):
        self.bot = bot
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_dirs: List[Path] = []
    
    async def load_plugin(self, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None) -> bool:
        """加载插件"""
        try:
            plugin = plugin_class(self.bot, config)
            if plugin.name in self.plugins:
                logger.warning(f"插件 {plugin.name} 已存在，跳过加载")
                return False
            
            await plugin.on_load()
            
            # 注册规则
            for rule in plugin.rules:
                self.bot.rule_engine.add_rule(rule)
            
            self.plugins[plugin.name] = plugin
            logger.info(f"插件 {plugin.name} 加载成功")
            return True
            
        except Exception as e:
            logger.error(f"加载插件失败: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            logger.warning(f"插件 {plugin_name} 不存在")
            return False
        
        try:
            plugin = self.plugins[plugin_name]
            await plugin.on_unload()
            
            # 移除规则
            for rule in plugin.rules:
                self.bot.rule_engine.remove_rule(rule.name)
            
            del self.plugins[plugin_name]
            logger.info(f"插件 {plugin_name} 卸载成功")
            return True
            
        except Exception as e:
            logger.error(f"卸载插件失败: {e}")
            return False
    
    async def reload_plugin(self, plugin_class: Type[Plugin], config: Optional[Dict[str, Any]] = None) -> bool:
        """重新加载插件"""
        plugin_name = plugin_class.__name__
        
        # 先卸载
        if plugin_name in self.plugins:
            await self.unload_plugin(plugin_name)
        
        # 再加载
        return await self.load_plugin(plugin_class, config)
    
    def load_plugins_from_dir(self, plugin_dir: str) -> List[str]:
        """从目录加载插件"""
        plugin_dir_path = Path(plugin_dir)
        if not plugin_dir_path.exists():
            raise FileNotFoundError(f"插件目录不存在: {plugin_dir}")
        
        loaded_plugins = []
        
        for py_file in plugin_dir_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                module_name = py_file.stem
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找插件类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Plugin) and 
                        obj != Plugin):
                        
                        plugin_name = obj.__name__
                        if plugin_name not in self.plugins:
                            # 获取插件配置
                            plugin_config = self.bot.config.get_plugin_config(plugin_name)
                            
                            # 异步加载插件
                            asyncio.create_task(self.load_plugin(obj, plugin_config))
                            loaded_plugins.append(plugin_name)
                
            except Exception as e:
                logger.error(f"加载插件文件 {py_file} 失败: {e}")
        
        return loaded_plugins
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """获取插件"""
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """获取所有插件"""
        return self.plugins.copy()
    
    def list_plugins(self) -> List[str]:
        """列出插件名称"""
        return list(self.plugins.keys())
    
    async def process_event(self, event: Event) -> None:
        """处理事件（插件钩子）"""
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
            
            try:
                await plugin.before_event(event)
                await plugin.on_event(event)
                await plugin.after_event(event)
            except Exception as e:
                logger.error(f"插件 {plugin.name} 处理事件时出错: {e}")
                await plugin.on_error(e)

# 插件装饰器
def plugin_config(**config):
    """插件配置装饰器"""
    def decorator(plugin_class: Type[Plugin]):
        plugin_class._default_config = config
        return plugin_class
    return decorator

# 示例插件基类
class BasePlugin(Plugin):
    """基础插件类"""
    
    async def on_load(self) -> None:
        """插件加载"""
        logger.info(f"插件 {self.name} 已加载")
    
    async def on_unload(self) -> None:
        """插件卸载"""
        logger.info(f"插件 {self.name} 已卸载")
