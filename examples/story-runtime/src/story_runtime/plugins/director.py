from __future__ import annotations

import random
from typing import Any, cast

from iamai import (
    Context,
    Plugin,
    Runtime,
    any_rules,
    command,
    contains,
    depends,
    message_handler,
    startswith,
    superusers,
)
from pydantic import BaseModel


def story_state(runtime: Runtime) -> dict[str, Any]:
    memory = runtime.get_plugin("memory")
    return cast(dict[str, Any], memory.state["story"])


class DirectorConfig(BaseModel):
    narrator: str = "旁白"


class DirectorPlugin(Plugin):
    name = "director"
    description = "Scene generation and recap commands."
    requires = ("memory",)
    optional_requires = ("cast", "world")
    config_model = DirectorConfig

    @command("scene", priority=10)
    async def scene(
        self, ctx: Context, args: str, story: dict[str, Any] = depends(story_state)
    ) -> None:
        narrator = self.config_obj.narrator if self.config_obj is not None else "旁白"
        prompt = args or "未知事件"
        cast_names = ", ".join(item["name"] for item in story.get("cast", [])[:3]) or "无名旅人"
        line = f"{narrator}: 在 {story['setting']}，{cast_names} 卷入了「{prompt}」。"
        story.setdefault("scenes", []).append(line)
        await ctx.reply(line)

    @command("twist", priority=20)
    async def twist(self, ctx: Context, story: dict[str, Any] = depends(story_state)) -> None:
        options = [
            "其实整座城市是倒着漂浮的。",
            "每一句对话都被月亮偷偷删改过。",
            "主角刚收到来自未来的求救短信。",
        ]
        line = random.choice(options)
        story.setdefault("scenes", []).append(line)
        await ctx.reply(line)

    @message_handler(
        priority=30,
        rule=any_rules(startswith("继续"), startswith("continue"), contains("下一幕")),
    )
    async def continue_story(
        self, ctx: Context, story: dict[str, Any] = depends(story_state)
    ) -> None:
        next_beat = f"scene-count={len(story.get('scenes', []))} setting={story['setting']}"
        await ctx.reply(f"故事继续推进，{next_beat}")

    @command("recap", priority=40)
    async def recap(self, ctx: Context, story: dict[str, Any] = depends(story_state)) -> None:
        scenes = story.get("scenes", [])
        if not scenes:
            await ctx.reply("故事还没开始。")
            return
        tail = scenes[-3:]
        await ctx.reply("recap:\n" + "\n".join(tail))

    @command("panic", priority=50, permission=superusers())
    async def panic(self, ctx: Context) -> None:
        raise RuntimeError("导演喊停，剧本掉进了海里")
