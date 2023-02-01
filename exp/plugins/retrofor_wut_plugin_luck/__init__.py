import re
import time
import random

from plugins.iamai_plugin_base import CommandPluginBase

from .config import Config


class Luck(CommandPluginBase[None, Config]):
    Config = Config

    def __post_init__(self):
        self.re_pattern = re.compile(r".*", flags=re.I)

    async def handle(self) -> None:
        random.seed(
            time.strftime("%Y%j", time.localtime()) + self.format_str("{user_id}")
        )
        lucy = random.randint(self.config.min_int, self.config.max_int)
        await self.event.reply(self.format_str(self.config.message_str, str(lucy)))
