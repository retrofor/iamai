from iamai import Plugin
from iamai.log import logger


class HalloKook(Plugin):
    async def handle(self) -> None:
        await self.bot.get_adapter("kook").send("hi", "PERSON", 2238357493)
        try:
            await self.event.reply(eval(f"{self.event.content[5:]}"))
        except Exception as e:
            await self.event.reply(f"Error:{e}")

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        if int(self.event.type) != 9:
            return False
        if int(self.event.user_id) != 2238357493:
            return False
        return self.event.content.lower().startswith(".show")
