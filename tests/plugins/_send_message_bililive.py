import time

from iamai import Plugin
from iamai.log import logger
from iamai.adapter.apscheduler import scheduler_decorator


@scheduler_decorator(
    trigger="interval", trigger_args={"seconds": 5}, override_rule=True
)
class Send(Plugin):
    async def handle(self) -> None:
        if self.state is None:
            self.state = 0
        await self.bot.get_adapter("bililive").send(str(self.state))
        self.state += 1

    async def rule(self) -> bool:
        return False
