import inspect
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from .logger import get_logger

if TYPE_CHECKING:
    from .bot import Bot

logger = get_logger(__name__)


class Plugin(ABC):
    name: str = ""
    enabled: bool = True
    priority: int = 10
    
    def __init__(self, bot: 'Bot'):
        self.bot = bot
        if not self.name:
            self.name = self.__class__.__name__
        
        logger.info(f"初始化插件: {self.name}")
    
    async def on_startup(self) -> None:
        pass
    
    async def on_shutdown(self) -> None:
        pass
    
    async def handle_event(self, data: Dict[str, Any], source: str) -> bool:
        if not self.enabled:
            return False
        
        post_type = data.get("post_type", "")
        if post_type:
            handler_name = f"handle_{post_type}"
            handler = getattr(self, handler_name, None)
            if handler and callable(handler):
                try:
                    result = await handler(data, source)
                    return result if isinstance(result, bool) else False
                except Exception as e:
                    logger.error(f"插件 {self.name} 处理事件时出错: {e}", exc_info=True)
                    return False
        
        return await self.handle(data, source)
    
    async def handle(self, data: Dict[str, Any], source: str) -> bool:
        """
        Generic event handler.
        
        Override this method to handle all events that don't have specific handlers.
        
        Args:
            data: Event data dictionary.
            source: Event source identifier.
            
        Returns:
            True if the event was handled, False otherwise.
        """
        return False


class PluginManager:
    """
    Manager for loading and handling plugins.
    
    The PluginManager is responsible for:
    - Loading plugins from modules
    - Dispatching events to plugins
    - Managing plugin lifecycle
    """
    
    def __init__(self, bot: 'Bot'):
        """
        Initialize the plugin manager.
        
        Args:
            bot: The Bot instance this manager belongs to.
        """
        self.bot = bot
        self.plugins: List[Plugin] = []
        logger.info("初始化插件管理器")
    
    def register(self, plugin_class: type[Plugin]) -> None:
        """
        Register a plugin class.
        
        Args:
            plugin_class: The plugin class to register.
        """
        try:
            plugin = plugin_class(self.bot)
            self.plugins.append(plugin)
            logger.info(f"已注册插件: {plugin.name} (优先级: {plugin.priority})")
            
            # Sort by priority (higher first)
            self.plugins.sort(key=lambda p: p.priority, reverse=True)
        except Exception as e:
            logger.error(f"注册插件失败: {e}", exc_info=True)
    
    def load_from_module(self, module_path: str) -> None:
        """
        Load plugins from a Python module.
        
        Args:
            module_path: Dotted path to the module (e.g., 'plugins.echo').
        """
        try:
            import importlib
            module = importlib.import_module(module_path)
            
            # Find all Plugin subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Plugin) and obj is not Plugin:
                    self.register(obj)
                    
        except Exception as e:
            logger.error(f"从模块 {module_path} 加载插件失败: {e}", exc_info=True)
    
    async def start_all(self) -> None:
        """Call on_startup for all plugins."""
        for plugin in self.plugins:
            try:
                await plugin.on_startup()
            except Exception as e:
                logger.error(f"插件 {plugin.name} 启动失败: {e}", exc_info=True)
    
    async def stop_all(self) -> None:
        """Call on_shutdown for all plugins."""
        for plugin in self.plugins:
            try:
                await plugin.on_shutdown()
            except Exception as e:
                logger.error(f"插件 {plugin.name} 停止失败: {e}", exc_info=True)
    
    async def dispatch_event(self, data: Dict[str, Any], source: str) -> None:
        """
        Dispatch an event to all plugins.
        
        Args:
            data: Event data dictionary.
            source: Event source identifier.
        """
        for plugin in self.plugins:
            try:
                handled = await plugin.handle_event(data, source)
                if handled:
                    # Event was handled, stop propagation
                    logger.debug(f"事件被插件 {plugin.name} 处理")
                    break
            except Exception as e:
                logger.error(f"插件 {plugin.name} 处理事件时出错: {e}", exc_info=True)


def on_event(event_type: str):
    """
    Decorator for marking methods as event handlers.
    
    Args:
        event_type: The type of event to handle (e.g., 'message', 'request').
        
    Example:
        class MyPlugin(Plugin):
            @on_event('message')
            async def my_handler(self, data, source):
                print("Handling message event")
    """
    def decorator(func: Callable) -> Callable:
        func._event_type = event_type
        return func
    return decorator
