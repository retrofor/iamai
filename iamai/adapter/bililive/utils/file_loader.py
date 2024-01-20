from pathlib import Path

import yaml
from genericpath import exists

DEFAULT_CONFIG_YML = {"debug": False, "roomid": 5651193}


def make_folder(folder: str) -> bool:
    path = Path(folder)
    if path.exists():
        return False
    else:
        path.mkdir(exist_ok=True, parents=True)
        return True


def load_config(yml: str, default_values: dict) -> any:
    make_folder("config")
    path = f"config/{yml}"
    data = {}
    if exists(path):
        with open(path, mode="r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    for k, v in data.items():
        default_values[k] = v
    if default_values.keys() != data.keys():
        with open(path, mode="w", encoding="utf-8") as f:
            yaml.safe_dump(default_values, f, allow_unicode=True)
    return default_values


def load_default_config() -> any:
    return load_config("config.yaml", DEFAULT_CONFIG_YML)
