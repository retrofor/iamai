from plugins.iamai_plugin_base import CommandPluginConfig


class Config(CommandPluginConfig):
    __config_name__ = "plugin_reply"
    data_type: str = "json"
    """数据类型，目前只支持 json。"""
    data_file: str = "data/reply_data.json"
    """数据文件位置。"""
    ignore_case: bool = True
    """是否忽略大小写，默认为 True。"""
