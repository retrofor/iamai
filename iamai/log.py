"""iamai 日志。

iamai 使用 [loguru](https://github.com/Delgan/loguru) 来记录日志信息。
自定义 logger 请参考 [loguru](https://github.com/Delgan/loguru) 文档。
"""
import os
import sys
from datetime import datetime

from loguru import logger as _logger

logger = _logger

current_path = os.path.dirname(os.path.abspath("__file__"))
log_path = os.path.join(
    current_path, "logs", datetime.now().strftime("%Y-%m-%d") + ".log"
)


def error_or_exception(message: str, exception: Exception, verbose: bool):
    logger.remove()
    logger.add(
        sys.stderr,
        format="<magenta>{time:YYYY-MM-DD HH:mm:ss.SSS}</magenta> <level>[{level}]</level> > <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    logger.add(sink=log_path, level="INFO", rotation="10 MB")  # 每个日志文件最大为 10MB
    if verbose:
        logger.exception(message)
    else:
        logger.critical(f"{message} {exception!r}")
