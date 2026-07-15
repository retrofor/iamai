from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tomllib
import zipfile

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SOURCE_ROOT = PROJECT_ROOT / "python"
FIXTURES_ROOT = PROJECT_ROOT / "tests" / "fixtures" / "extensions"


def _wheel_name(value: str) -> str:
    return re.sub(r"[-_.]+", "_", value)


def _wheel_version(value: str) -> str:
    return value.replace("-", "_")


def _record_row(path: str, content: bytes) -> tuple[str, str, str]:
    digest = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=")
    return path, f"sha256={digest.decode('ascii')}", str(len(content))


def _build_fixture_wheel(fixture_dir: Path, output_dir: Path) -> Path:
    """Build a minimal pure-Python wheel without requiring another build backend in CI."""
    pyproject = tomllib.loads((fixture_dir / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    distribution = str(project["name"])
    version = str(project["version"])
    normalized_distribution = _wheel_name(distribution)
    normalized_version = _wheel_version(version)
    dist_info = f"{normalized_distribution}-{normalized_version}.dist-info"

    files: dict[str, bytes] = {}
    for source_path in sorted((fixture_dir / "src").rglob("*.py")):
        archive_path = source_path.relative_to(fixture_dir / "src").as_posix()
        files[archive_path] = source_path.read_bytes()

    metadata_lines = [
        "Metadata-Version: 2.3",
        f"Name: {distribution}",
        f"Version: {version}",
        f"Summary: {project['description']}",
        f"Requires-Python: {project['requires-python']}",
    ]
    metadata_lines.extend(f"Requires-Dist: {item}" for item in project.get("dependencies", []))
    files[f"{dist_info}/METADATA"] = ("\n".join(metadata_lines) + "\n\n").encode()
    files[f"{dist_info}/WHEEL"] = (
        "Wheel-Version: 1.0\n"
        "Generator: iamai-test-fixture\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode()

    entry_point_lines: list[str] = []
    for group, entries in sorted(project.get("entry-points", {}).items()):
        entry_point_lines.append(f"[{group}]")
        entry_point_lines.extend(f"{name} = {value}" for name, value in sorted(entries.items()))
        entry_point_lines.append("")
    files[f"{dist_info}/entry_points.txt"] = "\n".join(entry_point_lines).encode()

    record_path = f"{dist_info}/RECORD"
    record_rows = [_record_row(path, content) for path, content in sorted(files.items())]
    record_rows.append((record_path, "", ""))
    record_buffer: list[str] = []
    for row in record_rows:
        writer_output = _csv_row(row)
        record_buffer.append(writer_output)
    files[record_path] = "".join(record_buffer).encode()

    output_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = output_dir / f"{normalized_distribution}-{normalized_version}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for archive_path, content in sorted(files.items()):
            wheel.writestr(archive_path, content)
    return wheel_path


def _csv_row(row: tuple[str, str, str]) -> str:
    from io import StringIO

    buffer = StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerow(row)
    return buffer.getvalue()


@pytest.fixture(scope="session")
def extension_wheels(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    output_dir = tmp_path_factory.mktemp("extension-wheels")
    return {
        name: _build_fixture_wheel(FIXTURES_ROOT / name, output_dir)
        for name in ("reference_plugin", "reference_adapter", "incompatible_plugin")
    }


def _uv_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("VIRTUAL_ENV", None)
    return environment


def _run_uv(
    tmp_path: Path,
    *arguments: str,
) -> subprocess.CompletedProcess[str]:
    uv = shutil.which("uv")
    if uv is None:
        raise RuntimeError("uv is required to run installed-distribution contract tests")
    return subprocess.run(
        [uv, *arguments],
        cwd=tmp_path,
        env=_uv_environment(),
        check=False,
        capture_output=True,
        text=True,
    )


def test_installed_entry_points_support_explicit_and_opt_in_auto_discovery(
    tmp_path: Path,
    extension_wheels: dict[str, Path],
) -> None:
    probe = tmp_path / "probe.py"
    probe.write_text(
        """
import importlib
import iamai
import json
import os
from pathlib import Path
import sys

from iamai import Runtime


def load(mode: str) -> dict[str, object]:
    explicit = mode == "explicit"
    config = {
        "runtime": {
            "adapters": ["reference_adapter"] if explicit else [],
            "plugins": ["reference_plugin"] if explicit else [],
            "builtin_plugins": False,
            "auto_discover_plugins": not explicit,
            "auto_discover_adapters": not explicit,
        },
        "adapter": {},
        "plugin": {},
        "state": {},
        "__meta__": {"root_dir": str(Path.cwd())},
    }
    runtime = Runtime(config, base_path=Path.cwd())
    runtime.load_plugins()
    runtime.load_adapters()
    plugin = runtime.plugins[0]
    adapter = runtime.adapters[0]
    plugin_module = importlib.import_module(plugin.__class__.__module__)
    adapter_module = importlib.import_module(adapter.__class__.__module__)
    return {
        "mode": mode,
        "plugins": [item.plugin_name for item in runtime.plugins],
        "adapters": [item.name for item in runtime.adapters],
        "plugin_module": str(Path(plugin_module.__file__).resolve()),
        "adapter_module": str(Path(adapter_module.__file__).resolve()),
    }


assert "PYTHONPATH" not in os.environ
print(
    json.dumps(
        {
            "prefix": sys.prefix,
            "site_packages": [
                str(Path(item).resolve()) for item in sys.path if "site-packages" in Path(item).parts
            ],
            "iamai_module": str(Path(iamai.__file__).resolve()),
            "runs": [load("explicit"), load("auto")],
        }
    )
)
""".lstrip(),
        encoding="utf-8",
    )
    result = _run_uv(
        tmp_path,
        "run",
        "--isolated",
        "--no-editable",
        "--no-default-groups",
        "--frozen",
        "--project",
        str(PROJECT_ROOT),
        "--with",
        str(extension_wheels["reference_plugin"]),
        "--with",
        str(extension_wheels["reference_adapter"]),
        "python",
        str(probe),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    site_packages = [Path(item) for item in payload["site_packages"]]
    iamai_module = Path(payload["iamai_module"])
    assert any(iamai_module.is_relative_to(path) for path in site_packages)
    assert not iamai_module.is_relative_to(PROJECT_SOURCE_ROOT)
    for run in payload["runs"]:
        assert run["plugins"] == ["reference_plugin"]
        assert run["adapters"] == ["reference_adapter"]
        assert any(Path(run["plugin_module"]).is_relative_to(path) for path in site_packages)
        assert any(Path(run["adapter_module"]).is_relative_to(path) for path in site_packages)
        assert str(FIXTURES_ROOT) not in run["plugin_module"]
        assert str(FIXTURES_ROOT) not in run["adapter_module"]


def test_standard_resolver_rejects_incompatible_iamai_requirement(
    tmp_path: Path,
    extension_wheels: dict[str, Path],
) -> None:
    result = _run_uv(
        tmp_path,
        "run",
        "--isolated",
        "--no-editable",
        "--no-default-groups",
        "--frozen",
        "--project",
        str(PROJECT_ROOT),
        "--with",
        str(extension_wheels["incompatible_plugin"]),
        "python",
        "-c",
        "raise SystemExit('resolver unexpectedly accepted incompatible extension')",
    )

    assert result.returncode != 0
    assert "iamai-plugin-incompatible" in result.stderr
    assert "iamai>=99" in result.stderr.replace(" ", "")
