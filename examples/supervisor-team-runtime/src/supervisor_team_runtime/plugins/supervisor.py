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

from supervisor_team_runtime.plugins.workers import WorkersPlugin


class SupervisorConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)


class SupervisorPlugin(Plugin):
    name = "supervisor"
    description = "Coordinates a small specialist team and synthesizes the result."
    requires = ("briefing", "workers")
    load_after = ("workers",)
    config_model = SupervisorConfig

    async def _make_assignments(
        self,
        goal: str,
        recent_goals: list[str],
    ) -> dict[str, Any]:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.5, default_max_tokens=650
        )
        payload = await chat_json(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a supervisor coordinating strategist, builder, and skeptic workers. "
                        "Decide what each worker should do."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\n"
                        f"Recent goals:\n{format_transcript([f'- {item}' for item in recent_goals], limit=5)}\n\n"
                        "Return JSON with objective, synthesis_brief, and assignments. "
                        "assignments should be a list of {role, task}."
                    ),
                },
            ],
        )
        data = payload if isinstance(payload, dict) else {}
        assignments = data.get("assignments", [])
        normalized: list[dict[str, str]] = []
        if isinstance(assignments, list):
            for item in assignments[:3]:
                if not isinstance(item, dict):
                    continue
                role = str(item.get("role", "")).strip()
                task = str(item.get("task", "")).strip()
                if not role or not task:
                    continue
                normalized.append({"role": role, "task": clip_text(task, limit=160)})
        if not normalized:
            normalized = [
                {
                    "role": "strategist",
                    "task": "Sequence the work and define priorities.",
                },
                {
                    "role": "builder",
                    "task": "Draft the key deliverable and concrete examples.",
                },
                {"role": "skeptic", "task": "List the main risks and missing pieces."},
            ]
        return {
            "objective": clip_text(str(data.get("objective", "")).strip() or goal, limit=100),
            "synthesis_brief": clip_text(
                str(data.get("synthesis_brief", "")).strip()
                or "Blend the strongest ideas into one answer.",
                limit=160,
            ),
            "assignments": normalized,
        }

    @command("team", priority=20)
    async def team(self, ctx: Context, args: str) -> None:
        goal = args.strip()
        if not goal:
            await ctx.reply("Usage: /team <goal>")
            return
        briefing = ctx.runtime.get_plugin("briefing")
        workers = cast(WorkersPlugin, ctx.runtime.get_plugin("workers"))
        assignments = await self._make_assignments(goal, briefing.state.get("goals", []))
        worker_outputs: list[dict[str, str]] = []
        for item in assignments["assignments"]:
            result = await workers.run_worker(
                role=item["role"],
                goal=goal,
                task=item["task"],
                shared_context=assignments["objective"],
            )
            worker_outputs.append(
                {
                    "role": item["role"],
                    "task": item["task"],
                    "result": clip_text(result, limit=260),
                }
            )
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.5, default_max_tokens=650
        )
        worker_lines = [f"- {item['role']}: {item['result']}" for item in worker_outputs]
        synthesis = await chat_text(
            settings,
            [
                {
                    "role": "system",
                    "content": "You are the team supervisor. Merge worker outputs into one strong answer.",
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\n"
                        f"Synthesis brief: {assignments['synthesis_brief']}\n\n"
                        "Worker outputs:\n"
                        f"{format_transcript(worker_lines, limit=6)}"
                    ),
                },
            ],
            max_tokens=420,
        )
        run = {
            "goal": goal,
            "assignments": worker_outputs,
            "summary": clip_text(synthesis, limit=400),
        }
        runs = briefing.state.setdefault("runs", [])
        runs.append(run)
        if len(runs) > 6:
            del runs[:-6]
        lines = [f"goal: {goal}"]
        for item in worker_outputs:
            lines.append(f"{item['role']}: {item['task']} => {item['result']}")
        lines.append(f"supervisor: {run['summary']}")
        await ctx.reply("\n".join(lines))

    @command("review", priority=30)
    async def review(self, ctx: Context) -> None:
        briefing = ctx.runtime.get_plugin("briefing")
        runs = briefing.state.get("runs", [])
        if not runs:
            await ctx.reply("No team run recorded yet.")
            return
        latest = runs[-1]
        lines = [f"last goal: {latest['goal']}"]
        for item in latest.get("assignments", []):
            lines.append(f"{item['role']}: {item['result']}")
        lines.append(f"summary: {latest['summary']}")
        await ctx.reply("\n".join(lines))
