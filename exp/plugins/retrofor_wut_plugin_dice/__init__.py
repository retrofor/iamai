import re
import random

from iamai.log import logger

from plugins.iamai_plugin_base import CommandPluginBase

from .config import Config


class Dice(CommandPluginBase[None, Config]):
    Config = Config

    def __post_init__(self):
        self.re_pattern = re.compile(
            r"\s*(?P<dice_times>\d+)d(?P<dice_faces>\d+)([*x](?P<dice_multiply>\d+))?",
            flags=re.I,
        )

    async def handle(self) -> None:
        dice_times = int(self.msg_match.group("dice_times"))
        dice_faces = int(self.msg_match.group("dice_faces"))
        if self.msg_match.group("dice_multiply") is None:
            dice_multiply = None
        else:
            dice_multiply = int(self.msg_match.group("dice_multiply"))

        if dice_times > self.config.max_dice_times:
            await self.event.reply(
                self.format_str(self.config.exceed_max_dice_times_str)
            )
            return

        dice = [random.randint(1, dice_faces) for _ in range(dice_times)]
        dice_sum = sum(dice)
        if dice_multiply is None:
            result_str = f"{dice_times}D{dice_faces}="
            if dice_times != 1:
                result_str += f"{'+'.join(map(lambda x: str(x), dice))}="
            result_str += str(dice_sum)
        else:
            result_str = f"{dice_times}D{dice_faces}X{dice_multiply}="
            if dice_times != 1:
                result_str += (
                    f"({'+'.join(map(lambda x: str(x), dice))})X{dice_multiply}="
                )
            result_str += f"{dice_sum}X{dice_multiply}={dice_sum * dice_multiply}"

        logger.info(f"Dice Plugin: {result_str}")
        await self.event.reply(self.format_str(self.config.message_str, result_str))
