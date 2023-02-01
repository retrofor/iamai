from typing import Set, Optional

from iamai import ConfigModel


class BasePluginConfig(ConfigModel):
    __config_name__ = ""
    handle_all_message: bool = False
    """是否处理所有类型的消息，此配置为 True 时会覆盖 handle_friend_message 和 handle_group_message。"""
    handle_friend_message: bool = True
    """是否处理好友消息。"""
    handle_group_message: bool = True
    """是否处理群消息。"""
    accept_group: Optional[Set[int]] = None
    """处理消息的群号，仅当 handle_group_message 为 True 时生效，留空表示处理所有群。"""
    message_str: str = "{user_name}: {message}"
    """最终发送消息的格式。"""


class RegexPluginConfig(BasePluginConfig):
    pass


class CommandPluginConfig(RegexPluginConfig):
    command_prefix: Set[str] = {".", "。"}
    """命令前缀。"""
    command: Set[str] = {}
    """命令文本。"""
    ignore_case: bool = True
    """忽略大小写。"""
