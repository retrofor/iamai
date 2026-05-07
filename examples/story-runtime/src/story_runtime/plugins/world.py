from __future__ import annotations

from typing import Any

from iamai import Context, Plugin, command


class WorldPlugin(Plugin):
    name = "world"
    description = "World-setting commands that should load before the director."
    requires = ("memory",)
    load_before = ("director",)

    @command("where", priority=10)
    async def where(self, ctx: Context, args: str, shared_state: dict[str, Any]) -> None:
        if not args:
            raise ValueError("用法: /where <setting>")
        shared_state["story"]["setting"] = args
        await ctx.reply(f"setting => {args}")
