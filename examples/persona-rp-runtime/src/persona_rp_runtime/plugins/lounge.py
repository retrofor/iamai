from __future__ import annotations

from iamai import Context, Plugin, message_handler, middleware
from pydantic import BaseModel


class LoungeConfig(BaseModel):
    memory_limit: int = 18


class LoungePlugin(Plugin):
    name = "lounge"
    description = "Dialogue memory and active persona state."
    state_scope = "persistent"
    config_model = LoungeConfig
    load_before = ("persona",)

    @middleware(phase="before", priority=0)
    async def ensure_lounge(self, ctx: Context) -> None:
        self.state.setdefault("dialogue", [])
        self.state.setdefault("active_persona", "noir-detective")

    @message_handler(priority=200)
    async def capture_dialogue(self, ctx: Context) -> None:
        text = ctx.text.strip()
        if not text or text.startswith("/"):
            return
        dialogue = self.state.setdefault("dialogue", [])
        speaker = ctx.event.user_id or "guest"
        dialogue.append(f"{speaker}: {text}")
        limit = int(self.config.get("memory_limit", 18))
        if len(dialogue) > limit:
            del dialogue[:-limit]
