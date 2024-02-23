"""red 协议配置。"""

import os
from ast import List
from os.path import join
from pathlib import Path
from typing import Optional

from iamai.config import ConfigModel

HOME = Path(os.path.expanduser("~"))
USER_CONFIG = join(HOME, ".chronocat", "config", "chronocat.yml")


class Config(ConfigModel):
    """red 配置类，将在适配器被加载时被混入到机器人主配置中。

    Attributes:
        adapter_type:USER_CONFIG 适配器类型，需要和协议端配置相同。
        auto_fill: 是否根据配置自动读取设置，默认开启。
        reconnect_interval: 重连等待时间。
        api_timeout: 进行 API 调用时等待返回响应的超时时间。
        access_token: 鉴权。
        show_raw: 是否显示原始数据，默认为 False，不显示。
        report_self_message: 是否上报自身消息, 默认不上报
    """

    __config_name__ = "red"
    multi_account: bool = False
    account_list: list = []
    auto_fill: bool = True
    reconnect_interval: int = 3
    api_timeout: int = 1000
    host: str = "localhost"
    port: int = 16531
    access_token: str = ""
    show_raw: bool = False
    report_self_message: bool = False
