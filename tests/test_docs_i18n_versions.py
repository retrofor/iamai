from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS_EXT = ROOT / "docs" / "_ext"
sys.path.insert(0, str(DOCS_EXT))

from iamai_i18n_versions import SwitcherEntry, _normalize_entries  # noqa: E402


def test_normalize_entries_marks_current_item() -> None:
    entries = _normalize_entries(
        [
            {"name": "dev", "label": "Development", "url": "/dev/"},
            {"name": "latest", "label": "Latest", "url": "/latest/"},
        ],
        current_name="latest",
    )

    assert [entry.current for entry in entries] == [False, True]


def test_normalize_entries_falls_back_to_current_name() -> None:
    entries = _normalize_entries([], current_name="dev")

    assert len(entries) == 1
    assert entries[0].name == "dev"
    assert entries[0].current is True


def test_switcher_entry_rejects_invalid_url() -> None:
    with pytest.raises(ValueError, match="url must be"):
        SwitcherEntry(name="bad", label="Bad", url="javascript:alert(1)")
