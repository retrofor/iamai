from iamai import Plugin
from iamai.log import logger


class HalloKook(Plugin):
    async def handle(self) -> None:
        await self.event.reply("Hallo Kook!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        if int(self.event.type) != 9:
            return False
        return self.event.content.lower() == "hello"
