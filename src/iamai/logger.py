"""
日志系统模块
使用loguru提供统一的日志功能
"""
from loguru import logger
import sys
from typing import Optional
from .typing import LogLevel

# 移除默认的logger
logger.remove()

def setup_logger(
    level: LogLevel = "INFO",
    log_file: Optional[str] = "iamai.log",
    console: bool = False,
    format_string: Optional[str] = None
) -> None:
    """设置日志器"""
    if format_string is None:
        format_string = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    # 控制台输出
    if console:
        logger.add(
            sys.stderr,
            format=format_string,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    # 文件输出
    if log_file:
        logger.add(
            log_file,
            format=format_string,
            level=level,
            rotation="1 day",
            retention="30 days",
            compression="zip",
            backtrace=True,
            diagnose=True
        )

def get_logger(name: str):
    """获取logger实例"""
    return logger.bind(name=name)

# 默认只写文件
setup_logger()

