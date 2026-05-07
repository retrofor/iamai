from __future__ import annotations

from iamai import Context, Plugin, command, middleware
from pydantic import BaseModel


class SessionConfig(BaseModel):
    history_limit: int = 6


class SessionPlugin(Plugin):
    name = "session"
    description = "Shared run history for planner / executor workflows."
    config_model = SessionConfig

    @middleware(phase="before", priority=0)
    async def ensure_session(self, ctx: Context) -> None:
        self.state.setdefault("runs", [])
        self.state.setdefault("last_command", "")
        ctx.shared_state["planner_executor_runs"] = self.state["runs"]

    @middleware(phase="after", priority=90)
    async def remember_last_command(self, ctx: Context) -> None:
        if ctx.command_name is not None:
            self.state["last_command"] = ctx.command_name

    @command("runs", priority=70)
    async def runs(self, ctx: Context) -> None:
        runs = self.state.get("runs", [])
        if not runs:
            await ctx.reply("No execution runs yet.")
            return
        lines = ["recent runs:"]
        for item in runs[-5:]:
            lines.append(
                f"- {item['goal']} ({len(item.get('steps', []))} steps, {item.get('status', 'done')})"
            )
        await ctx.reply("\n".join(lines))
