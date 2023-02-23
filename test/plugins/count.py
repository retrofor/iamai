from iamai import Plugin
import onedice

class Count(Plugin):
    async def handle(self) -> None:
        if self.state is None:
            self.state = 0
        self.state += 1
        await self.event.reply(f"count: {self.state}")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type == "message_sent" or self.event.type == "message":
            return self.event.message.get_plain_text() == "count"
        else:
            return False

