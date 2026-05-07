from __future__ import annotations

from iamai import Context, Plugin, command


class ChaosPlugin(Plugin):
    name = "chaos"
    description = "Intentional failure demo for error middleware."
    requires = ("session",)
    load_after = ("arcade",)

    @command("boom", priority=10)
    async def boom(self, ctx: Context) -> None:
        raise RuntimeError("slot machine exploded in a shower of coins")
