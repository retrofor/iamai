"""Sphinx extension for iamai documentation i18n and version switching."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sphinx.application import Sphinx

SWITCHER_CONFIG_JS = "iamai-docs-switcher-config.js"
SWITCHER_JS = "iamai-docs-switcher.js"
SWITCHER_CSS = "iamai-docs-switcher.css"


class SwitcherEntry(BaseModel):
    """One selectable item in the docs switcher."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    label: str = Field(min_length=1)
    url: str = Field(min_length=1)
    current: bool = False

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str) -> str:
        if value.startswith(("#", "/", "http://", "https://", ".")):
            return value
        raise ValueError("url must be absolute, root-relative, relative, or #")


class SwitcherConfig(BaseModel):
    """Serialized switcher config consumed by the browser widget."""

    model_config = ConfigDict(extra="forbid")

    project: str
    current_version: str
    current_language: str
    versions: list[SwitcherEntry]
    languages: list[SwitcherEntry]

    def to_json_payload(self) -> dict[str, Any]:
        """Return the browser-facing JSON payload."""

        return self.model_dump(mode="json")


def build_switcher_config(app: Sphinx) -> SwitcherConfig:
    """Build the docs switcher config from Sphinx configuration."""

    current_version = str(getattr(app.config, "iamai_docs_current_version", "dev"))
    current_language = str(
        getattr(app.config, "iamai_docs_current_language", app.config.language or "zh_CN")
    )
    versions = _normalize_entries(
        getattr(app.config, "iamai_docs_versions", []),
        current_name=current_version,
    )
    languages = _normalize_entries(
        getattr(app.config, "iamai_docs_languages", []),
        current_name=current_language,
    )
    return SwitcherConfig(
        project=app.config.project,
        current_version=current_version,
        current_language=current_language,
        versions=versions,
        languages=languages,
    )


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the i18n/version switcher extension."""

    app.add_config_value("iamai_docs_current_version", "dev", "html", types=frozenset({str}))
    app.add_config_value("iamai_docs_current_language", "zh_CN", "html", types=frozenset({str}))
    app.add_config_value("iamai_docs_versions", [], "html", types=frozenset({list, tuple}))
    app.add_config_value("iamai_docs_languages", [], "html", types=frozenset({list, tuple}))
    app.connect("builder-inited", _on_builder_inited)
    app.connect("build-finished", _on_build_finished)
    app.add_js_file(SWITCHER_CONFIG_JS, defer="defer")
    app.add_js_file(SWITCHER_JS, defer="defer")
    app.add_css_file(SWITCHER_CSS)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def _normalize_entries(
    raw_entries: list[Any] | tuple[Any, ...], *, current_name: str
) -> list[SwitcherEntry]:
    entries: list[SwitcherEntry] = []
    for raw_entry in raw_entries:
        if isinstance(raw_entry, str):
            entry = SwitcherEntry(name=raw_entry, label=raw_entry, url="#")
        else:
            entry = SwitcherEntry.model_validate(raw_entry)
        if entry.name == current_name:
            entry.current = True
        entries.append(entry)
    if not entries:
        entries.append(SwitcherEntry(name=current_name, label=current_name, url="#", current=True))
    if not any(entry.current for entry in entries):
        entries[0].current = True
    return entries


def _on_builder_inited(app: Sphinx) -> None:
    app.env.iamai_docs_switcher_config = build_switcher_config(app).to_json_payload()


def _on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    if exception is not None:
        return
    static_dir = Path(app.outdir) / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)
    payload = getattr(
        app.env,
        "iamai_docs_switcher_config",
        SwitcherConfig(
            project=app.config.project,
            current_version="dev",
            current_language=str(app.config.language or "zh_CN"),
            versions=[SwitcherEntry(name="dev", label="dev", url="#", current=True)],
            languages=[
                SwitcherEntry(
                    name=str(app.config.language or "zh_CN"),
                    label="中文",
                    url="#",
                    current=True,
                )
            ],
        ).to_json_payload(),
    )
    (static_dir / SWITCHER_CONFIG_JS).write_text(
        "window.iamai_DOCS_SWITCHER = "
        + json.dumps(payload, ensure_ascii=False, sort_keys=True)
        + ";\n",
        encoding="utf-8",
    )
