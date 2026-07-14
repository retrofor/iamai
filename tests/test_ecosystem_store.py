from __future__ import annotations

# ruff: noqa: E402

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS_EXT = ROOT / "docs" / "_ext"
sys.path.insert(0, str(DOCS_EXT))

from iamai_store import (
    StoreEntry,
    StoreSubmission,
    build_submission_issue_body,
    build_submission_issue_url,
    iamaiStoreCardDirective,
    iamaiStoreSubmitDirective,
    load_store_index,
)


def _write_entry(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _entry(entry_id: str = "plugin.echo") -> dict[str, Any]:
    return {
        "id": entry_id,
        "name": "Echo Plugin",
        "type": "plugin",
        "summary": "Echo command plugin for local testing.",
        "package": "iamai-plugin-echo",
        "repository": "https://example.com/iamai-plugin-echo",
        "license": "MIT",
        "status": "active",
        "verification": ["community", "package_verified"],
        "entry_points": [
            {
                "group": "iamai.plugins",
                "name": "echo",
                "value": "iamai_plugin_echo:EchoPlugin",
            }
        ],
        "tags": ["echo", "demo"],
        "platforms": ["terminal"],
        "runtime_capabilities": ["network:http"],
        "security_notes": "No credentials required.",
        "permission_notes": "No agent permissions.",
    }


def _submission(entry_id: str = "plugin.echo") -> dict[str, Any]:
    payload = _entry(entry_id)
    payload["verification"] = ["community"]
    return payload


def test_store_entry_adds_default_install_command_and_search_text() -> None:
    entry = StoreEntry.model_validate(_entry())
    payload = entry.to_index_item()

    assert payload["install_command"] == "uv add iamai-plugin-echo"
    assert "echo plugin" in payload["search_text"]
    assert payload["runtime_capabilities"] == ["network:http"]
    assert payload["sort_rank"] == 30


def test_load_store_index_validates_entries_and_unique_ids(tmp_path: Path) -> None:
    entries = tmp_path / "entries"
    entries.mkdir()
    _write_entry(entries / "one.json", _entry("plugin.one"))
    _write_entry(entries / "two.json", _entry("plugin.two"))

    index = load_store_index(tmp_path, ["entries"])

    assert [entry.id for entry in index.entries] == ["plugin.one", "plugin.two"]


def test_load_store_index_rejects_duplicate_ids(tmp_path: Path) -> None:
    entries = tmp_path / "entries"
    entries.mkdir()
    _write_entry(entries / "one.json", _entry("plugin.same"))
    _write_entry(entries / "two.json", _entry("plugin.same"))

    with pytest.raises(ValueError, match="duplicate store entry id"):
        load_store_index(tmp_path, ["entries"])


def test_store_entry_rejects_invalid_url() -> None:
    payload = _entry()
    payload["repository"] = "not-a-url"

    with pytest.raises(ValueError, match="URL must be absolute"):
        StoreEntry.model_validate(payload)


def test_store_card_directive_outputs_target_slot() -> None:
    directive = iamaiStoreCardDirective.__new__(iamaiStoreCardDirective)
    directive.arguments = ["plugin.echo"]

    nodes = directive.run()

    assert 'data-iamai-store-card="plugin.echo"' in nodes[0].astext()


def test_store_submission_builds_community_registry_entry() -> None:
    submission = StoreSubmission.model_validate(_submission())

    entry = submission.to_store_entry()

    assert entry.status == "active"
    assert entry.verification == ["community"]
    assert entry.package == "iamai-plugin-echo"
    assert entry.security_notes == "No credentials required."


def test_store_submission_rejects_maintainer_verification_badges() -> None:
    payload = _entry()
    payload["verification"] = ["community", "official"]

    with pytest.raises(ValueError, match="maintainer review"):
        StoreSubmission.model_validate(payload)


def test_store_submission_requires_safety_fields_for_published_tools() -> None:
    payload = _submission("agent_tool.demo")
    payload["type"] = "agent_tool"
    payload["security_notes"] = ""
    payload["permission_notes"] = ""

    with pytest.raises(ValueError, match="security_notes is required"):
        StoreSubmission.model_validate(payload)

    payload["security_notes"] = "Uses outbound HTTPS."
    with pytest.raises(ValueError, match="permission_notes is required"):
        StoreSubmission.model_validate(payload)


def test_store_submission_issue_body_contains_registry_json() -> None:
    submission = StoreSubmission.model_validate(_submission())

    body = build_submission_issue_body(submission)

    assert "```json" in body
    assert '"id": "plugin.echo"' in body
    assert "Verification badges are assigned by maintainers only" in body


def test_store_submission_issue_url_targets_configured_repo() -> None:
    submission = StoreSubmission.model_validate(_submission())

    url = build_submission_issue_url("iamai/iamai", submission)

    assert url.startswith("https://github.com/iamai/iamai/issues/new?")
    assert "template=ecosystem-submission.yml" in url
    assert "%5BEcosystem%5D+Echo+Plugin" in url
    assert "runtime_capabilities=network%3Ahttp" in url


def test_store_submit_directive_outputs_submission_mount() -> None:
    class _Config:
        iamai_store_github_repo = "iamai/iamai"
        iamai_store_issue_template = "ecosystem-submission.yml"
        iamai_store_submit_api_url = ""

    class _App:
        config = _Config()

    class _Settings:
        class env:
            app = _App()

    class _Document:
        settings = _Settings()

    class _State:
        document = _Document()

    directive = iamaiStoreSubmitDirective.__new__(iamaiStoreSubmitDirective)
    directive.options = {}
    directive.state = _State()

    nodes = directive.run()

    html = nodes[0].astext()
    assert "data-iamai-store-submit" in html
    assert 'data-github-repo="iamai/iamai"' in html
