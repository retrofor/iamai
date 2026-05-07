from __future__ import annotations

from iamai import Context, Event, Plugin, command, message_handler
from iamai_example_utils import LLMSettings, chat_text, format_transcript, resolve_llm_settings
from pydantic import BaseModel, Field


class AssistantConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    summary_window: int = 12


class AssistantPlugin(Plugin):
    name = "assistant"
    description = "Summarizes room context and answers explicit assistant requests."
    requires = ("room",)
    load_after = ("room",)
    config_model = AssistantConfig

    def _room_key(self, event: Event) -> str:
        return str(event.channel_id or event.guild_id or event.user_id or "global")

    def _recent_entries(self, event: Event) -> list[str]:
        room = self.runtime.get_plugin("room")
        entries = room.state.setdefault("rooms", {}).get(self._room_key(event), [])
        window = int(self.config.get("summary_window", 12))
        return list(entries[-window:])

    async def _answer(self, prompt: str, entries: list[str], *, mode: str) -> str:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.6, default_max_tokens=520
        )
        return await chat_text(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an explicitly AI group assistant. Use the recent room transcript as context. "
                        f"Current mode: {mode}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Recent messages:\n{format_transcript(entries, limit=12)}\n\n"
                        f"Task: {prompt}"
                    ),
                },
            ],
            max_tokens=420,
        )

    @command("digest", priority=10)
    async def digest(self, ctx: Context) -> None:
        entries = self._recent_entries(ctx.event)
        if not entries:
            await ctx.reply("Not enough room context yet.")
            return
        answer = await self._answer(
            "Write a compact digest with the main topic, decisions, and open questions.",
            entries,
            mode="digest",
        )
        await ctx.reply(answer)

    @command("todo", priority=20)
    async def todo(self, ctx: Context) -> None:
        entries = self._recent_entries(ctx.event)
        if not entries:
            await ctx.reply("Not enough room context yet.")
            return
        answer = await self._answer(
            "Extract action items only. If none exist, say so plainly.",
            entries,
            mode="todo",
        )
        await ctx.reply(answer)

    @command("mood", priority=30)
    async def mood(self, ctx: Context) -> None:
        entries = self._recent_entries(ctx.event)
        if not entries:
            await ctx.reply("Not enough room context yet.")
            return
        answer = await self._answer(
            "Describe the room mood in 2-3 sentences and mention any tension or momentum.",
            entries,
            mode="mood",
        )
        await ctx.reply(answer)

    @command("reply", priority=40)
    async def reply_with_context(self, ctx: Context, args: str) -> None:
        question = args.strip()
        if not question:
            await ctx.reply("Usage: /reply <question>")
            return
        entries = self._recent_entries(ctx.event)
        answer = await self._answer(question, entries, mode="reply")
        await ctx.reply(answer)

    @command("ask-next", priority=45)
    async def ask_next(self, ctx: Context, args: str) -> None:
        prompt = args.strip() or "请发送下一条补充信息，我会结合它回复。"
        await ctx.reply(prompt)
        next_ctx = await ctx.wait_for_message(timeout=60.0)
        entries = [*self._recent_entries(ctx.event), f"next: {next_ctx.text}"]
        answer = await self._answer(
            f"Use the user's next message to answer helpfully: {next_ctx.text}",
            entries,
            mode="multi-turn",
        )
        await ctx.reply(answer)

    @message_handler(startswith=("ai ", "runtime "), priority=50)
    async def addressed(self, ctx: Context) -> None:
        question = ctx.text.split(" ", 1)[1].strip() if " " in ctx.text else ""
        if not question:
            return
        entries = self._recent_entries(ctx.event)
        answer = await self._answer(question, entries, mode="addressed-chat")
        await ctx.reply(answer)
