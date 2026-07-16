from __future__ import annotations

from pathlib import Path
import re

import tomli

ROOT = Path(__file__).resolve().parents[1]
SETUP_UV_ACTION = "astral-sh/setup-uv@v8.3.2"
_RELEASE_VERSION_PATTERN = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-?(?P<prerelease>a|alpha|b|beta|rc)[.-]?(?P<number>0|[1-9]\d*))?$"
)


def _load_toml(path: str) -> dict[str, object]:
    return tomli.loads((ROOT / path).read_text(encoding="utf-8"))


def _package_version(lock: dict[str, object], name: str) -> str:
    packages = lock.get("package", [])
    assert isinstance(packages, list)
    package = next(item for item in packages if isinstance(item, dict) and item.get("name") == name)
    return str(package["version"])


def _semantic_release_version(version: str) -> tuple[int, int, int, str, int]:
    match = _RELEASE_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"unsupported release version: {version!r}")
    prerelease = {"alpha": "a", "beta": "b"}.get(
        match.group("prerelease") or "",
        match.group("prerelease") or "",
    )
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        prerelease,
        int(match.group("number")) if match.group("number") is not None else -1,
    )


def test_release_version_is_synchronized_across_package_metadata() -> None:
    python_version = str(_load_toml("pyproject.toml")["project"]["version"])  # type: ignore[index]
    rust_version = str(_load_toml("Cargo.toml")["package"]["version"])  # type: ignore[index]
    cargo_lock_version = _package_version(_load_toml("Cargo.lock"), "iamai-core")
    uv_lock_version = _package_version(_load_toml("uv.lock"), "iamai")

    expected = _semantic_release_version(python_version)
    assert _semantic_release_version(rust_version) == expected
    assert _semantic_release_version(cargo_lock_version) == expected
    assert _semantic_release_version(uv_lock_version) == expected
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{python_version}]" in changelog


def test_release_version_semantics_preserve_prerelease_identity() -> None:
    assert _semantic_release_version("1.0.0rc1") == _semantic_release_version("1.0.0-rc.1")
    assert _semantic_release_version("1.0.0rc1") != _semantic_release_version("1.0.0-rc.2")
    assert _semantic_release_version("1.0.0rc1") != _semantic_release_version("1.0.0")


def test_mit_license_is_declared_across_release_packages() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert license_text.startswith("MIT License\n")

    python_project = _load_toml("pyproject.toml")["project"]
    assert python_project["license"] == "MIT"  # type: ignore[index]
    assert python_project["license-files"] == ["LICENSE"]  # type: ignore[index]
    assert _load_toml("Cargo.toml")["package"]["license"] == "MIT"  # type: ignore[index]

    workspace = _load_toml("pyproject.toml")["tool"]["uv"]["workspace"]  # type: ignore[index]
    for member in workspace["members"]:  # type: ignore[index]
        project = _load_toml(f"{member}/pyproject.toml")["project"]
        assert project["license"] == "MIT", member  # type: ignore[index]


def test_tag_workflow_owns_the_github_and_pypi_release() -> None:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "tags: ['v*']" in workflow
    assert "uv publish --check-url https://pypi.org/simple" in workflow
    assert "gh release create" in workflow
    assert "gh release edit" in workflow
    assert "--json isDraft" in workflow
    assert "name: Validate release source" in workflow
    assert 'test "$GITHUB_REF_NAME" = "v$package_version"' in workflow
    assert "uv sync --locked --all-packages --group dev --group docs" in workflow
    assert workflow.index("name: Validate release source") < workflow.index("name: Build wheels")
    assert workflow.index("uv publish") < workflow.index("gh release upload")
    assert not (ROOT / ".github/workflows/changelog.yml").exists()


def test_workflows_pin_setup_uv_to_a_resolvable_release_tag() -> None:
    for path in (".github/workflows/check.yml", ".github/workflows/release.yml"):
        workflow = (ROOT / path).read_text(encoding="utf-8")
        assert SETUP_UV_ACTION in workflow
        assert "astral-sh/setup-uv@v8\n" not in workflow


def test_pre_commit_ci_has_a_repository_configuration() -> None:
    config_path = ROOT / ".pre-commit-config.yaml"
    assert config_path.is_file()
    config = config_path.read_text(encoding="utf-8")
    assert "https://github.com/pre-commit/pre-commit-hooks" in config
    assert "rev: v6.0.0" in config
