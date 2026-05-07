from __future__ import annotations

from iamai import Context, Plugin, command, middleware


class BriefingPlugin(Plugin):
    name = "briefing"
    description = "Shared state for supervisor runs."
    load_before = ("workers", "supervisor")

    @middleware(phase="before", priority=0)
    async def ensure_briefing_state(self, ctx: Context) -> None:
        self.state.setdefault("runs", [])
        self.state.setdefault("goals", [])

    @middleware(phase="after", priority=90)
    async def keep_goal_queue_warm(self, ctx: Context) -> None:
        if ctx.command_name == "team" and ctx.args:
            goals = self.state.setdefault("goals", [])
            goals.append(ctx.args)
            if len(goals) > 8:
                del goals[:-8]

    @command("queue", priority=70)
    async def queue(self, ctx: Context) -> None:
        goals = self.state.get("goals", [])
        if not goals:
            await ctx.reply("Goal queue is empty.")
            return
        lines = ["recent goals:"]
        for item in goals[-5:]:
            lines.append(f"- {item}")
        await ctx.reply("\n".join(lines))
