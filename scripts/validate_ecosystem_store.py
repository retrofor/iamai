#!/usr/bin/env python3
"""Validate iamai ecosystem store registry entries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS_EXT = ROOT / "docs" / "_ext"
sys.path.insert(0, str(DOCS_EXT))

from iamai_store import STORE_INDEX_FILENAME, load_store_index  # noqa: E402


def main() -> None:
    """Run registry validation."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs-dir",
        default=str(ROOT / "docs"),
        help="Path to the Sphinx docs directory",
    )
    parser.add_argument(
        "--registry-path",
        action="append",
        dest="registry_paths",
        default=None,
        help="Registry path relative to docs-dir. Can be passed multiple times.",
    )
    parser.add_argument(
        "--write-index",
        type=Path,
        default=None,
        help="Optional path to write merged JSON index",
    )
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir).resolve()
    registry_paths = args.registry_paths or ["ecosystem/entries"]
    try:
        index = load_store_index(docs_dir, registry_paths)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    payload: dict[str, Any] = index.to_json_payload()
    print(f"ok: {len(payload['entries'])} ecosystem entries")
    if args.write_index is not None:
        args.write_index.parent.mkdir(parents=True, exist_ok=True)
        args.write_index.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(f"wrote {args.write_index}")
    else:
        print(f"index artifact: {STORE_INDEX_FILENAME}")


if __name__ == "__main__":
    main()
