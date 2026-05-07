from __future__ import annotations

from iamai import Context, Plugin, middleware


class SessionPlugin(Plugin):
    name = "session"
    description = "Shared player session state and lifecycle middleware."

    @middleware(phase="before", priority=0)
    async def ensure_profile(self, ctx: Context) -> None:
        players = self.state.setdefault("players", {})
        user_id = ctx.event.user_id or "guest"
        profile = players.setdefault(
            user_id,
            {
                "coins": int(self.config.get("starting_coins", 20)),
                "spins": 0,
                "wins": 0,
                "history": [],
            },
        )
        ctx.shared_state["active_player"] = user_id
        ctx.shared_state["active_profile"] = profile

    @middleware(phase="after", priority=100)
    async def remember_success(self, ctx: Context) -> None:
        if not ctx.command_name:
            return
        profile = ctx.shared_state.get("active_profile")
        if not isinstance(profile, dict):
            return
        history = profile.setdefault("history", [])
        history.append(ctx.event.text)
        del history[:-5]

    @middleware(phase="error", priority=0)
    async def handle_arcade_errors(self, ctx: Context, error: Exception) -> bool:
        await ctx.reply(f"arcade meltdown: {error}")
        return True
