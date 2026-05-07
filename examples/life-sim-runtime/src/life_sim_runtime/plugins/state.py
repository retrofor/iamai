from __future__ import annotations

import random

from iamai import Context, Plugin, command, middleware

DEFAULT_NAMES = ["Mira", "Jun", "Tao", "Nova", "Ren", "Sol"]


def make_default_life(*, theme: str = "slice-of-life") -> dict:
    return {
        "name": random.choice(DEFAULT_NAMES),
        "theme": theme,
        "age": 18,
        "stats": {
            "wealth": 5,
            "health": 6,
            "joy": 6,
            "reputation": 4,
        },
        "history": [f"You begin a new {theme} life with equal parts doubt and momentum."],
        "pending_scene": None,
    }


class LifeStatePlugin(Plugin):
    name = "life_state"
    description = "Shared state and error handling for the life simulator."
    state_scope = "persistent"
    load_before = ("life",)

    @middleware(phase="before", priority=0)
    async def ensure_life(self, ctx: Context) -> None:
        self.state.setdefault("life", make_default_life())

    @middleware(phase="error", priority=0)
    async def soften_errors(self, ctx: Context, error: Exception) -> bool:
        if ctx.plugin.plugin_name != "life":
            return False
        await ctx.reply(f"timeline wobble: {error}")
        return True

    @command("history", priority=80)
    async def history(self, ctx: Context) -> None:
        history = self.state["life"].get("history", [])
        lines = ["history:"]
        for item in history[-8:]:
            lines.append(f"- {item}")
        await ctx.reply("\n".join(lines))
