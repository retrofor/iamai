from typing import Set, Optional

from plugins.iamai_plugin_base import CommandPluginConfig


class Config(CommandPluginConfig):
    __config_name__ = "plugin_send"
    command: Set[str] = {"send"}
    """命令文本。"""
    send_user_id: int = 0
    """发送消息的对象的 QQ 号码。"""
    send_success_msg: Optional[str] = None
    """发送成功时回复的消息，设置为 None 表示不发送任何消息。"""
    send_filed_msg: Optional[str] = "发送失败：{message}"
    """发送失败时回复的消息。"""
