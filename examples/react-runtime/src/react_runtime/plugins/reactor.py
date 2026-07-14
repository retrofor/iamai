from __future__ import annotations

from pathlib import Path
from typing import cast

from iamai import AgentTrace, Context, Plugin, command, message_handler
from iamai_example_utils import (
    LLMSettings,
    chat_json,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field

from react_runtime.plugins.mcp import McpPlugin
from react_runtime.plugins.memory import MemoryPlugin
from react_runtime.plugins.tools import ToolsPlugin

_SOUL_PATH = Path(__file__).resolve().parents[3] / "SOUL.md"


class ReactorConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    max_turns: int = Field(default=5, ge=1, le=20)
    chat_mode: bool = False


class ReactorPlugin(Plugin):
    name = "reactor"
    description = "Runs a ReAct loop over local tools."
    requires = ("mcp", "memory", "tools")
    load_after = ("mcp", "tools")
    config_model = ReactorConfig

    @command("ask", priority=10)
    async def ask(self, ctx: Context, args: str) -> None:
        question = args.strip()
        if not question:
            await ctx.reply("Usage: /ask <question>")
            return
        await self._run_react(ctx, question)

    @message_handler(priority=99)
    async def chat_fallback(self, ctx: Context) -> None:
        if not self.config.get("chat_mode"):
            return
        text = (ctx.event.text or "").strip()
        if not text or text.startswith("/"):
            return
        await self._run_react(ctx, text)

    async def _run_react(self, ctx: Context, question: str) -> None:
        tools = cast(ToolsPlugin, ctx.runtime.get_plugin("tools"))
        memory = cast(MemoryPlugin, ctx.runtime.get_plugin("memory"))
        mcp = cast(McpPlugin, ctx.runtime.get_plugin("mcp"))
        all_tools = f"{tools.describe_tools()}\n{mcp.describe_tools()}"
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.5, default_max_tokens=2000
        )
        soul = ""
        if _SOUL_PATH.is_file():
            soul = "\n\n## 你的人格\n" + _SOUL_PATH.read_text(encoding="utf-8").strip()
        stored_question = clip_text(question, limit=2000)
        trace = AgentTrace(f"react:{stored_question}")
        trace_lines: list[str] = []
        final_answer = ""
        was_silent = False
        for turn in range(1, max(1, int(self.config.get("max_turns", 5))) + 1):
            payload = await chat_json(
                settings,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a ReAct agent. Each turn, return ONE JSON object with "
                            "exactly ONE of these actions:\n"
                            '- {"thought":"...", "reply":"message"} - send a message\n'
                            '- {"thought":"...", "silent":true} - stay quiet\n'
                            '- {"thought":"...", "tool":"name","input":...} - call a tool\n'
                            "After a tool returns a result, end with reply or silent and do not "
                            "repeat the same tool. Local tool input is plain text; MCP tool input "
                            "may be a JSON object. Before remember, check Saved notes for duplicates."
                            + soul
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question: {question}\n\n"
                            f"Available tools:\n{all_tools}\n\n"
                            f"Saved notes:\n{format_transcript(memory.notes_for(ctx), limit=8)}\n\n"
                            f"Trace so far:\n{format_transcript(trace_lines, limit=10)}"
                        ),
                    },
                ],
                max_tokens=4000,
            )
            data = payload if isinstance(payload, dict) else {}
            thought = clip_text(str(data.get("thought", "")).strip() or f"turn {turn}", limit=120)
            reply_value = data.get("reply")
            reply = reply_value.strip() if isinstance(reply_value, str) else ""
            tool_value = data.get("tool")
            tool_name = tool_value.strip() if isinstance(tool_value, str) else ""
            action_count = sum((bool(reply), data.get("silent") is True, bool(tool_name)))
            if action_count != 1:
                final_answer = "The model returned an invalid action. Please try again."
                trace_lines.append(f"turn {turn}: thought={thought} invalid action")
                trace.add(
                    "error",
                    "invalid_action",
                    input=stored_question,
                    output=final_answer,
                    turn=turn,
                )
                break
            if reply:
                final_answer = clip_text(reply, limit=2500)
                trace_lines.append(f"turn {turn}: thought={thought} reply={final_answer}")
                trace.add("final", "answer", input=stored_question, output=final_answer, turn=turn)
                break
            if data.get("silent") is True:
                trace_lines.append(f"turn {turn}: thought={thought} silent")
                was_silent = True
                break
            tool_input_raw = data.get("input", "")
            if tool_name:
                if "." in tool_name:
                    observation = await mcp.call_tool(tool_name, tool_input_raw)
                else:
                    observation = await tools.run_tool(tool_name, str(tool_input_raw).strip(), ctx)
                trace.add(
                    "tool",
                    tool_name,
                    input=clip_text(tool_input_raw, limit=1000),
                    output=clip_text(observation, limit=4000),
                    turn=turn,
                    thought=thought,
                )
                trace_lines.append(
                    f"turn {turn}: thought={thought} "
                    f"tool={tool_name}({clip_text(str(tool_input_raw).strip(), limit=60)}) "
                    f"observation={clip_text(observation, limit=140)}"
                )
                continue
        if not final_answer and not was_silent:
            final_answer = "I reached the turn limit; inspect the trace and answer from the observations above."
        traces = memory.traces_for(ctx)
        trace.add("summary", "react", input=stored_question, output=final_answer)
        traces.append(
            {
                "question": stored_question,
                "trace": list(trace_lines),
                "final": final_answer,
                "agent_trace": trace.to_dict(),
            }
        )
        limit = int(memory.config.get("trace_limit", 6))
        if len(traces) > limit:
            del traces[:-limit]
        if ctx.event.adapter == "onebot11":
            if final_answer.strip():
                await ctx.reply(final_answer)
        else:
            lines = [f"question: {question}", *trace_lines[-6:], f"final: {final_answer}"]
            await ctx.reply("\n".join(lines))

    @command("react-trace", priority=20)
    async def show_trace(self, ctx: Context) -> None:
        memory = cast(MemoryPlugin, ctx.runtime.get_plugin("memory"))
        traces = memory.traces_for(ctx)
        if not traces:
            await ctx.reply("No trace recorded yet.")
            return
        last = traces[-1]
        lines = [
            f"last question: {last['question']}",
            *last["trace"][-6:],
            f"final: {last['final']}",
        ]
        await ctx.reply("\n".join(lines))
