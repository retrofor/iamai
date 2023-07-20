import inspect
import logging
from os import listdir
from os.path import join, isfile
from importlib.machinery import SourceFileLoader

from utils.plugin import BotPlugin
from utils.file_loader import make_folder

PLUGINS_DIR = "plugins"
make_folder(PLUGINS_DIR)


def load_plugins():
    plugins = [
        f
        for f in listdir(PLUGINS_DIR)
        if isfile(join(PLUGINS_DIR, f)) and f.endswith(".py")
    ]
    bot_plugins = []
    for plugin in plugins:
        try:
            module = SourceFileLoader(
                plugin[:-3], f"{PLUGINS_DIR}/{plugin}"
            ).load_module()
            for name, cs in inspect.getmembers(module, inspect.isclass):
                if cs.__base__ == BotPlugin:
                    logging.info(f"正在加載插件 {plugin} ({name})")
                    bot_plugins.append(cs())
                    break
        except Exception as e:
            logging.error(f"加載插件 {plugin} 時出現錯誤: {e}")

    return bot_plugins
