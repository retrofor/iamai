"""Console 适配器配置。"""
from typing import Any, Dict

from iamai.config import ConfigModel


class Config(ConfigModel):
    """Console 配置类，将在适配器被加载时被混入到机器人主配置中。"""

    __config_name__ = "console"
    show_raw: bool = False
