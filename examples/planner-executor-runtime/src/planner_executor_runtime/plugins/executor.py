from __future__ import annotations

from typing import Any, cast

from iamai import Context, Plugin, command
from iamai_example_utils import (
    LLMSettings,
    chat_json,
    chat_text,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field

from planner_executor_runtime.plugins.planner import PlannerPlugin


class ExecutorConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)


class ExecutorPlugin(Plugin):
    name = "executor"
    description = "Executes a plan step by step and produces a final handoff."
    requires = ("session", "planner")
    load_after = ("planner",)
    config_model = ExecutorConfig

    async def _run_step(
        self,
        goal: str,
        strategy: str,
        step: dict[str, str],
        completed: list[dict[str, str]],
    ) -> dict[str, str]:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.7, default_max_tokens=700
        )
        notes = [
            f"- {item['step']}: {clip_text(item['result'], limit=140)}" for item in completed[-3:]
        ]
        payload = await chat_json(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an execution agent. Produce the best possible output for one plan step. "
                        "Stay concrete and useful."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\n"
                        f"Strategy: {strategy}\n"
                        f"Current step: {step['step']}\n"
                        f"Deliverable: {step['deliverable']}\n"
                        f"Done when: {step['done_when']}\n\n"
                        "Completed notes:\n"
                        f"{format_transcript(notes, limit=3)}\n\n"
                        "Return JSON with result, artifact, and risk."
                    ),
                },
            ],
        )
        data = payload if isinstance(payload, dict) else {}
        return {
            "step": step["step"],
            "result": clip_text(
                str(data.get("result", "")).strip() or "Produced a useful draft output.",
                limit=220,
            ),
            "artifact": clip_text(
                str(data.get("artifact", "")).strip() or step["deliverable"],
                limit=140,
            ),
            "risk": clip_text(
                str(data.get("risk", "")).strip() or "May need a quick review for polish.",
                limit=140,
            ),
        }

    async def _summarize_run(
        self,
        goal: str,
        strategy: str,
        steps: list[dict[str, str]],
    ) -> str:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.5, default_max_tokens=420
        )
        transcript = [
            f"- {item['step']}: {item['result']} (artifact={item['artifact']}, risk={item['risk']})"
            for item in steps
        ]
        return await chat_text(
            settings,
            [
                {
                    "role": "system",
                    "content": "Summarize an execution run into a compact handoff note.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\nStrategy: {strategy}\n"
                        f"Steps:\n{format_transcript(transcript, limit=8)}\n\n"
                        "Write a short final handoff."
                    ),
                },
            ],
            max_tokens=420,
        )

    @command("execute", priority=20)
    async def execute(self, ctx: Context, args: str) -> None:
        goal = args.strip()
        if not goal:
            await ctx.reply("Usage: /execute <goal>")
            return
        session = ctx.runtime.get_plugin("session")
        planner = cast(PlannerPlugin, ctx.runtime.get_plugin("planner"))
        recent_runs = cast(list[dict[str, Any]], session.state.get("runs", []))
        plan = await planner.build_plan(goal, recent_runs=recent_runs)
        completed: list[dict[str, str]] = []
        for step in plan["steps"]:
            completed.append(await self._run_step(goal, plan["strategy"], step, completed))
        summary = await self._summarize_run(goal, plan["strategy"], completed)
        run = {
            "goal": goal,
            "title": plan["title"],
            "strategy": plan["strategy"],
            "steps": completed,
            "summary": clip_text(summary, limit=400),
            "status": "done",
        }
        runs = session.state.setdefault("runs", [])
        runs.append(run)
        limit = int(session.config.get("history_limit", 6))
        if len(runs) > limit:
            del runs[:-limit]
        lines = [f"executed: {plan['title']}", f"strategy: {plan['strategy']}"]
        for index, item in enumerate(completed, start=1):
            lines.append(f"{index}. {item['step']} => {item['result']}")
        lines.append(f"handoff: {run['summary']}")
        await ctx.reply("\n".join(lines))

    @command("last", priority=30)
    async def last(self, ctx: Context) -> None:
        session = ctx.runtime.get_plugin("session")
        runs = session.state.get("runs", [])
        if not runs:
            await ctx.reply("No execution history yet.")
            return
        latest = runs[-1]
        lines = [f"last goal: {latest['goal']}", f"summary: {latest['summary']}"]
        for index, item in enumerate(latest.get("steps", []), start=1):
            lines.append(f"{index}. {item['step']} -> {item['artifact']}")
        await ctx.reply("\n".join(lines))
