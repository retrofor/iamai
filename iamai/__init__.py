"""iamai
简单的 Python 异步多后端机器人框架

本模块从子模块导入了以下内容：
- `Bot` => [`iamai.bot.Bot`](./bot#Bot)
- `Event` => [`iamai.event.Event`](./event#Event)
- `Plugin` => [`iamai.plugin.Plugin`](./plugin#Plugin)
- `Adapter` => [`iamai.adapter.Adapter`](./adapter/#Adapter)
- `ConfigModel` => [`iamai.config.ConfigModel`](./config#ConfigModel)
"""
from iamai.bot import Bot
from iamai.event import Event
from iamai.plugin import Plugin
from iamai.adapter import Adapter
from iamai.config import ConfigModel
