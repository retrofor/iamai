"""State store backends for plugin-scoped persistent data."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class StateStore:
    """Abstract state backend for plugin persistence."""

    def load_plugin_state(self, plugin_name: str) -> dict[str, Any]:
        """Load state for one plugin."""
        return {}

    def save_plugin_state(self, plugin_name: str, state: dict[str, Any]) -> None:
        """Persist state for one plugin."""
        return None


class NullStateStore(StateStore):
    """No-op state store used for memory-only operation."""

    pass


class JsonStateStore(StateStore):
    """JSON-file backed plugin state store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self.data: dict[str, Any] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {}
        self._loaded = True

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(payload, encoding="utf-8")
        temp_path.replace(self.path)

    def load_plugin_state(self, plugin_name: str) -> dict[str, Any]:
        """Load a copy of one plugin's JSON-backed state."""
        self._load()
        value = self.data.get(plugin_name, {})
        return dict(value) if isinstance(value, dict) else {}

    def save_plugin_state(self, plugin_name: str, state: dict[str, Any]) -> None:
        """Persist one plugin's state to the JSON store."""
        self._load()
        self.data[plugin_name] = dict(state)
        self._save()


class SqliteStateStore(StateStore):
    """SQLite-backed plugin state store."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10.0)

    def _ensure_table(self) -> None:
        with self._connect() as connection:
            connection.execute(
                "create table if not exists plugin_state "
                "(plugin_name text primary key, payload text not null)"
            )

    def load_plugin_state(self, plugin_name: str) -> dict[str, Any]:
        """Load one plugin's state from SQLite."""
        with self._connect() as connection:
            row = connection.execute(
                "select payload from plugin_state where plugin_name = ?",
                (plugin_name,),
            ).fetchone()
        if row is None:
            return {}
        value = json.loads(str(row[0]))
        return dict(value) if isinstance(value, dict) else {}

    def save_plugin_state(self, plugin_name: str, state: dict[str, Any]) -> None:
        """Persist one plugin's state to SQLite."""
        payload = json.dumps(dict(state), ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                "insert into plugin_state(plugin_name, payload) values(?, ?) "
                "on conflict(plugin_name) do update set payload = excluded.payload",
                (plugin_name, payload),
            )


def create_state_store(config: dict[str, Any], *, base_path: Path) -> StateStore:
    """Create the configured state store backend."""
    raw = config.get("state", {})
    if raw is False:
        return NullStateStore()
    if not isinstance(raw, dict):
        raw = {}
    backend = str(raw.get("backend", "memory"))
    if backend == "json":
        path = Path(str(raw.get("path", ".iamai/state.json")))
        if not path.is_absolute():
            path = base_path / path
        return JsonStateStore(path)
    if backend == "sqlite":
        path = Path(str(raw.get("path", ".iamai/state.sqlite3")))
        if not path.is_absolute():
            path = base_path / path
        return SqliteStateStore(path)
    return NullStateStore()
