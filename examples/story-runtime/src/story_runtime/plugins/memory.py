from __future__ import annotations

from iamai import Context, Plugin, middleware
from pydantic import BaseModel


class MemoryConfig(BaseModel):
    default_setting: str = "floating city"


class MemoryPlugin(Plugin):
    name = "memory"
    description = "Shared story state and event middleware."
    config_model = MemoryConfig

    @middleware(phase="before", priority=0)
    async def ensure_story(self, ctx: Context) -> None:
        story = self.state.setdefault(
            "story",
            {
                "setting": (
                    self.config_obj.default_setting
                    if self.config_obj is not None
                    else "floating city"
                ),
                "cast": [],
                "scenes": [],
            },
        )
        ctx.shared_state["story"] = story

    @middleware(phase="after", priority=50)
    async def mark_last_action(self, ctx: Context) -> None:
        if ctx.command_name:
            self.state["story"]["last_action"] = ctx.command_name

    @middleware(phase="error", priority=0)
    async def soften_story_errors(self, ctx: Context, error: Exception) -> bool:
        await ctx.reply(f"故事线断了：{error}")
        return True
