
# config_loader.py

import json
import yaml
import toml

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def load_yaml(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def load_toml(file_path):
    with open(file_path, 'r') as file:
        return toml.load(file)

def load_py(file_path):
    with open(file_path, 'r') as file:
        code = compile(file.read(), file_path, 'exec')
        config = {}
        exec(code, config)
        return config

def load_config(file_path):
    if file_path.endswith('.json'):
        return load_json(file_path)
    elif file_path.endswith('.yml') or file_path.endswith('.yaml'):
        return load_yaml(file_path)
    elif file_path.endswith('.toml'):
        return load_toml(file_path)
    elif file_path.endswith('.py'):
        return load_py(file_path)
    else:
        raise ValueError("Unsupported file format")