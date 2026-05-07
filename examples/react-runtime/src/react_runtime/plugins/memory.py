from __future__ import annotations

from iamai import Context, Plugin, command, middleware
from pydantic import BaseModel


class MemoryConfig(BaseModel):
    note_limit: int = 12
    trace_limit: int = 6


class MemoryPlugin(Plugin):
    name = "memory"
    description = "State buffers and friendly error handling for the ReAct loop."
    config_model = MemoryConfig

    @middleware(phase="before", priority=0)
    async def ensure_buffers(self, ctx: Context) -> None:
        self.state.setdefault("notes", [])
        self.state.setdefault("traces", [])
        self.state.setdefault("last_error", "")

    @middleware(phase="error", priority=0)
    async def explain_agent_error(self, ctx: Context, error: Exception) -> bool:
        self.state["last_error"] = str(error)
        if ctx.plugin.plugin_name != "reactor":
            return False
        await ctx.reply(f"react loop stopped: {error}")
        return True

    @command("notes", priority=80)
    async def notes(self, ctx: Context) -> None:
        notes = self.state.get("notes", [])
        if not notes:
            await ctx.reply("No notes stored.")
            return
        lines = ["notes:"]
        for item in notes[-8:]:
            lines.append(f"- {item}")
        await ctx.reply("\n".join(lines))
