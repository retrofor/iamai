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

# UI sinks: functions that accept (level: str, message: str)
_ui_sinks = []

def register_ui_sink(fn):
    """注册一个 UI 日志接收函数。fn(level: str, message: str)"""
    if fn not in _ui_sinks:
        _ui_sinks.append(fn)

def unregister_ui_sink(fn):
    """注销 UI 日志接收函数"""
    try:
        _ui_sinks.remove(fn)
    except ValueError:
        pass

def _broadcast_to_ui(record):
    """将 loguru 的 record 广播给所有注册的 UI sink"""
    try:
        rec = record.record
        # 如果这是来自 UI 的记录（例如 UI 侧调用 add_log 写入），则不再广播到 UI，避免循环
        extra = rec.get('extra', {}) or {}
        if extra.get('from_ui'):
            return
        level = rec.get("level").name if rec.get("level") else "INFO"
        time = rec.get("time").strftime("%H:%M:%S") if rec.get("time") else ""
        message = rec.get("message", "")
        text = f"[{time}] {level}: {message}"
        for fn in list(_ui_sinks):
            try:
                fn(level, text)
            except Exception:
                # 忽略 UI 推送错误
                pass
    except Exception:
        pass

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

    # 添加一个内部 sink，用于把日志广播到已注册的 UI 面板
    logger.add(_broadcast_to_ui, level=level, format=format_string)

def get_logger(name: str):
    """获取logger实例"""
    return logger.bind(name=name)

# 默认只写文件
setup_logger()

