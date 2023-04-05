from iamai import Plugin


class Halloiamai(Plugin):
    async def handle(self) -> None:
        await self.event.reply("Hello, iamai!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return str(self.event.message).lower() == "hello"
