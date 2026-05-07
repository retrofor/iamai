"""Built-in adapter implementations."""

from .onebot11 import OneBot11Adapter
from .telegram import TelegramAdapter
from .terminal import TerminalAdapter
from .webhook import WebhookAdapter

__all__ = ["OneBot11Adapter", "TelegramAdapter", "TerminalAdapter", "WebhookAdapter"]
