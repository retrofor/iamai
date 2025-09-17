"""
控制台中间件模块
使用Textual实现交互式终端界面
"""
import asyncio
from typing import Any, Dict, Optional
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Input, Button, Static, RichLog, Header, Footer
from textual.reactive import reactive
from rich.text import Text
from dataclasses import dataclass
from . import Middleware, register_middleware, MiddlewareConfig
from ..event import Event, MessageEvent
from ..message import Message, ConsoleMessage, MessageBuilder
from ..logger import get_logger
from ..logger import register_ui_sink, unregister_ui_sink

logger = get_logger(__name__)

@dataclass
class ConsoleMiddlewareConfig(MiddlewareConfig):
    middleware_connect_type: str = "direct"
    bot_name: str = "BOT"
    bot_id: str = "111"
    user_name: str = "USER"
    user_id: str = "222"

class ChatPanel(RichLog):
    def __init__(self, **kwargs):
        super().__init__(id="chat-log", wrap=True, max_lines=1000, **kwargs)
        self.messages = []
    def add_message(self, user: str, content: str, is_bot: bool = False):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "🤖" if is_bot else "👤"
        style = "bold blue" if is_bot else "bold green"
        text = Text(f"{emoji} [{timestamp}] {user}: ", style=style)
        text.append(content, style="white")
        self.write(text)
        self.messages.append({"user": user, "content": content, "is_bot": is_bot, "timestamp": timestamp})
        self.scroll_end(animate=False)

class LogPanel(RichLog):
    def __init__(self, **kwargs):
        super().__init__(id="system-log", wrap=True, max_lines=1000, **kwargs)
    def add_log(self, level: str, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_config = {
            "DEBUG": {"color": "dim", "emoji": "🐛"},
            "INFO": {"color": "blue", "emoji": "ℹ️"},
            "WARNING": {"color": "yellow", "emoji": "⚠️"},
            "ERROR": {"color": "red", "emoji": "❌"},
            "CRITICAL": {"color": "bold red", "emoji": "💥"}
        }
        config = level_config.get(level, {"color": "white", "emoji": "📝"})
        text = Text(f"{config['emoji']} [{timestamp}] {level}: ", style=config['color'] + " bold")
        text.append(message, style="white")
    self.write(text)
    self.scroll_end(animate=False)
    # 现在日志由 loguru 直接写入并通过 UI sink广播到这里，
    # 因此不在此处重复写回 loguru，防止产生重复条目。

class ConsoleApp(App):
    CSS = """
    Horizontal { height: 100%; }
    .chat-panel { width: 60%; border: solid $primary; margin: 1; }
    .log-panel { width: 40%; border: solid $secondary; margin: 1; }
    .input-container { height: 3; margin: 1; }
    .send-button { width: 3; content-align: center middle; background: $primary; color: $surface; margin-left: 1; border: solid $primary; }
    .send-button:hover { background: $primary-darken-1; }
    Input { margin: 1; }
    #chat-log { height: 1fr; border: solid $surface; margin: 1; }
    #system-log { height: 1fr; border: solid $surface; margin: 1; }
    """
    BINDINGS = [ ("ctrl+k", "command_palette", "Command Palette") ]
    def __init__(self, middleware: 'ConsoleMiddleware'):
        super().__init__()
        self.middleware = middleware
        self.chat_panel: ChatPanel = ChatPanel()
        self.log_panel: LogPanel = LogPanel()
    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Static("💬 聊天室", id="chat-title"),
                self.chat_panel,
                Horizontal(
                    Input(placeholder="输入消息...", id="message-input"),
                    Button("📤", id="send-button", classes="send-button"),
                    classes="input-container"
                ),
                classes="chat-panel"
            ),
            Vertical(
                Static("📋 系统日志", id="log-title"),
                self.log_panel,
                classes="log-panel"
            )
        )
        yield Footer()
    def on_mount(self) -> None:
        self.chat_panel.add_message(
            self.middleware.config.bot_name,
            "机器人已启动，输入 help 查看可用命令",
            is_bot=True
        )
        # 系统日志示例
    logger = get_logger(__name__)
    logger.info("机器人实例已创建")
    logger.info("启动机器人...")
    logger.info("加载插件...")
    logger.info("总共加载了 0 个插件")
    logger.info("启动中间件...")
    logger.info(f"中间件 {self.middleware.name} 加载成功")
    logger.info(f"启动控制台中间件: {self.middleware.name}")
    logger.info("控制台中间件已启动")
    logger.info("启动了 1 个中间件")
    logger.info("机器人启动成功")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message-input":
            self._send_message(event.input)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-button":
            input_widget = self.query_one("#message-input", Input)
            self._send_message(input_widget)
    def _send_message(self, input_widget: Input) -> None:
        content = input_widget.value.strip()
        if content:
            self.chat_panel.add_message(
                self.middleware.config.user_name,
                content,
                is_bot=False
            )
            # 立刻在右侧日志记录发送的消息，确保用户可见
            try:
                if self.log_panel:
                    self.log_panel.add_log("INFO", f"发送消息: {content}")
            except Exception:
                pass
            asyncio.create_task(self.middleware._process_user_input(content))
            input_widget.value = ""

@register_middleware("iamai.middleware.console")
class ConsoleMiddleware(Middleware):
    def __init__(self, name: str, config: ConsoleMiddlewareConfig, bot: 'Bot'):
        super().__init__(name, config, bot)
        self.app: ConsoleApp = None
        self.input_task = None
    async def start(self) -> None:
        if not self.enabled:
            return
        logger.info(f"启动控制台中间件: {self.name}")
        self.app = ConsoleApp(self)
        # 注册 UI 日志接收器，使 loguru 的日志能显示在右侧 LogPanel
        def _ui_sink(level: str, message: str):
            try:
                if self.app and self.app.log_panel:
                    self.app.log_panel.add_log(level, message)
            except Exception:
                pass

        self._ui_sink = _ui_sink
        register_ui_sink(self._ui_sink)
        self.input_task = asyncio.create_task(self._run_app())
        self.connected = True
        logger.info("控制台中间件已启动")
    async def stop(self) -> None:
        logger.info(f"停止控制台中间件: {self.name}")
        # 注销 UI 日志接收器
        try:
            unregister_ui_sink(self._ui_sink)
        except Exception:
            pass

        if self.input_task:
            self.input_task.cancel()
            try:
                await self.input_task
            except asyncio.CancelledError:
                pass
        self.connected = False
        logger.info("控制台中间件已停止")
    async def _run_app(self) -> None:
        try:
            await self.app.run_async()
        except Exception as e:
            logger.error(f"控制台应用运行错误: {e}")
    async def send_message(self, content: str, channel_id: str, **kwargs) -> None:
        # 记录发送日志（会通过 loguru 广播到右侧 LogPanel）
        logger.info(f"ConsoleMiddleware.send_message called: {content}")

        async def _do_add():
            try:
                if self.app and self.app.chat_panel:
                    self.app.chat_panel.add_message(
                        self.config.bot_name,
                        content,
                        is_bot=True
                    )
            except Exception as e:
                logger.error(f"向 UI 添加消息失败: {e}")

        # 尝试在事件循环中异步调度 UI 更新，以兼容 Textual 的事件循环
        try:
            asyncio.create_task(_do_add())
        except Exception:
            # 退化到直接调用
            try:
                _do_add()
            except Exception:
                pass
    async def _process_user_input(self, content: str) -> None:
        try:
            message = MessageBuilder.create_console_message(
                content=content,
                user_id=self.config.user_id,
                channel_id="console_channel",
                user_name=self.config.user_name
            )
            event = message.to_event()
            # 直接调用 bot.process_event 以获取处理结果，并在 UI 日志中记录
            if not self.enabled:
                return
            results = await self.bot.process_event(event, self)
            # 在日志面板记录收到的消息和处理结果，以便在右侧日志可见
            if self.app and self.app.log_panel:
                try:
                    self.app.log_panel.add_log("INFO", f"收到消息 from {self.config.user_name}: {content}")
                    self.app.log_panel.add_log("INFO", f"消息已处理: {len(results)} 条规则执行返回结果 | results={results}")
                except Exception:
                    # 不影响主流程
                    pass
        except Exception as e:
            logger.error(f"处理用户输入时出错: {e}")
            if self.app and self.app.log_panel:
                self.app.log_panel.add_log("ERROR", f"处理消息时出错: {e}")
    def create_event(self, raw_data: Any, **fields) -> Event:
        if isinstance(raw_data, dict) and 'content' in raw_data:
            message = MessageBuilder.create_console_message(
                content=raw_data['content'],
                user_id=raw_data.get('user_id', self.config.user_id),
                channel_id=raw_data.get('channel_id', 'console_channel'),
                user_name=raw_data.get('user_name', self.config.user_name),
                **fields
            )
            return message.to_event()
        else:
            return Event(
                type='custom',
                platform='console',
                raw_data=raw_data,
                **fields
            )
    async def connect_direct(self) -> None:
        self.connected = True
        logger.info("控制台中间件已连接")
    def add_log(self, level: str, message: str) -> None:
        if self.app and self.app.log_panel:
            self.app.log_panel.add_log(level, message)
