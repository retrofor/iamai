from __future__ import annotations

from typing import Any, cast

from iamai import Context, Plugin, command, middleware
from pydantic import BaseModel, Field


class MemoryConfig(BaseModel):
    note_limit: int = 12
    trace_limit: int = 6
    session_limit: int = Field(default=256, ge=1)


class MemoryPlugin(Plugin):
    name = "memory"
    description = "State buffers and friendly error handling for the ReAct loop."
    config_model = MemoryConfig

    def session_state(self, ctx: Context) -> dict[str, Any]:
        sessions = cast(
            dict[str, dict[str, Any]],
            self.state.setdefault("sessions", {}),
        )
        key = ctx.runtime.sessions.session_key(ctx)
        bucket = sessions.pop(key, None)
        if bucket is None:
            bucket = {}
        sessions[key] = bucket
        session_limit = int(self.config.get("session_limit", 256))
        while len(sessions) > session_limit:
            del sessions[next(iter(sessions))]
        bucket.setdefault("notes", [])
        bucket.setdefault("traces", [])
        bucket.setdefault("last_error", "")
        return bucket

    def notes_for(self, ctx: Context) -> list[str]:
        return cast(list[str], self.session_state(ctx)["notes"])

    def traces_for(self, ctx: Context) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.session_state(ctx)["traces"])

    @middleware(phase="before", priority=0)
    async def ensure_buffers(self, ctx: Context) -> None:
        self.session_state(ctx)

    @middleware(phase="error", priority=0)
    async def explain_agent_error(self, ctx: Context, error: Exception) -> bool:
        self.session_state(ctx)["last_error"] = str(error)
        if ctx.plugin.plugin_name != "reactor":
            return False
        await ctx.reply(f"react loop stopped: {error}")
        return True

    @command("notes", priority=80)
    async def notes(self, ctx: Context) -> None:
        notes = self.notes_for(ctx)
        if not notes:
            await ctx.reply("No notes stored.")
            return
        lines = ["notes:"]
        for item in notes[-8:]:
            lines.append(f"- {item}")
        await ctx.reply("\n".join(lines))
