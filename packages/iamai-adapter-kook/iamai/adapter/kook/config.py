"""Kook 适配器配置。"""
from typing import Literal

from iamai.config import ConfigModel


class Config(ConfigModel):
    """Kook 配置类，将在适配器被加载时被混入到机器人主配置中。

    Attributes:
        adapter_type: 适配器类型，需要和协议端配置相同。
        reconnect_interval: 重连等待时间。
        api_timeout: 进行 API 调用时等待返回响应的超时时间。
        access_token: 鉴权。
        compress: 是否启用压缩，默认为 0，不启用。
        show_raw: 是否显示原始数据，默认为 False，不显示。
    """

    __config_name__ = "kook"
    adapter_type: Literal["ws", "wb"] = "ws"
    reconnect_interval: int = 3
    api_timeout: int = 1000
    access_token: str = ""
    compress: Literal[0, 1] = 0
    show_raw: bool = False
    report_self_message: bool = False
