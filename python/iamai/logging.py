"""Loguru-backed logging configuration for iamai."""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path
from types import FrameType
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    """Forward standard-library logging records into Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: FrameType | None = logging.currentframe()
        depth = 0
        ignored_files = {logging.__file__, __file__}
        while frame is not None and frame.f_code.co_filename in ignored_files:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(config: dict[str, Any], *, base_path: Path) -> None:
    """Configure the process logging pipeline from validated config."""

    logging_config = dict(config.get("logging", {}))
    if not logging_config.get("enabled", True):
        logger.remove()
        logging.disable(logging.CRITICAL)
        return

    logging.disable(logging.NOTSET)
    logger.remove()
    level = str(logging_config.get("level", "INFO")).upper()
    log_format = str(logging_config.get("format"))
    serialize = bool(logging_config.get("serialize", False))
    backtrace = bool(logging_config.get("backtrace", False))
    diagnose = bool(logging_config.get("diagnose", False))
    enqueue = bool(logging_config.get("enqueue", False))
    catch = bool(logging_config.get("catch", True))

    if logging_config.get("stderr", True):
        logger.add(
            sys.stderr,
            level=level,
            format=log_format,
            serialize=serialize,
            backtrace=backtrace,
            diagnose=diagnose,
            enqueue=enqueue,
            catch=catch,
            colorize=logging_config.get("colorize"),
        )

    if logging_config.get("file"):
        file_path = Path(str(logging_config["file"])).expanduser()
        if not file_path.is_absolute():
            file_path = base_path / file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            file_path,
            level=level,
            format=log_format,
            serialize=serialize,
            backtrace=backtrace,
            diagnose=diagnose,
            enqueue=enqueue,
            catch=catch,
            rotation=logging_config.get("rotation"),
            retention=logging_config.get("retention"),
            compression=logging_config.get("compression"),
            colorize=False,
        )

    if logging_config.get("intercept_stdlib", True):
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        for name in logging.root.manager.loggerDict:
            logging.getLogger(name).handlers = []
            logging.getLogger(name).propagate = True

    if logging_config.get("capture_warnings", True):
        logging.captureWarnings(True)
    else:
        logging.captureWarnings(False)
        warnings.simplefilter("default")


def get_logger(name: str) -> Any:
    """Return a named Loguru logger."""

    return logger.bind(name=name)
