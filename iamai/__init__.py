"""iamai

简单的 Python 异步多后端机器人框架

本模块从子模块导入了以下内容：
- `Bot` => [`iamai.bot.Bot`](./bot#Bot)
- `Event` => [`iamai.event.Event`](./event#Event)
- `MessageEvent` => [`iamai.event.MessageEvent`](./event#MessageEvent)
- `Plugin` => [`iamai.plugin.Plugin`](./plugin#Plugin)
- `Adapter` => [`iamai.adapter.Adapter`](./adapter/#Adapter)
- `ConfigModel` => [`iamai.config.ConfigModel`](./config#ConfigModel)
- `Depends` => [`iamai.dependencies.Depends`](./dependencies#Depends)
- `Cli` => [`iamai.cli.Cli`](./cli#Cli)
"""
from iamai.adapter import Adapter
from iamai.bot import Bot
from iamai.cli import Cli
from iamai.config import ConfigModel
from iamai.dependencies import Depends
from iamai.event import Event, MessageEvent
from iamai.plugin import Plugin

__all__ = [
    "Adapter",
    "Bot",
    "ConfigModel",
    "Depends",
    "Event",
    "MessageEvent",
    "Plugin",
    "Cli",
]

__version__ = "3.3.3"
