from __future__ import annotations

from iamai import Context, Event, Plugin, command, message_handler, middleware
from pydantic import BaseModel


class RoomConfig(BaseModel):
    memory_limit: int = 24


class RoomPlugin(Plugin):
    name = "room"
    description = "Stores recent room messages for assistant features."
    state_scope = "persistent"
    config_model = RoomConfig
    load_before = ("assistant",)

    def _room_key(self, event: Event) -> str:
        return str(event.channel_id or event.guild_id or event.user_id or "global")

    @middleware(phase="before", priority=0)
    async def ensure_rooms(self, ctx: Context) -> None:
        self.state.setdefault("rooms", {})

    @message_handler(priority=200)
    async def capture_message(self, ctx: Context) -> None:
        text = ctx.text.strip()
        if not text or text.startswith("/"):
            return
        key = self._room_key(ctx.event)
        rooms = self.state.setdefault("rooms", {})
        entries = rooms.setdefault(key, [])
        speaker = ctx.event.user_id or "guest"
        entries.append(f"{speaker}: {text}")
        limit = int(self.config.get("memory_limit", 24))
        if len(entries) > limit:
            del entries[:-limit]

    @command("recent", priority=80)
    async def recent(self, ctx: Context) -> None:
        key = self._room_key(ctx.event)
        entries = self.state.setdefault("rooms", {}).get(key, [])
        if not entries:
            await ctx.reply("No room memory yet.")
            return
        lines = ["recent messages:"]
        for item in entries[-10:]:
            lines.append(f"- {item}")
        await ctx.reply("\n".join(lines))
