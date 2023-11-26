from iamai import Plugin


class Hallo(Plugin):
    async def handle(self) -> None:
        await self.event.reply("Hello!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "gensokyo":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message).lower() == "shiki"
