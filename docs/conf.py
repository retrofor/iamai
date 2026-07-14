from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE = ROOT / "python"
DOCS_EXT = ROOT / "docs" / "_ext"

sys.path.insert(0, str(PYTHON_SOURCE))
sys.path.insert(0, str(DOCS_EXT))

class MockCoreModule(MagicMock):
    """Mock for the Rust _core extension."""

    CoreMessage = MagicMock

    @staticmethod
    def deep_merge_json(base: str, overlay: str) -> str:
        return overlay

    @staticmethod
    def next_event_id() -> str:
        return "mock_event_id"

    @staticmethod
    def normalize_onebot11_event(raw: str, adapter: str, platform: str) -> str:
        return raw


sys.modules["iamai._core"] = MockCoreModule()

project = "iamai"
author = "iamai contributors"
language = "zh_CN"
locale_dirs = ["locales"]
gettext_compact = False
gettext_uuid = True

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "iamai_mermaid",
    "iamai_blog",
    "iamai_store",
    "iamai_i18n_versions",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autosummary_generate = True
autosummary_imported_members = False
autodoc_member_order = "bysource"
autoclass_content = "both"
autodoc_typehints = "description"
autodoc_mock_imports = ["openai"]
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

html_theme = "furo"
html_title = "iamai Documentation"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_logo = "_static/brand/iamai-logo.svg"
html_favicon = "_static/brand/favicon.ico"
iamai_store_registry_paths = ["ecosystem/entries"]
iamai_store_github_repo = "retrofor/iamai"
iamai_blog_registry_paths = ["community/blog/posts"]
iamai_docs_current_version = "dev"
iamai_docs_current_language = "zh_CN"
iamai_docs_versions = [
    {"name": "dev", "label": "Development", "url": "#", "current": True},
    {"name": "latest", "label": "Latest", "url": "/latest/zh_CN/"},
    {"name": "0.3", "label": "0.3", "url": "/0.3/zh_CN/"},
]
iamai_docs_languages = [
    {"name": "zh_CN", "label": "中文", "url": "#", "current": True},
    {"name": "en", "label": "English", "url": "/dev/en/"},
]
html_theme_options = {
    "navigation_with_keys": True,
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#0f766e",
        "color-brand-content": "#0d9488",
    },
    "dark_css_variables": {
        "color-brand-primary": "#5eead4",
        "color-brand-content": "#2dd4bf",
    },
}
