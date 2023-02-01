from typing import Set

from plugins.iamai_plugin_base import CommandPluginConfig


class Config(CommandPluginConfig):
    __config_name__ = "plugin_luck"
    command: Set[str] = {"luck"}
    """命令文本。"""
    min_int: int = 0
    """最小随机整数。"""
    max_int: int = 100
    """最大随机整数。"""
    message_str: str = "{user_name}今天的运气是: {message}"
    """最终发送消息的格式。"""
