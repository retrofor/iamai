import asyncio
import signal
from typing import Any, Dict, List, Optional, Union
from .logger import get_logger, setup_logger
from .plugin import PluginManager

logger = get_logger(__name__)


class Bot:
    def __init__(self, config: Optional[Union[Dict[str, Any], Any]] = None):
        setup_logger()
        self.config = config or {}
        self.middlewares: List[Any] = []
        self.plugin_manager = PluginManager(self)
        self.running = False

        self._init_middlewares()
        self._init_plugins()

        logger.info("Bot 初始化完成")

    def _init_middlewares(self) -> None:
        if not self.config:
            logger.warning("未配置中间件")
            return

        middleware_name = self.config.get("middleware", "console")
        middleware_config_key = f"{middleware_name}_config"
        middleware_config_data = self.config.get(middleware_config_key, {})

        try:
            if middleware_name == "onebot11":
                from .middleware.onebot11 import (
                    OneBot11Middleware,
                    OneBot11MiddlewareConfig,
                )

                if isinstance(middleware_config_data, dict):
                    middleware_config = OneBot11MiddlewareConfig(
                        **middleware_config_data
                    )
                else:
                    middleware_config = middleware_config_data

                middleware = OneBot11Middleware(
                    middleware_name, middleware_config, self
                )
                self.middlewares.append(middleware)
                logger.info(f"已加载中间件: {middleware_name}")
            else:
                logger.error(f"未知的中间件类型: {middleware_name}")
        except Exception as e:
            logger.error(f"加载中间件失败: {e}", exc_info=True)

    def _init_plugins(self) -> None:
        """初始化插件"""
        plugins_config = self.config.get("plugins", [])
        
        if not plugins_config:
            logger.info("未配置插件")
            return
        
        for plugin_module in plugins_config:
            try:
                self.plugin_manager.load_from_module(plugin_module)
            except Exception as e:
                logger.error(f"加载插件模块 {plugin_module} 失败: {e}", exc_info=True)

    async def start(self) -> None:
        logger.info("启动 Bot...")
        self.running = True

        # 启动所有插件
        await self.plugin_manager.start_all()

        # 启动所有中间件（不等待它们完成，因为它们会持续运行）
        for middleware in self.middlewares:
            asyncio.create_task(middleware.start())

    async def stop(self) -> None:
        logger.info("停止 Bot...")
        self.running = False

        # 停止所有插件
        await self.plugin_manager.stop_all()

        # 停止所有中间件
        tasks = []
        for middleware in self.middlewares:
            task = asyncio.create_task(middleware.stop())
            tasks.append(task)

        # 等待所有中间件停止
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("Bot 已停止")

    async def run(self) -> None:
        # 设置信号处理
        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("收到停止信号")
            asyncio.create_task(self.stop())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        try:
            await self.start()
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("收到键盘中断")
        except Exception as e:
            logger.error(f"运行时错误: {e}", exc_info=True)
        finally:
            await self.stop()

    async def handle_event(self, data: Dict[str, Any], source: str = "unknown") -> None:
        """
        处理事件（分发到插件）
        
        Args:
            data: 事件数据
            source: 事件来源
        """
        # 如果有插件，分发给插件处理
        if self.plugin_manager.plugins:
            await self.plugin_manager.dispatch_event(data, source)
        else:
            # 没有插件时，打印原始数据
            self.print_event(data, source)
    
    def print_event(self, data: Dict[str, Any], source: str = "unknown") -> None:
        """
        打印事件数据（调试用）
        
        Args:
            data: 事件数据
            source: 事件来源
        """
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print("\n" + "=" * 80)
        print(f"[{timestamp}] 事件来源: {source}")
        print("-" * 80)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("=" * 80 + "\n")
