import loguru

logger = loguru.logger

logger.configure(
)

logger = logger.bind(name="iamai")

__all__ = ["logger"]