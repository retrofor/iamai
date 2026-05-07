from __future__ import annotations

from iamai import Context, Plugin, command
from iamai_example_utils import LLMSettings, chat_text, clip_text, resolve_llm_settings
from pydantic import BaseModel, Field

WORKER_PROMPTS = {
    "strategist": "Find leverage, sequence, and obvious constraints.",
    "builder": "Turn the plan into tangible deliverables and examples.",
    "skeptic": "Stress-test assumptions, edge cases, and missing evidence.",
}


class WorkersConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    worker_temperature: float = 0.8


class WorkersPlugin(Plugin):
    name = "workers"
    description = "Role-specialized workers for the supervisor loop."
    requires = ("briefing",)
    load_after = ("briefing",)
    config_model = WorkersConfig

    async def run_worker(
        self,
        *,
        role: str,
        goal: str,
        task: str,
        shared_context: str,
    ) -> str:
        if role not in WORKER_PROMPTS:
            raise ValueError(f"unsupported worker role: {role}")
        settings = resolve_llm_settings(
            self.config_obj,
            default_temperature=float(self.config.get("worker_temperature", 0.8)),
            default_max_tokens=520,
        )
        return await chat_text(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        f"You are the {role} worker in a small agent team. "
                        f"{WORKER_PROMPTS[role]} Keep your output practical."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Goal: {goal}\n"
                        f"Assignment: {task}\n"
                        f"Shared context: {shared_context}\n\n"
                        "Respond with a concise worker memo."
                    ),
                },
            ],
            max_tokens=420,
        )

    @command("roles", priority=10)
    async def roles(self, ctx: Context) -> None:
        lines = ["worker roles:"]
        for name, description in WORKER_PROMPTS.items():
            lines.append(f"- {name}: {clip_text(description, limit=100)}")
        await ctx.reply("\n".join(lines))
