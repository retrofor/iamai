from __future__ import annotations

import json
from importlib import resources

def read_json(name: str):
    return json.loads((resources.files(__package__) / name.removeprefix("data/")).read_text(encoding="utf-8"))


def read_lines(name: str) -> list[str]:
    return (resources.files(__package__) / name.removeprefix("data/")).read_text(encoding="utf-8").splitlines()


# Keep the old names so hot reload can survive mixed old/new imports.
load_json = read_json
load_text_lines = read_lines
