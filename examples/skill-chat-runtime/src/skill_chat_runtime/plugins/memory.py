from __future__ import annotations

import logging

from iamai import Context, Plugin, command, middleware
from pydantic import BaseModel

from skill_chat_runtime.skilllib import TraceRecord, format_trace

logger = logging.getLogger(__name__)


class MemoryConfig(BaseModel):
    """Configuration for the memory plugin."""

    note_limit: int = 12
    trace_limit: int = 8


class MemoryPlugin(Plugin):
    """Persistent notes and trace buffers for the skill-chat loop."""

    name = "memory"
    description = "Persistent notes and trace buffers for the skill-chat loop."
    state_scope = "persistent"
    config_model = MemoryConfig

    @middleware(phase="before", priority=0)
    async def ensure_buffers(self, ctx: Context) -> None:
        """Ensure notes, traces, and last_error keys exist in plugin state."""
        self.state.setdefault("notes", [])
        self.state.setdefault("traces", [])
        self.state.setdefault("last_error", "")

    def append_trace(self, trace: TraceRecord | dict[str, object]) -> TraceRecord:
        """Store a trace record, trimming the buffer to the configured limit."""
        record = trace if isinstance(trace, TraceRecord) else TraceRecord.model_validate(trace)
        traces = self.state.setdefault("traces", [])
        traces.append(record.model_dump(mode="python"))
        limit = int(self.config.get("trace_limit", 8))
        if len(traces) > limit:
            del traces[:-limit]
        logger.info(
            "trace stored trace_id=%s status=%s tool=%s",
            record.trace_id,
            record.status,
            record.tool_name,
        )
        return record

    def last_trace(self) -> TraceRecord | None:
        """Return the most recent trace record, or None if no traces exist."""
        traces = self.state.get("traces", [])
        if not traces:
            return None
        return TraceRecord.model_validate(traces[-1])

    @middleware(phase="error", priority=0)
    async def explain_agent_error(self, ctx: Context, error: Exception) -> bool:
        """Log errors and reply with a friendly message for router failures."""
        self.state["last_error"] = str(error)
        logger.error("skill-chat error: %s", error)
        if ctx.plugin.plugin_name != "router":
            return False
        await ctx.reply(f"skill-chat stopped: {error}")
        return True

    @command("trace", priority=80)
    async def trace(self, ctx: Context) -> None:
        """Display the most recent execution trace."""
        trace = self.last_trace()
        if trace is None:
            await ctx.reply("No trace recorded yet.")
            return
        await ctx.reply(format_trace(trace))

    @command("traces", priority=81)
    async def traces(self, ctx: Context) -> None:
        """List the last 6 execution traces with status and tool info."""
        traces = self.state.get("traces", [])
        if not traces:
            await ctx.reply("No trace recorded yet.")
            return
        items = [TraceRecord.model_validate(item) for item in traces[-6:]]
        lines = [f"recent traces: total={len(traces)}"]
        for item in items:
            lines.append(
                f"- {item.trace_id} status={item.status} tool={item.tool_name} "
                f"path={' -> '.join(item.path) if item.path else item.tool_name}"
            )
        await ctx.reply("\n".join(lines))

    @command("successes", priority=82)
    async def successes(self, ctx: Context) -> None:
        """List the last 6 successful traces."""
        items = [
            TraceRecord.model_validate(item)
            for item in self.state.get("traces", [])
            if item.get("status") == "success"
        ]
        if not items:
            await ctx.reply("No successful trace recorded yet.")
            return
        lines = ["recent success traces:"]
        for item in items[-6:]:
            lines.append(f"- {item.trace_id} tool={item.tool_name} skill={item.skill_id or '-'}")
        await ctx.reply("\n".join(lines))

    @command("failures", priority=83)
    async def failures(self, ctx: Context) -> None:
        """List the last 6 failed traces with error messages."""
        items = [
            TraceRecord.model_validate(item)
            for item in self.state.get("traces", [])
            if item.get("status") == "failure"
        ]
        if not items:
            await ctx.reply("No failed trace recorded yet.")
            return
        lines = ["recent failure traces:"]
        for item in items[-6:]:
            lines.append(f"- {item.trace_id} tool={item.tool_name} error={item.error or '-'}")
        await ctx.reply("\n".join(lines))
