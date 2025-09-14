"""
机器人核心模块
"""
import asyncio
import importlib
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path
import signal
import sys

from .event import Event
from .rule import RuleEngine, RuleDefinition
from .plugin import PluginManager, BasePlugin
from .middleware import Middleware, MiddlewareRegistry, middleware_registry
from .config import Config
from .logger import get_logger, setup_logger

logger = get_logger(__name__)

class Bot:
    """机器人核心类"""
    
    def __init__(self, config: Optional[Union[str, Path, Config]] = None):
        # 配置
        if isinstance(config, (str, Path)):
            self.config = Config(config)
        elif isinstance(config, Config):
            self.config = config
        else:
            self.config = Config()
        
        # 设置日志（只在第一次创建Bot实例时设置）
        if not hasattr(Bot, '_logger_initialized'):
            setup_logger(
                level=self.config.bot_config.log.level,
                log_file=self.config.bot_config.log.log_file,
                console=self.config.bot_config.log.console,
                format_string=self.config.bot_config.log.format_string
            )
            Bot._logger_initialized = True
        
        # 核心组件
        self.rule_engine = RuleEngine()
        self.plugin_manager = PluginManager(self)
        self.middlewares: Dict[str, Middleware] = {}
        self.running = False
        
        # 统计信息
        self.stats = {
            'events_processed': 0,
            'rules_executed': 0,
            'plugins_loaded': 0,
            'middlewares_active': 0,
            'uptime': 0
        }
        
        # 信号处理
        self._setup_signal_handlers()
        
        logger.info("机器人实例已创建")
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            
            def signal_handler():
                logger.info("收到信号，准备关闭...")
                asyncio.create_task(self.stop())
            
            for sig in [signal.SIGTERM, signal.SIGINT]:
                loop.add_signal_handler(sig, signal_handler)
    
    async def start(self) -> None:
        """启动机器人"""
        if self.running:
            logger.warning("机器人已在运行")
            return
        
        logger.info("启动机器人...")
        
        try:
            # 加载插件
            await self._load_plugins()
            
            # 启动中间件
            await self._start_middlewares()
            
            self.running = True
            logger.info("机器人启动成功")
            
            # 启动统计任务
            asyncio.create_task(self._stats_task())
            
            # 保持运行
            await self._keep_alive()
            
        except Exception as e:
            logger.error(f"启动机器人失败: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """停止机器人"""
        if not self.running:
            return
        
        logger.info("停止机器人...")
        
        self.running = False
        
        try:
            # 停止中间件
            await self._stop_middlewares()
            
            # 卸载插件
            await self._unload_plugins()
            
            logger.info("机器人已停止")
            
        except Exception as e:
            logger.error(f"停止机器人时出错: {e}")
    
    async def _load_plugins(self) -> None:
        """加载插件"""
        logger.info("加载插件...")
        
        # 从配置的插件目录加载
        for plugin_dir in self.config.bot_config.plugin_dir:
            try:
                loaded_plugins = self.plugin_manager.load_plugins_from_dir(plugin_dir)
                if loaded_plugins:
                    logger.info(f"从 {plugin_dir} 加载了 {len(loaded_plugins)} 个插件")
            except FileNotFoundError as e:
                logger.error(f"插件目录加载失败: {e}")
                # 继续加载其他目录，不中断启动
        
        # 等待插件加载完成
        await asyncio.sleep(0.1)
        
        self.stats['plugins_loaded'] = len(self.plugin_manager.plugins)
        logger.info(f"总共加载了 {self.stats['plugins_loaded']} 个插件")
    
    async def _unload_plugins(self) -> None:
        """卸载插件"""
        logger.info("卸载插件...")
        
        for plugin_name in list(self.plugin_manager.plugins.keys()):
            await self.plugin_manager.unload_plugin(plugin_name)
    
    async def _start_middlewares(self) -> None:
        """启动中间件"""
        logger.info("启动中间件...")
        
        for middleware_name in self.config.bot_config.middlewares:
            try:
                await self._load_middleware(middleware_name)
            except Exception as e:
                logger.error(f"加载中间件 {middleware_name} 失败: {e}")
        
        # 启动所有中间件
        for middleware in self.middlewares.values():
            try:
                await middleware.start()
            except Exception as e:
                logger.error(f"启动中间件 {middleware.name} 失败: {e}")
        
        self.stats['middlewares_active'] = len(self.middlewares)
        logger.info(f"启动了 {self.stats['middlewares_active']} 个中间件")
    
    async def _stop_middlewares(self) -> None:
        """停止中间件"""
        logger.info("停止中间件...")
        
        for middleware in self.middlewares.values():
            try:
                await middleware.stop()
            except Exception as e:
                logger.error(f"停止中间件 {middleware.name} 失败: {e}")
        
        self.middlewares.clear()
    
    async def _load_middleware(self, middleware_name: str) -> None:
        """加载中间件"""
        try:
            # 从注册表获取中间件类
            middleware_class = middleware_registry.get(middleware_name)
            if not middleware_class:
                raise ImportError(f"找不到中间件: {middleware_name}")
            
            # 获取配置
            config_name = middleware_name.split('.')[-1]
            middleware_config = self.config.get_middleware_config(config_name)
            
            # 添加bot_name到配置中
            middleware_config['bot_name'] = self.config.bot_config.bot_name
            
            # 创建中间件配置对象
            from .middleware import MiddlewareConfig
            config_obj = MiddlewareConfig(**middleware_config)
            
            # 创建中间件实例
            middleware = middleware_class(
                name=config_name,
                config=config_obj,
                bot=self
            )
            
            self.middlewares[middleware.name] = middleware
            logger.info(f"中间件 {middleware_name} 加载成功")
            
        except Exception as e:
            logger.error(f"加载中间件 {middleware_name} 失败: {e}")
            raise
    
    async def process_event(self, event: Event, middleware: Optional[Middleware] = None) -> List[Any]:
        """处理事件"""
        if not self.running:
            return []
        
        self.stats['events_processed'] += 1
        
        try:
            # 插件钩子
            await self.plugin_manager.process_event(event)
            
            # 规则引擎处理
            results = await self.rule_engine.process_event(
                event, self, middleware
            )
            
            self.stats['rules_executed'] += len(results)
            
            # 标记事件已处理
            event.handled = True
            
            return results
            
        except Exception as e:
            logger.error(f"处理事件时出错: {e}")
            return []
    
    def add_rule(self, rule: Union[RuleDefinition, callable]) -> None:
        """添加规则"""
        if callable(rule):
            # 装饰器规则
            if hasattr(rule, '_rule_metadata'):
                metadata = rule._rule_metadata
                rule_def = RuleDefinition(
                    name=metadata['name'],
                    condition=metadata['condition'],
                    action=rule,
                    priority=metadata['priority'],
                    enabled=metadata['enabled'],
                    event_types=metadata['event_types']
                )
                self.rule_engine.add_rule(rule_def)
            else:
                # 简单函数规则
                rule_def = RuleDefinition(
                    name=rule.__name__,
                    condition="event.type == 'message'",
                    action=rule,
                    priority=0,
                    enabled=True
                )
                self.rule_engine.add_rule(rule_def)
        else:
            # RuleDefinition对象
            self.rule_engine.add_rule(rule)
    
    def load_plugin(self, plugin_class: Type['Plugin'], config: Optional[Dict[str, Any]] = None) -> bool:
        """加载插件（同步包装）"""
        return asyncio.create_task(self.plugin_manager.load_plugin(plugin_class, config))
    
    def load_plugins_from_dir(self, plugin_dir: str) -> List[str]:
        """从目录加载插件"""
        return self.plugin_manager.load_plugins_from_dir(plugin_dir)
    
    def get_plugin(self, plugin_name: str) -> Optional['Plugin']:
        """获取插件"""
        return self.plugin_manager.get_plugin(plugin_name)
    
    def get_all_rules(self) -> List[RuleDefinition]:
        """获取所有规则"""
        return self.rule_engine.get_rules()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        import time
        uptime = time.time() - getattr(self, '_start_time', time.time())
        
        return {
            **self.stats,
            'uptime': uptime,
            'plugins': len(self.plugin_manager.plugins),
            'middlewares': len(self.middlewares),
            'rules': len(self.rule_engine.rules)
        }
    
    async def _keep_alive(self) -> None:
        """保持运行"""
        self._start_time = asyncio.get_event_loop().time()
        
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
    
    async def _stats_task(self) -> None:
        """统计任务"""
        while self.running:
            await asyncio.sleep(60)  # 每分钟更新一次统计
            logger.debug(f"统计信息: {self.get_stats()}")
    
    async def run(self) -> None:
        """运行机器人"""
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        finally:
            await self.stop()
