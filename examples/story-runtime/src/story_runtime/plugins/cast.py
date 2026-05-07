from __future__ import annotations

from typing import Any

from iamai import Context, Plugin, command


class CastPlugin(Plugin):
    name = "cast"
    description = "Character casting commands."
    requires = ("memory",)

    @command("cast", priority=10)
    async def cast(self, ctx: Context, args: str, shared_state: dict[str, Any]) -> None:
        if ":" not in args:
            raise ValueError("用法: /cast <name>:<role>")
        name, role = [part.strip() for part in args.split(":", 1)]
        if not name or not role:
            raise ValueError("角色名和身份都不能为空")
        cast_list = shared_state["story"].setdefault("cast", [])
        cast_list.append({"name": name, "role": role})
        await ctx.reply(f"casted {name} as {role}")
