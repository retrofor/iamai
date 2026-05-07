from __future__ import annotations

import random
from typing import Any, cast

from asterline import Context, Plugin, command
from asterline_example_utils import (
    LLMSettings,
    chat_json,
    clip_text,
    format_transcript,
    resolve_llm_settings,
)
from pydantic import BaseModel, Field

DEFAULT_NAMES = ["Mira", "Jun", "Tao", "Nova", "Ren", "Sol"]


def make_default_life(*, theme: str = "slice-of-life") -> dict[str, Any]:
    return {
        "name": random.choice(DEFAULT_NAMES),
        "theme": theme,
        "age": 18,
        "stats": {
            "wealth": 5,
            "health": 6,
            "joy": 6,
            "reputation": 4,
        },
        "history": [f"You begin a new {theme} life with equal parts doubt and momentum."],
        "pending_scene": None,
    }


class LifeConfig(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    choices_per_scene: int = 3


class LifePlugin(Plugin):
    name = "life"
    description = "Generates yearly scenes and applies player choices."
    requires = ("life_state",)
    load_after = ("life_state",)
    config_model = LifeConfig

    def _life(self) -> dict[str, Any]:
        return cast(dict[str, Any], self.runtime.get_plugin("life_state").state["life"])

    async def _generate_scene(self, life: dict[str, Any]) -> dict[str, Any]:
        settings = resolve_llm_settings(
            self.config_obj, default_temperature=0.8, default_max_tokens=620
        )
        stats = life.get("stats", {})
        history = life.get("history", [])
        payload = await chat_json(
            settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a life simulator narrator. Generate one vivid but compact yearly event. "
                        "Return structured choices with small stat changes, reply in Chinese."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Name: {life['name']}\n"
                        f"Theme: {life['theme']}\n"
                        f"Age: {life['age']}\n"
                        f"Stats: {stats}\n"
                        f"History:\n{format_transcript([f'- {item}' for item in history], limit=6)}\n\n"
                        "Return JSON with scene and choices. "
                        "Each choice should have label, note, and effect."
                        " effect is an object with wealth, health, joy, reputation integers in [-2, 3]."
                    ),
                },
            ],
        )
        data = payload if isinstance(payload, dict) else {}
        raw_choices = data.get("choices", [])
        normalized: list[dict[str, Any]] = []
        choice_limit = max(2, min(int(self.config.get("choices_per_scene", 3)), 4))
        if isinstance(raw_choices, list):
            for item in raw_choices[:choice_limit]:
                if not isinstance(item, dict):
                    continue
                effect = item.get("effect", {})
                effect_map = {
                    "wealth": (int(effect.get("wealth", 0)) if isinstance(effect, dict) else 0),
                    "health": (int(effect.get("health", 0)) if isinstance(effect, dict) else 0),
                    "joy": int(effect.get("joy", 0)) if isinstance(effect, dict) else 0,
                    "reputation": (
                        int(effect.get("reputation", 0)) if isinstance(effect, dict) else 0
                    ),
                }
                normalized.append(
                    {
                        "label": clip_text(
                            str(item.get("label", "")).strip() or "Keep moving.",
                            limit=100,
                        ),
                        "note": clip_text(
                            str(item.get("note", "")).strip() or "A quiet tradeoff follows.",
                            limit=120,
                        ),
                        "effect": effect_map,
                    }
                )
        if not normalized:
            normalized = [
                {
                    "label": "Take a stable internship.",
                    "note": "Less chaos, more routine.",
                    "effect": {"wealth": 2, "health": 0, "joy": -1, "reputation": 1},
                },
                {
                    "label": "Ship an experimental side project.",
                    "note": "Stress rises, but momentum does too.",
                    "effect": {"wealth": 0, "health": -1, "joy": 2, "reputation": 1},
                },
                {
                    "label": "Disappear for a month of rest.",
                    "note": "Recovery over reputation.",
                    "effect": {"wealth": -1, "health": 2, "joy": 1, "reputation": -1},
                },
            ]
        return {
            "scene": clip_text(
                str(data.get("scene", "")).strip()
                or "A fork in the road appears just as the year starts to accelerate.",
                limit=260,
            ),
            "choices": normalized,
        }

    @command("newlife", priority=10)
    async def newlife(self, ctx: Context, args: str) -> None:
        theme = args.strip() or random.choice(
            ["slice-of-life", "cyberpunk", "indie hacker", "space colony"]
        )
        life = make_default_life(theme=theme)
        life["name"] = random.choice(DEFAULT_NAMES)
        self.runtime.get_plugin("life_state").state["life"] = life
        await ctx.reply(
            f"new life: {life['name']} age={life['age']} theme={life['theme']} "
            "Use /next to generate your first yearly event."
        )

    @command("status", priority=20)
    async def status(self, ctx: Context) -> None:
        life = self._life()
        stats = life.get("stats", {})
        await ctx.reply(
            f"{life['name']} age={life['age']} theme={life['theme']} "
            f"wealth={stats.get('wealth', 0)} health={stats.get('health', 0)} "
            f"joy={stats.get('joy', 0)} reputation={stats.get('reputation', 0)}"
        )

    @command("next", priority=30)
    async def next_scene(self, ctx: Context) -> None:
        life = self._life()
        if life.get("pending_scene") is not None:
            await ctx.reply("A scene is already waiting. Use /choose <index> first.")
            return
        scene = await self._generate_scene(life)
        life["pending_scene"] = scene
        lines = [f"year {life['age'] + 1}: {scene['scene']}"]
        for index, choice in enumerate(scene["choices"], start=1):
            effect = choice["effect"]
            lines.append(
                f"{index}. {choice['label']} "
                f"(wealth={effect['wealth']:+d}, health={effect['health']:+d}, "
                f"joy={effect['joy']:+d}, reputation={effect['reputation']:+d})"
            )
        await ctx.reply("\n".join(lines))

    @command("choose", priority=40)
    async def choose(self, ctx: Context, args: str) -> None:
        token = args.strip()
        if not token.isdigit():
            await ctx.reply("Usage: /choose <index>")
            return
        life = self._life()
        scene = life.get("pending_scene")
        if scene is None:
            await ctx.reply("No pending scene. Use /next first.")
            return
        index = int(token) - 1
        choices = scene.get("choices", [])
        if index < 0 or index >= len(choices):
            await ctx.reply("Choice index out of range.")
            return
        choice = choices[index]
        for key, delta in choice["effect"].items():
            current = int(life["stats"].get(key, 0))
            life["stats"][key] = max(0, current + int(delta))
        life["age"] += 1
        outcome = f"At age {life['age']}, you chose '{choice['label']}'. {choice['note']}"
        life.setdefault("history", []).append(outcome)
        life["pending_scene"] = None
        stats = life["stats"]
        await ctx.reply(
            f"{outcome}\n"
            f"stats => wealth={stats['wealth']} health={stats['health']} "
            f"joy={stats['joy']} reputation={stats['reputation']}"
        )
