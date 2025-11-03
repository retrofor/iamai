import asyncio
import signal
from typing import Any, Dict, List, Optional, Union
from .logger import logger as _logger

class Bot:
    def __init__(self, config: Optional[Union[Dict[str, Any], Any]] = None):
        self.logger = _logger
        self.config = config or {}
        self.middlewares: List[Any] = []
        self.running = False

        self._init_middlewares()

        self.logger.info("Bot 初始化完成")

    def _init_middlewares(self) -> None:
        if not self.config:
            self.logger.warning("未配置中间件")
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
                self.logger.info(f"已加载中间件: {middleware_name}")
            else:
                self.logger.error(f"未知的中间件类型: {middleware_name}")
        except Exception as e:
            self.logger.error(f"加载中间件失败: {e}", exc_info=True)

    async def start(self) -> None:
        self.logger.info("启动 Bot...")
        self.running = True

        # 启动所有中间件（不等待它们完成，因为它们会持续运行）
        for middleware in self.middlewares:
            asyncio.create_task(middleware.start())

    async def stop(self) -> None:
        self.logger.info("停止 Bot...")
        self.running = False

        # 停止所有中间件
        tasks = []
        for middleware in self.middlewares:
            task = asyncio.create_task(middleware.stop())
            tasks.append(task)

        # 等待所有中间件停止
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        self.logger.info("Bot 已停止")

    async def run(self) -> None:
        # 设置信号处理
        loop = asyncio.get_event_loop()

        def signal_handler():
            self.logger.info("收到停止信号")
            asyncio.create_task(self.stop())

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, signal_handler)

        try:
            await self.start()
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            self.logger.info("收到键盘中断")
        except Exception as e:
            self.logger.error(f"运行时错误: {e}", exc_info=True)
        finally:
            await self.stop()

    def print_event(self, data: Dict[str, Any], source: str = "unknown") -> None:
        import json
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        self.logger.info(f"[{timestamp}] 事件来源: {source}")
        self.logger.info(json.dumps(data, indent=2, ensure_ascii=False))
