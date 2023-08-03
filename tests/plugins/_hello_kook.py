from iamai import Plugin
from iamai.log import logger
from iamai.adapter.kook.message import KookMessage, KookMessageSegment


class HalloKook(Plugin):
    async def handle(self) -> None:
        await self.event.reply(KookMessageSegment.Card(self.event.user_id))

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        # if int(self.event.type) != 9:
        #     return False
        return self.event.message.get_plain_text() == "hello"
