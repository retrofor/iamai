from __future__ import annotations

from pathlib import Path

import tomli

ROOT = Path(__file__).resolve().parents[1]
SETUP_UV_ACTION = "astral-sh/setup-uv@v8.3.2"


def _load_toml(path: str) -> dict[str, object]:
    return tomli.loads((ROOT / path).read_text(encoding="utf-8"))


def _package_version(lock: dict[str, object], name: str) -> str:
    packages = lock.get("package", [])
    assert isinstance(packages, list)
    package = next(item for item in packages if isinstance(item, dict) and item.get("name") == name)
    return str(package["version"])


def _production_registry_packages(lock: dict[str, object], root_name: str) -> set[str]:
    packages = lock.get("package", [])
    assert isinstance(packages, list)
    packages_by_name = {
        str(package["name"]): package
        for package in packages
        if isinstance(package, dict) and "name" in package
    }
    assert len(packages_by_name) == len(packages)

    pending = [root_name]
    visited: set[str] = set()
    registry_packages: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        package = packages_by_name[name]
        source = package.get("source", {})
        assert isinstance(source, dict)
        if "registry" in source:
            registry_packages.add(name)
        dependencies = package.get("dependencies", [])
        assert isinstance(dependencies, list)
        pending.extend(
            str(dependency["name"])
            for dependency in dependencies
            if isinstance(dependency, dict) and "name" in dependency
        )

    return registry_packages


def test_release_version_is_synchronized_across_package_metadata() -> None:
    python_version = str(_load_toml("pyproject.toml")["project"]["version"])  # type: ignore[index]
    rust_version = str(_load_toml("Cargo.toml")["package"]["version"])  # type: ignore[index]
    cargo_lock_version = _package_version(_load_toml("Cargo.lock"), "iamai-core")
    uv_lock_version = _package_version(_load_toml("uv.lock"), "iamai")

    assert python_version == rust_version == cargo_lock_version == uv_lock_version
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{python_version}]" in changelog


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


def test_fossa_scans_only_declared_runtime_dependencies() -> None:
    root_project = _load_toml("pyproject.toml")["project"]
    compliance_project = _load_toml("compliance/fossa/pyproject.toml")["project"]
    assert compliance_project["dependencies"] == root_project["dependencies"]  # type: ignore[index]

    # Release metadata uses ranges, so this lock resolves independently from the workspace lock.
    root_packages = _production_registry_packages(_load_toml("uv.lock"), "iamai")
    compliance_packages = _production_registry_packages(
        _load_toml("compliance/fossa/uv.lock"),
        "iamai-fossa-production",
    )
    assert compliance_packages == root_packages

    config = (ROOT / ".fossa.yml").read_text(encoding="utf-8")
    assert config == (
        "version: 3\n"
        "\n"
        "targets:\n"
        "  only:\n"
        "    - type: cargo\n"
        "      path: .\n"
        "    # FOSSA 3.17.12 prefilters uv discovery as pipenv before reporting it as uv.\n"
        "    - type: pipenv\n"
        "      path: compliance/fossa\n"
        "    - type: uv\n"
        "      path: compliance/fossa\n"
    )
