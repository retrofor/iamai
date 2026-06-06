from __future__ import annotations

from typing import Any

from iamai import (
    Context,
    Plugin,
    Runtime,
    any_rules,
    command,
    contains,
    depends,
    message_handler,
    startswith,
    superusers,
)
from iamai_example_utils import (
    LLMSettings,
    chat_text,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field


def story_state(runtime: Runtime) -> dict[str, Any]:
    memory = runtime.get_plugin("memory")
    return memory.state.setdefault(
        "story",
        {"setting": "未知世界", "cast": [], "scenes": []},
    )


def _build_context(story: dict[str, Any], max_scenes: int = 6) -> str:
    """Build a compact story context string for the LLM prompt."""
    parts: list[str] = []
    setting = story.get("setting", "未知世界")
    parts.append(f"世界观: {setting}")
    cast = story.get("cast", [])
    if cast:
        cast_lines = [f"  - {item['name']} ({item['role']})" for item in cast[:8]]
        parts.append(f"角色:\n" + "\n".join(cast_lines))
    scenes = story.get("scenes", [])
    if scenes:
        recent = scenes[-max_scenes:]
        parts.append(f"已发生的剧情 (最近 {len(recent)} 幕):\n" + "\n".join(f"  {s}" for s in recent))
    return "\n\n".join(parts)


def _narrator_voice(config_obj: Any) -> str:
    """Build the narrator persona description."""
    narrator = getattr(config_obj, "narrator", "旁白") if config_obj is not None else "旁白"
    style = getattr(config_obj, "style", "") if config_obj is not None else ""
    base = (
        f"你是一个名为「{narrator}」的故事旁白。"
        "用生动、富有画面感的语言叙述故事进展。"
        "每次回复控制在 3-6 句话，保持紧凑有张力。"
        "直接输出叙述内容，不要加前缀和引号。"
    )
    if style:
        base += f" 风格要求: {style}"
    return base


class DirectorConfig(BaseModel):
    narrator: str = "旁白"
    style: str = ""
    llm: LLMSettings = Field(default_factory=LLMSettings)


class DirectorPlugin(Plugin):
    name = "director"
    description = "LLM-powered scene generation, twists, and story continuation."
    requires = ("memory",)
    optional_requires = ("cast", "world")
    config_model = DirectorConfig

    # ----------------------------------------------------------------
    # helpers
    # ----------------------------------------------------------------

    async def _generate(self, instruction: str, context: str) -> str:
        """Call the LLM with the story context and a specific instruction."""
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.8, default_max_tokens=500
        )
        messages = [
            {"role": "system", "content": _narrator_voice(self.config_obj)},
            {
                "role": "user",
                "content": (
                    f"当前故事状态:\n{context}\n\n"
                    f"请完成以下任务:\n{instruction}"
                ),
            },
        ]
        result = await chat_text(settings, messages, temperature=0.85)
        return clip_text(result, limit=400)

    async def _append_scene(self, story: dict[str, Any], line: str) -> None:
        story.setdefault("scenes", []).append(line)

    # ----------------------------------------------------------------
    # commands
    # ----------------------------------------------------------------

    @command("scene", priority=10)
    async def scene(
        self, ctx: Context, args: str, story: dict[str, Any] = depends(story_state)
    ) -> None:
        prompt = args.strip() or "一个意想不到的转折"
        context = _build_context(story)
        narrator = self.config_obj.narrator if self.config_obj is not None else "旁白"
        line = await self._generate(
            instruction=f"用户输入了事件提示「{prompt}」，请围绕这个提示展开一个生动的场景叙述。",
            context=context,
        )
        label = f"[{narrator}] {line}"
        await self._append_scene(story, label)
        await ctx.reply(label)

    @command("twist", priority=20)
    async def twist(
        self, ctx: Context, story: dict[str, Any] = depends(story_state)
    ) -> None:
        context = _build_context(story)
        line = await self._generate(
            instruction=(
                "故事需要一个出乎意料的剧情转折！"
                "请生成一个令人惊讶但又合理的反转，颠覆读者对当前局势的认知。"
            ),
            context=context,
        )
        label = f"[转折] {line}"
        await self._append_scene(story, label)
        await ctx.reply(label)

    @message_handler(
        priority=30,
        rule=any_rules(startswith("继续"), startswith("continue"), contains("下一幕")),
    )
    async def continue_story(
        self, ctx: Context, story: dict[str, Any] = depends(story_state)
    ) -> None:
        context = _build_context(story)
        line = await self._generate(
            instruction="请自然地推进故事，基于已有剧情写出下一幕的叙述。",
            context=context,
        )
        label = f"[推进] {line}"
        await self._append_scene(story, label)
        await ctx.reply(label)

    @command("recap", priority=40)
    async def recap(
        self, ctx: Context, story: dict[str, Any] = depends(story_state)
    ) -> None:
        scenes = story.get("scenes", [])
        if not scenes:
            await ctx.reply("故事还没开始。")
            return
        tail = scenes[-3:]
        await ctx.reply("recap:\n" + "\n".join(tail))

    @command("panic", priority=50, permission=superusers())
    async def panic(
        self, ctx: Context, story: dict[str, Any] = depends(story_state)
    ) -> None:
        context = _build_context(story)
        ending = await self._generate(
            instruction=(
                "故事即将结束。请写一个收尾，呼应开篇的设定、角色的命运。"
                "要有余韵，让读者感到这个故事即使结束了也还在心里继续。"
                "2-4 句话即可。"
            ),
            context=context,
        )
        label = f"[终幕] {ending}"
        await self._append_scene(story, label)
        await ctx.reply(label)
        raise RuntimeError("— 故事终 —")
