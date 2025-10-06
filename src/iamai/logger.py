"""
日志系统模块
使用loguru提供统一的日志功能
"""
from loguru import logger
import sys
import socket
import threading
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

_socket_server_thread = None
_socket_clients = []

def _socket_sink_server(host='127.0.0.1', port=56789):
    """启动 socket server，接收日志 sink 客户端连接并广播日志"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    while True:
        client, _ = server.accept()
        _socket_clients.append(client)

def _socket_sink(message):
    """loguru sink: 将日志通过 socket 广播给所有客户端"""
    for client in list(_socket_clients):
        try:
            client.sendall((message + '\n').encode('utf-8'))
        except Exception:
            try:
                _socket_clients.remove(client)
            except Exception:
                pass

def setup_logger(
    level: LogLevel = "INFO",
    log_file: Optional[str] = "iamai.log",
    console: bool = False,
    format_string: Optional[str] = None,
    socket_sink: bool = True,
    socket_host: str = '127.0.0.1',
    socket_port: int = 56789
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
    # Socket sink
    if socket_sink:
        global _socket_server_thread
        if _socket_server_thread is None:
            _socket_server_thread = threading.Thread(target=_socket_sink_server, args=(socket_host, socket_port), daemon=True)
            _socket_server_thread.start()
        logger.add(_socket_sink, level=level, format="{message}")

    # 添加一个内部 sink，用于把日志广播到已注册的 UI 面板
    logger.add(_broadcast_to_ui, level=level, format=format_string)

def get_logger(name: str):
    """获取logger实例"""
    return logger.bind(name=name)

# 默认只写文件
setup_logger()

