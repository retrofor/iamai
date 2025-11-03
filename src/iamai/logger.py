"""
日志系统模块

This module provides a logging system based on Loguru.
It offers a simple and powerful logging interface with:
- Color-coded output
- Automatic exception tracing
- Flexible configuration
- Context binding
"""

import sys
from typing import Optional
from pathlib import Path
from loguru import logger as _logger


# 默认日志格式
DEFAULT_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[name]}</cyan> - "
    "<level>{message}</level>"
)

# 全局配置标志
_configured = False


def get_logger(name: str = "iamai"):
    """
    Get a logger instance with the specified name.

    This function returns a loguru logger with context binding.
    The name is used to identify the source of log messages.

    Args:
        name: Logger name, typically the module name (__name__)

    Returns:
        A loguru logger instance with name context

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello from my module")
    """
    return _logger.bind(name=name)


def setup_logger(config: Optional[dict] = None) -> None:
    """
    Setup the logging system with custom configuration.

    This function configures loguru with the specified settings.
    It should be called once at application startup.

    Args:
        config: Configuration dictionary with the following keys:
            - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            - format: Custom log format string
            - file: Optional file path to write logs to
            - rotation: Log file rotation policy (e.g., "500 MB", "1 week")
            - retention: How long to keep old log files (e.g., "1 month")
            - compression: Compression format for rotated logs (e.g., "zip")

    Example:
        >>> setup_logger({
        ...     "level": "DEBUG",
        ...     "file": "logs/app.log",
        ...     "rotation": "500 MB"
        ... })
    """
    global _configured

    if config is None:
        config = {}

    # 移除默认的处理器
    _logger.remove()

    # 获取日志级别
    level = config.get("level", "INFO").upper()

    # 获取日志格式
    log_format = config.get("format", DEFAULT_LOG_FORMAT)
    
    # 配置默认的 extra 字段
    _logger.configure(extra={"name": "iamai"})

    # 添加控制台处理器
    _logger.add(
        sys.stdout,
        format=log_format,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # 如果配置了文件输出
    if "file" in config:
        file_path = Path(config["file"])
        file_path.parent.mkdir(parents=True, exist_ok=True)

        _logger.add(
            str(file_path),
            format=log_format,
            level=level,
            rotation=config.get("rotation", "500 MB"),
            retention=config.get("retention", "1 month"),
            compression=config.get("compression", "zip"),
            backtrace=True,
            diagnose=True,
        )

    _configured = True


# 初始化默认配置
if not _configured:
    setup_logger()

# 创建默认 logger
logger = get_logger()
