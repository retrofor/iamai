from iamai import Plugin
from iamai.adapter.kook.message import KookMessage, KookMessageSegment
from iamai.log import logger


class EvalKook(Plugin):
    async def handle(self) -> None:
        try:
            await self.event.reply(
                KookMessageSegment.at(user_id=self.event.author_id)
            )  # eval(self.event.content[6:]))
        except Exception as e:
            await self.event.reply(f"Error:\n{e}")

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        if int(self.event.type) != 9:
            return False
        return self.event.message.startswith(".show")
