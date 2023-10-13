"""Bililive 适配器配置。"""
from typing import Any, Dict, List, Union, Literal, Optional

from iamai.config import ConfigModel


class Config(ConfigModel):
    """Bililive 配置类，将在适配器被加载时被混入到机器人主配置中。

    Attributes:
        adapter_type: 适配器类型，需要和协议端配置相同。
        reconnect_interval: 重连等待时间。
        api_timeout: 进行 API 调用时等待返回响应的超时时间。
        show_raw: 是否显示原始数据，默认为 False，不显示。
        session_data_path: session 数据文件路径, 默认为 "data/session.token"。
        report_self_message: 是否上报自己发送的消息，默认为 False，不上报。
        room_id: 监听的房间号列表，默认为 [0]）。
        ssl: 是否使用 SSL，默认为 True，使用。
    """

    __config_name__ = "bililive"
    adapter_type: Literal["ws"] = "ws"
    reconnect_interval: int = 3
    api_timeout: int = 1000
    session_data_path: str = "data/session.token"
    show_raw: bool = False
    report_self_message: bool = False
    room_id: int = 0
    login: bool = True
