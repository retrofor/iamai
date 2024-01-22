"""API Documentation

Comprehensive AI Toolkit for Multimodal Learning and Cross-Platform Robotics.

This Module imports the following contents from the sub-module:
- `Bot` => [`iamai.bot.Bot`](bot#class-bot-bot)
- `Event` => [`iamai.event.Event`](event#Event)
- `MessageEvent` => [`iamai.event.MessageEvent`](./event#MessageEvent)
- `Plugin` => [`iamai.plugin.Plugin`](./plugin#Plugin)
- `Adapter` => [`iamai.adapter.Adapter`](./adapter/#Adapter)
- `ConfigModel` => [`iamai.config.ConfigModel`](./config#ConfigModel)
- `Depends` => [`iamai.dependencies.Depends`](./dependencies#Depends)
"""
from iamai.adapter import Adapter
from iamai.bot import Bot
from iamai.config import ConfigModel
from iamai.dependencies import Depends
from iamai.event import Event, MessageEvent
from iamai.plugin import Plugin
from iamai.const import __version__

__all__ = [
    "Adapter",
    "Bot",
    "ConfigModel",
    "Depends",
    "Event",
    "MessageEvent",
    "Plugin",
    "__version__",
]
