from __future__ import annotations

from typing import Any, cast

from iamai import Context, Event, Plugin, Runtime, command, depends, superusers
from pydantic import BaseModel, Field


class QuestsConfig(BaseModel):
    daily_goal: int = Field(default=30, ge=1, le=10000)


def current_profile(runtime: Runtime, event: Event) -> dict[str, Any]:
    session = runtime.get_plugin("session")
    players = session.state.setdefault("players", {})
    return cast(dict[str, Any], players[event.user_id or "guest"])


class QuestsPlugin(Plugin):
    name = "quests"
    description = "Goal and leaderboard commands built on top of session + arcade."
    requires = ("session", "arcade")
    config_model = QuestsConfig

    @command("quest", priority=10)
    async def quest(self, ctx: Context, profile: dict[str, Any] = depends(current_profile)) -> None:
        goal = int(self.config_obj.daily_goal if self.config_obj is not None else 30)
        coins = int(profile.get("coins", 0))
        if coins >= goal:
            await ctx.reply(f"quest clear: coins={coins} 已达到今日目标 {goal}")
            return
        await ctx.reply(f"quest: 再赚 {goal - coins} coins 就能清掉今日任务")

    @command("leaderboard", priority=20, permission=superusers())
    async def leaderboard(self, ctx: Context, runtime: Runtime) -> None:
        session = runtime.get_plugin("session")
        players = session.state.get("players", {})
        ranking = sorted(
            players.items(),
            key=lambda item: (-int(item[1].get("coins", 0)), item[0]),
        )[:5]
        if not ranking:
            await ctx.reply("leaderboard is empty")
            return
        lines = ["leaderboard:"]
        for index, (user_id, profile) in enumerate(ranking, start=1):
            lines.append(f"{index}. {user_id} coins={profile.get('coins', 0)}")
        await ctx.reply("\n".join(lines))
