from __future__ import annotations

from typing import Any

from iamai import Context, Event, Plugin, command, depends, message_handler, middleware
from pydantic import BaseModel


def source_label(event: Event) -> str:
    user = event.user_id or "unknown"
    channel = event.channel_id or "private"
    return f"{event.adapter}:{user}@{channel}"


class EchoConfig(BaseModel):
    greeting: str = "你好，我是 Shinemay。"


class EchoPlugin(Plugin):
    name = "echo"
    description = "Simple echo and greeting example plugin."
    config_model = EchoConfig

    @middleware(priority=5, phase="before")
    async def track_last_event(self, ctx: Context) -> None:
        ctx.shared_state["last_event_id"] = ctx.event.id
        ctx.shared_state["last_source"] = source_label(ctx.event)

    @command("ping", priority=10)
    async def ping(self, ctx: Context, source: str = depends(source_label)) -> None:
        await ctx.reply(f"pong [{source}]")

    @command("echo", priority=20)
    async def echo(self, ctx: Context, args: str) -> None:
        if not args:
            await ctx.reply("用法: /echo <text>")
            return
        await ctx.reply(args)

    @command("whoami", priority=30)
    async def whoami(self, ctx: Context, event: Event) -> None:
        await ctx.reply(f"adapter={event.adapter} user={event.user_id} channel={event.channel_id}")

    @command("state", priority=40)
    async def show_state(self, ctx: Context, shared_state: dict[str, Any]) -> None:
        await ctx.reply(
            f"last_event_id={shared_state.get('last_event_id')} "
            f"last_source={shared_state.get('last_source')}"
        )

    @message_handler(startswith=("hi", "hello", "你好"), priority=100)
    async def greet(self, ctx: Context, source: str = depends(source_label)) -> None:
        greeting = (
            self.config_obj.greeting if self.config_obj is not None else "你好，我是 Shinemay"
        )
        await ctx.reply(f"{greeting} 当前来源: {source}")
