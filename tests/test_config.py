import os
import yaml
from pydantic import ValidationError
from iamai.config import MainConfig

current_dir = os.path.dirname(__file__)


def load_config(config_path: str) -> MainConfig:
    """从 YAML 文件加载配置."""
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        return MainConfig(**config_data)  # Pydantic 负责验证数据
    except FileNotFoundError:
        print(f"配置文件未找到: {config_path}")
        return MainConfig()  # 返回默认配置
    except yaml.YAMLError as e:
        print(f"YAML 解析错误: {e}")
        raise
    except ValidationError as e:
        print(f"配置验证错误: {e}")
        raise


# 示例用法
if __name__ == "__main__":
    config = load_config(os.path.join(current_dir, "config.yaml"))
    print(config.bot.name)
    print(config.log.level)
    print(config.middleware.middleware_settings)
