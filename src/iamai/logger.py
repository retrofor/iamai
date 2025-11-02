"""
日志系统模块
"""

import logging
import sys
from typing import Optional
from pathlib import Path


# 默认日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 全局日志配置
_loggers = {}
_log_level = logging.INFO
_log_format = DEFAULT_LOG_FORMAT


def get_logger(name: str = "iamai") -> logging.Logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    # 如果没有处理器，添加默认处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_log_format, DEFAULT_DATE_FORMAT))
        logger.addHandler(handler)

    logger.setLevel(_log_level)
    _loggers[name] = logger

    return logger


def setup_logger(config: Optional[dict] = None) -> None:
    """
    设置日志系统

    Args:
        config: 日志配置字典
    """
    global _log_level, _log_format

    if config is None:
        config = {}

    # 设置日志级别
    level_str = config.get("level", "INFO")
    _log_level = getattr(logging, level_str.upper(), logging.INFO)

    # 设置日志格式
    _log_format = config.get("format", DEFAULT_LOG_FORMAT)

    # 更新所有已存在的logger
    for logger in _loggers.values():
        logger.setLevel(_log_level)
        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(_log_format, DEFAULT_DATE_FORMAT))

    # 设置根logger
    logging.basicConfig(
        level=_log_level, format=_log_format, datefmt=DEFAULT_DATE_FORMAT
    )


# 创建默认logger
logger = get_logger()
