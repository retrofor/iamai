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
        self.log_panel.add_log("INFO", "机器人实例已创建")
        self.log_panel.add_log("INFO", "启动机器人...")
        self.log_panel.add_log("INFO", "加载插件...")
        self.log_panel.add_log("INFO", "总共加载了 0 个插件")
        self.log_panel.add_log("INFO", "启动中间件...")
        self.log_panel.add_log("INFO", f"中间件 {self.middleware.name} 加载成功")
        self.log_panel.add_log("INFO", f"启动控制台中间件: {self.middleware.name}")
        self.log_panel.add_log("INFO", "控制台中间件已启动")
        self.log_panel.add_log("INFO", "启动了 1 个中间件")
        self.log_panel.add_log("INFO", "机器人启动成功")
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
        self.input_task = asyncio.create_task(self._run_app())
        self.connected = True
        logger.info("控制台中间件已启动")
    async def stop(self) -> None:
        logger.info(f"停止控制台中间件: {self.name}")
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
        if self.app and self.app.chat_panel:
            self.app.chat_panel.add_message(
                self.config.bot_name,
                content,
                is_bot=True
            )
    async def _process_user_input(self, content: str) -> None:
        try:
            message = MessageBuilder.create_console_message(
                content=content,
                user_id=self.config.user_id,
                channel_id="console_channel",
                user_name=self.config.user_name
            )
            event = message.to_event()
            await self.handle_event(event)
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
