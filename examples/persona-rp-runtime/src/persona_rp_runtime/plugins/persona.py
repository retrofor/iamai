from __future__ import annotations

from iamai import Context, Plugin, command, message_handler
from iamai_example_utils import LLMSettings, chat_text, format_transcript, resolve_llm_settings
from pydantic import BaseModel, Field


def default_personas() -> dict[str, str]:
    return {
        "noir-detective": "Dry, observant, low-key dramatic, always notices the city first.",
        "space-captain": "Calm, exploratory, mission-driven, speaks like a veteran commander.",
        "rogue-alchemist": "Curious, mischievous, poetic about experiments and unintended outcomes.",
        "campus-coach": "Supportive, direct, practical, good at reframing anxiety into action.",
    }


class PersonaConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    personas: dict[str, str] = Field(default_factory=default_personas)


class PersonaPlugin(Plugin):
    name = "persona"
    description = "Explicit AI persona roleplay commands and chat handler."
    requires = ("lounge",)
    load_after = ("lounge",)
    config_model = PersonaConfig

    def _personas(self) -> dict[str, str]:
        return dict(self.config.get("personas", {})) or default_personas()

    async def _speak(self, prompt: str) -> str:
        lounge = self.runtime.get_plugin("lounge")
        active = str(lounge.state.get("active_persona", "noir-detective"))
        persona_brief = self._personas().get(active, default_personas()["noir-detective"])
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.9, default_max_tokens=420
        )
        return await chat_text(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an AI roleplay assistant. Stay in the chosen fictional voice, "
                        "but do not pretend to be human or physically present. "
                        f"Current persona: {active}. Style brief: {persona_brief}"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Recent dialogue:\n{format_transcript(lounge.state.get('dialogue', []), limit=10)}\n\n"
                        f"Respond to: {prompt}"
                    ),
                },
            ],
            max_tokens=280,
        )

    @command("personas", priority=10)
    async def personas(self, ctx: Context) -> None:
        lounge = self.runtime.get_plugin("lounge")
        active = lounge.state.get("active_persona", "noir-detective")
        lines = [f"active persona: {active}"]
        for name, brief in self._personas().items():
            lines.append(f"- {name}: {brief}")
        await ctx.reply("\n".join(lines))

    @command("persona", priority=20)
    async def switch_persona(self, ctx: Context, args: str) -> None:
        name = args.strip()
        if not name:
            await ctx.reply("Usage: /persona <name>")
            return
        personas = self._personas()
        if name not in personas:
            await ctx.reply(f"Unknown persona: {name}")
            return
        lounge = self.runtime.get_plugin("lounge")
        lounge.state["active_persona"] = name
        await ctx.reply(f"persona switched to {name}")

    @command("say", priority=30)
    async def say(self, ctx: Context, args: str) -> None:
        prompt = args.strip()
        if not prompt:
            await ctx.reply("Usage: /say <prompt>")
            return
        await ctx.reply(await self._speak(prompt))

    @message_handler(startswith=("ai ", "@ai "), priority=50)
    async def addressed(self, ctx: Context) -> None:
        prompt = ctx.text.split(" ", 1)[1].strip() if " " in ctx.text else ""
        if not prompt:
            return
        await ctx.reply(await self._speak(prompt))
