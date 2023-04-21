"""iamai 日志。

iamai 使用 [loguru](https://github.com/Delgan/loguru) 来记录日志信息。
自定义 logger 请参考 [loguru](https://github.com/Delgan/loguru) 文档。
"""
import sys

from loguru import logger as _logger

logger = _logger


def error_or_exception(message: str, exception: Exception, verbose: bool):
    logger.remove()
    logger.add(
        sys.stderr,
<<<<<<< HEAD
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> [<level>{level}</level>] > <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
=======
        format="<magenta>{time:YYYY-MM-DD HH:mm:ss.SSS}</magenta> <level>[{level}]</level> > <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
>>>>>>> 0ee2714126501b7068d8b0e65b8d3d4fb815cf16
    )
    if verbose:
        logger.exception(message)
    else:
        logger.critical(f"{message} {exception!r}")
