from __future__ import annotations

import random
import re
from typing import Any, cast

from iamai import Context, Event, Plugin, Runtime, command, depends, regex
from pydantic import BaseModel


class ArcadeConfig(BaseModel):
    wheel: list[tuple[str, int]] = [
        ("meteor", -6),
        ("treasure", 12),
        ("lucky cat", 8),
    ]


def current_profile(runtime: Runtime, event: Event) -> dict[str, Any]:
    session = runtime.get_plugin("session")
    players = session.state.setdefault("players", {})
    user_id = event.user_id or "guest"
    return cast(
        dict[str, Any],
        players.setdefault(
            user_id,
            {"coins": 20, "spins": 0, "wins": 0, "history": []},
        ),
    )


class ArcadePlugin(Plugin):
    name = "arcade"
    description = "Slot-machine and dice commands."
    requires = ("session",)
    config_model = ArcadeConfig

    @command("spin", priority=10)
    async def spin(self, ctx: Context, profile: dict[str, Any] = depends(current_profile)) -> None:
        wheel = (
            self.config_obj.wheel
            if self.config_obj is not None
            else [("meteor", -6), ("treasure", 12), ("lucky cat", 8)]
        )
        symbol, delta = random.choice(wheel)
        coins = int(profile.get("coins", 0)) + int(delta)
        profile["coins"] = max(coins, 0)
        profile["spins"] = int(profile.get("spins", 0)) + 1
        if delta > 0:
            profile["wins"] = int(profile.get("wins", 0)) + 1
        await ctx.reply(
            f"wheel => {symbol} ({delta:+d}) | coins={profile['coins']} spins={profile['spins']}"
        )

    @command("wallet", priority=20)
    async def wallet(
        self, ctx: Context, profile: dict[str, Any] = depends(current_profile)
    ) -> None:
        await ctx.reply(
            f"coins={profile.get('coins', 0)} wins={profile.get('wins', 0)} "
            f"recent={len(profile.get('history', []))}"
        )

    @command("roll", priority=30)
    async def roll(
        self,
        ctx: Context,
        args: str,
        profile: dict[str, Any] = depends(current_profile),
    ) -> None:
        token = args or "d20"
        match = re.fullmatch(r"(?:(\d+)d)?(\d+)", token.strip())
        if match is None:
            raise ValueError("roll 格式应为 /roll d20 或 /roll 2d6")
        count = int(match.group(1) or 1)
        sides = int(match.group(2))
        if count < 1 or count > 10 or sides < 2 or sides > 100:
            raise ValueError("roll 范围不合法")
        values = [random.randint(1, sides) for _ in range(count)]
        total = sum(values)
        reward = max(total - sides // 2, 0) // max(count, 1)
        profile["coins"] = int(profile.get("coins", 0)) + reward
        await ctx.reply(f"roll {token} => {values} total={total} reward=+{reward}")

    @command("guess", priority=35, rule=regex(r"^/guess (?P<number>\d+)$"))
    async def guess(
        self,
        ctx: Context,
        number: str,
        profile: dict[str, Any] = depends(current_profile),
    ) -> None:
        value = int(number)
        reward = 5 if value == 7 else 1
        profile["coins"] = int(profile.get("coins", 0)) + reward
        await ctx.reply(f"guess={value} reward=+{reward} coins={profile['coins']}")
