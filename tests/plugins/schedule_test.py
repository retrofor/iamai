from time import strftime, localtime

from iamai import Plugin
from iamai.adapter.apscheduler import scheduler_decorator


@scheduler_decorator(
    trigger="interval", trigger_args={"seconds": 10}, override_rule=True
)
class Schedulers(Plugin):
    async def handle(self) -> None:
        await self.bot.get_adapter("console").send(
            f"Time: {strftime('%Y-%m-%d %H:%M:%S', localtime())}"
        )

    async def rule(self) -> bool:
        return False
