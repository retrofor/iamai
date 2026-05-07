from __future__ import annotations

from typing import Any

from iamai import Context, Plugin, command
from iamai_example_utils import (
    LLMSettings,
    chat_json,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field


class PlannerConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    max_steps: int = 4


class PlannerPlugin(Plugin):
    name = "planner"
    description = "Builds compact execution plans."
    requires = ("session",)
    config_model = PlannerConfig

    async def build_plan(
        self,
        goal: str,
        *,
        recent_runs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.4, default_max_tokens=700
        )
        max_steps = max(2, min(int(self.config.get("max_steps", 4)), 6))
        history_lines = [
            f"- goal={item.get('goal', '')} outcome={clip_text(item.get('summary', ''), limit=120)}"
            for item in (recent_runs or [])[-3:]
        ]
        payload = await chat_json(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a concise planner. Break a goal into a realistic sequence of steps. "
                        f"Return no more than {max_steps} steps."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal:\n{goal}\n\n"
                        "Recent runs:\n"
                        f"{format_transcript(history_lines, limit=3)}\n\n"
                        "Return JSON with keys title, strategy, and steps. "
                        "Each step should include step, deliverable, and done_when."
                    ),
                },
            ],
        )
        data = payload if isinstance(payload, dict) else {}
        raw_steps = data.get("steps", [])
        steps: list[dict[str, str]] = []
        if isinstance(raw_steps, list):
            for item in raw_steps[:max_steps]:
                if not isinstance(item, dict):
                    continue
                step_text = clip_text(
                    str(item.get("step", "")).strip() or "Do the next useful thing."
                )
                steps.append(
                    {
                        "step": step_text,
                        "deliverable": clip_text(
                            str(item.get("deliverable", "")).strip() or "A concrete output."
                        ),
                        "done_when": clip_text(
                            str(item.get("done_when", "")).strip()
                            or "The step is demonstrably complete."
                        ),
                    }
                )
        if not steps:
            steps = [
                {
                    "step": "Clarify the desired outcome.",
                    "deliverable": "A crisp outcome statement.",
                    "done_when": "The goal fits in one sentence.",
                },
                {
                    "step": "Produce the first draft.",
                    "deliverable": "A usable draft or checklist.",
                    "done_when": "Someone can act on it immediately.",
                },
            ]
        return {
            "title": clip_text(str(data.get("title", "")).strip() or goal, limit=80),
            "strategy": clip_text(
                str(data.get("strategy", "")).strip()
                or "Front-load clarity, then execute in order.",
                limit=180,
            ),
            "steps": steps,
        }

    @command("plan", priority=10)
    async def plan(self, ctx: Context, args: str) -> None:
        goal = args.strip()
        if not goal:
            await ctx.reply("Usage: /plan <goal>")
            return
        session = ctx.runtime.get_plugin("session")
        plan = await self.build_plan(goal, recent_runs=session.state.get("runs", []))
        lines = [f"plan: {plan['title']}", f"strategy: {plan['strategy']}"]
        for index, step in enumerate(plan["steps"], start=1):
            lines.append(f"{index}. {step['step']} -> {step['deliverable']}")
        await ctx.reply("\n".join(lines))
