from iamai import Plugin
from iamai.adapter.cqhttp.message import CQHTTPMessageSegment as ms
from iamai.log import logger, error_or_exception


class Echo(Plugin):
    async def handle(self) -> None:
        try:
            await self.event.reply(eval(str(self.event.message.replace("/echo ", ""))))
        except Exception as e:
            await self.event.reply(f"Error: {e}")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type != "message":
            return False
        return self.event.message.startswith("/echo ")
