from time import strftime, localtime

from iamai import Plugin
from iamai.adapter.apscheduler import scheduler_decorator
import random


@scheduler_decorator(
    trigger="interval",
    trigger_args={"seconds": random.randint(10, 20)},
    override_rule=True,
)
class Schedule(Plugin):
    async def handle(self) -> None:
        await self.bot.get_adapter("cqhttp").send(
            f"Time: {strftime('%Y-%m-%d %H:%M:%S', localtime())}",
            message_type="group",
            id_=126211793,  # Group ID
        )

    async def rule(self) -> bool:
        return (
            self.event.type == "apscheduler" and type(self) is self.event.plugin_class
        )
