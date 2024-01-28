from iamai import Plugin


class Reload(Plugin):
    async def handle(self) -> None:
        self.bot.reload_plugins()
        await self.event.reply("\n".join(map(repr, self.bot.plugins)))

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message_sent":
            return False
        return self.event.message.get_plain_text() == "reload"
