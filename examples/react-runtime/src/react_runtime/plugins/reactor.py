from __future__ import annotations

from typing import cast

from iamai import AgentTrace, Context, Plugin, command
from iamai_example_utils import (
    LLMSettings,
    chat_json,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field

from react_runtime.plugins.tools import ToolsPlugin


class ReactorConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    max_turns: int = 5


class ReactorPlugin(Plugin):
    name = "reactor"
    description = "Runs a ReAct loop over local tools."
    requires = ("memory", "tools")
    load_after = ("tools",)
    config_model = ReactorConfig

    @command("ask", priority=10)
    async def ask(self, ctx: Context, args: str) -> None:
        question = args.strip()
        if not question:
            await ctx.reply("Usage: /ask <question>")
            return
        tools = cast(ToolsPlugin, ctx.runtime.get_plugin("tools"))
        memory = ctx.runtime.get_plugin("memory")
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.5, default_max_tokens=500
        )
        trace = AgentTrace(f"react:{question}")
        trace_lines: list[str] = []
        final_answer = ""
        for turn in range(1, max(1, int(self.config.get("max_turns", 5))) + 1):
            payload = await chat_json(
                settings,
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a ReAct assistant. Think briefly, then either call one tool or finish. "
                            "Return JSON with thought and either action{tool,input} or final."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question: {question}\n\n"
                            f"Available tools:\n{tools.describe_tools()}\n\n"
                            f"Saved notes:\n{format_transcript(memory.state.get('notes', []), limit=8)}\n\n"
                            f"Trace so far:\n{format_transcript(trace_lines, limit=10)}"
                        ),
                    },
                ],
                max_tokens=420,
            )
            data = payload if isinstance(payload, dict) else {}
            thought = clip_text(str(data.get("thought", "")).strip() or f"turn {turn}", limit=120)
            final = str(data.get("final", "")).strip()
            if final:
                final_answer = clip_text(final, limit=300)
                trace_lines.append(f"turn {turn}: thought={thought} final={final_answer}")
                trace.add("final", "answer", input=question, output=final_answer, turn=turn)
                break
            action = data.get("action", {})
            if not isinstance(action, dict):
                raise ValueError("model returned an invalid action payload")
            tool_name = str(action.get("tool", "")).strip()
            tool_input = str(action.get("input", "")).strip()
            if not tool_name:
                raise ValueError("model did not choose a tool or final answer")
            observation = await tools.run_tool(tool_name, tool_input, ctx)
            trace.add(
                "tool",
                tool_name,
                input=tool_input,
                output=observation,
                turn=turn,
                thought=thought,
            )
            trace_lines.append(
                f"turn {turn}: thought={thought} action={tool_name}({clip_text(tool_input, limit=60)}) "
                f"observation={clip_text(observation, limit=140)}"
            )
        if not final_answer:
            final_answer = "I reached the turn limit; inspect the trace and answer from the observations above."
        traces = memory.state.setdefault("traces", [])
        trace.add("summary", "react", input=question, output=final_answer)
        traces.append(
            {
                "question": question,
                "trace": list(trace_lines),
                "final": final_answer,
                "agent_trace": trace.to_dict(),
            }
        )
        limit = int(memory.config.get("trace_limit", 6))
        if len(traces) > limit:
            del traces[:-limit]
        lines = [f"question: {question}", *trace_lines[-6:], f"final: {final_answer}"]
        await ctx.reply("\n".join(lines))

    @command("react-trace", priority=20)
    async def trace(self, ctx: Context) -> None:
        memory = ctx.runtime.get_plugin("memory")
        traces = memory.state.get("traces", [])
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
