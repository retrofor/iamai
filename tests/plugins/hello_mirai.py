from iamai import Plugin


class Halloiamai(Plugin):
    async def handle(self) -> None:
        await self.event.reply("Hello, iamai!")

    async def rule(self) -> bool:
        if self.event.adapter.name != "mirai":
            return False
        if self.event.type != "FriendMessage":
            return False
        return self.event.message.get_plain_text().lower() == "hello"
