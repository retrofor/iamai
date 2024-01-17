"""中间件"""
from ast import literal_eval
import os
from os.path import dirname, join, abspath
from iamai import ConfigModel, Plugin
from iamai.log import logger
from .config import Directory
from .models.utils import *
import joblib

BASE_DIR = Directory(_path=dirname(abspath("__file__")))
HYDRO_DIR = dirname(abspath(__file__))


def _init_directory(_prefix: str = ''):
    """初始化水系目录"""
    for _ in BASE_DIR.get_dice_dir_list(_prefix):
        if not os.path.exists(_):
            os.makedirs(_)


def _load_models():
    models = {}
    models['hola'] = joblib.load(
        join(HYDRO_DIR, 'models', 'hola.pkl'))
    return models


def load_model(model):
    logger.info("loading models...")
    return _load_models()[model]


def init_directory(_prefix: str = 'HydroRoll'):
    _init_directory(_prefix=_prefix)


class HydroRoll(Plugin):
    """中间件"""
    class Config(ConfigModel):
        __config_name__ = "HydroRoll"

    priority = 0

    # TODO: HydroRollCore should be able to handle all signals and tokens from Psi.
    logger.info("Loading HydroRollCore...")

    async def handle(self) -> None:
        """
        @TODO: HydroRollCore should be able to handle all signals and tokens from Psi.
        @BODY: HydroRollCore actives the rule-packages.
        """

        if self.event.message.get_plain_text() == ".core":
            await self.event.reply("HydroRollCore is running.")
        elif self.event.message.startswith(".test"):
            try:
                result = literal_eval(self.event.message.get_plain_text()[5:])
                await self.event.reply(result)
            except Exception as error:
                await self.event.reply(f"{error!r}")

    async def rule(self) -> bool:
        """
        @TODO: Psi should be able to handle all message first.
        @BODY: lexer module will return a list of tokens, parser module will parse the tokens into a tree, and executor module will execute the tokens with a stack with a bool return value.
        """
        logger.info("loading psi...")
        if not self.bot.global_state.get('HydroRoll.dir'):
            hola = load_model('hola')

            init_directory()
            self.bot.global_state['HydroRoll.dir'] = True
        return self.event.adapter.name in ['cqhttp', 'kook', 'console', 'mirai']
