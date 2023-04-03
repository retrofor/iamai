from loguru import logger
import sys

# logger.remove()  # 清除默认输出处理器

# 添加控制台输出处理器
# console_handler = logger.add(sys.stderr, level="INFO", colorize=True,format="<level>{level: ^8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - {message}")

# 添加文件输出处理器
file_handler = logger.add("file.log", level="DEBUG", rotation="1 week", retention="10 days",
                          enqueue=True, compression="gz", encoding="utf-8", format="{time} - {level} - {message}")

# 配置loguru日志记录器
# logger.configure(console_handler)

# 在需要记录日志的地方调用logger即可，例如：
logger.info("Hello world!")
