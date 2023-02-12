"""IamAI
简单的 Python 异步多后端机器人框架

本模块从子模块导入了以下内容：
- `Bot` => [`IamAI.bot.Bot`](./bot#Bot)
- `Event` => [`IamAI.event.Event`](./event#Event)
- `Plugin` => [`IamAI.plugin.Plugin`](./plugin#Plugin)
- `Adapter` => [`IamAI.adapter.Adapter`](./adapter/#Adapter)
- `ConfigModel` => [`IamAI.config.ConfigModel`](./config#ConfigModel)
"""


name = "IamAI"

from IamAI.bot import Bot
from IamAI.event import Event
from IamAI.plugin import Plugin
from IamAI.adapter import Adapter
from IamAI.config import ConfigModel
