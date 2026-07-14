from __future__ import annotations

from pathlib import Path

import tomli

ROOT = Path(__file__).resolve().parents[1]


def _load_toml(path: str) -> dict[str, object]:
    return tomli.loads((ROOT / path).read_text(encoding="utf-8"))


def _package_version(lock: dict[str, object], name: str) -> str:
    packages = lock.get("package", [])
    assert isinstance(packages, list)
    package = next(item for item in packages if isinstance(item, dict) and item.get("name") == name)
    return str(package["version"])


def test_release_version_is_synchronized_across_package_metadata() -> None:
    python_version = str(_load_toml("pyproject.toml")["project"]["version"])  # type: ignore[index]
    rust_version = str(_load_toml("Cargo.toml")["package"]["version"])  # type: ignore[index]
    cargo_lock_version = _package_version(_load_toml("Cargo.lock"), "iamai-core")
    uv_lock_version = _package_version(_load_toml("uv.lock"), "iamai")

    assert python_version == rust_version == cargo_lock_version == uv_lock_version
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{python_version}]" in changelog


def test_tag_workflow_owns_the_github_and_pypi_release() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "tags: ['v*']" in workflow
    assert "uv publish --check-url https://pypi.org/simple" in workflow
    assert "gh release create" in workflow
    assert "gh release edit" in workflow
    assert "--json isDraft" in workflow
    assert workflow.index("uv publish") < workflow.index("gh release upload")
    assert not (ROOT / ".github/workflows/changelog.yml").exists()
