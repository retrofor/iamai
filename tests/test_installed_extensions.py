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
import asyncio
import json
import os
from pathlib import Path
import sys

from iamai import Context, Message, Runtime
from iamai.harness import (
    Action,
    ControlledToolEnvironment,
    ExactEvaluator,
    Experiment,
    ExecutionBudget,
    ExecutionPolicy,
    JsonlTrajectoryStore,
    ScriptedAgent,
    Task,
    Tool,
    ToolResult,
    ToolSpec,
    Trial,
    TrialConfig,
)
from iamai.testing import (
    assert_adapter_api_result,
    assert_adapter_can_close,
    assert_adapter_cancellation,
    assert_adapter_config,
    assert_adapter_error,
    assert_adapter_event,
    assert_adapter_lifecycle,
    assert_adapter_send_result,
    assert_adapter_start_failure,
    assert_plugin_config,
    assert_plugin_dependencies,
    assert_plugin_handler,
    assert_plugin_lifecycle,
    assert_plugin_metadata,
    assert_plugin_permission,
    assert_plugin_startup_failure_cleanup,
)


async def run_conformance(runtime, plugin, adapter):
    plugin_module = importlib.import_module(plugin.__class__.__module__)
    adapter_module = importlib.import_module(adapter.__class__.__module__)

    configured_adapter = assert_adapter_config(
        adapter.__class__,
        runtime,
        config={"access_token": "fixture-secret"},
        expected={"endpoint": "https://example.invalid/events"},
    )
    event = configured_adapter.normalize(
        {
            "id": "evt-installed",
            "channel_id": "room",
            "user_id": "allowed",
            "text": "hello from wheel",
        }
    )
    assert_adapter_event(
        event,
        adapter="reference_adapter",
        expected_fields={"channel_id": "room", "text": "hello from wheel"},
    )
    assert_adapter_send_result(
        await configured_adapter.send_message(Message("pong"), event=event),
        expected={"target": "room", "text": "pong"},
    )
    assert_adapter_api_result(
        await configured_adapter.call_api("ping", value=1),
        expected={"action": "ping", "params": {"value": 1}},
    )
    await assert_adapter_error(
        configured_adapter.call_api("fail"),
        error_type=adapter_module.ReferenceAdapterError,
        match="forced reference API failure",
    )
    await assert_adapter_can_close(configured_adapter)

    lifecycle_adapter = adapter.__class__(runtime)
    await assert_adapter_lifecycle(
        lifecycle_adapter,
        ready=lifecycle_adapter.started.is_set,
        clean=lambda: lifecycle_adapter.closed,
    )
    cancellation_adapter = adapter.__class__(runtime)
    await assert_adapter_cancellation(
        cancellation_adapter,
        ready=cancellation_adapter.started.is_set,
        clean=lambda: cancellation_adapter.closed,
    )
    failing_adapter = adapter_module.ReferenceFailingAdapter(runtime)
    await assert_adapter_start_failure(
        failing_adapter,
        error_type=adapter_module.ReferenceAdapterError,
        match="forced reference startup failure",
        clean=lambda: not failing_adapter.resource_open,
    )

    assert_plugin_metadata(plugin.__class__)
    assert_plugin_dependencies(plugin.__class__)
    plugin_config, plugin_config_obj = assert_plugin_config(
        plugin.__class__,
        {"greeting": "hello from conformance"},
    )
    assert plugin_config["greeting"] == "hello from conformance"
    assert plugin_config_obj.greeting == "hello from conformance"
    handler = assert_plugin_handler(plugin, "handle", kind="message")
    context = Context(
        runtime=runtime,
        adapter=adapter,
        plugin=plugin,
        event=event,
        handler=handler,
    )
    await assert_plugin_permission(handler, context, expected=True)

    lifecycle_plugin = plugin.__class__(runtime)
    await assert_plugin_lifecycle(
        lifecycle_plugin,
        cleanup=lambda: not lifecycle_plugin.active,
    )
    failing_plugin = plugin_module.ReferenceFailingPlugin(runtime)
    await assert_plugin_startup_failure_cleanup(
        failing_plugin,
        cleanup=lambda: not failing_plugin.active,
        expected_exception=RuntimeError,
    )
    return {"adapter": True, "plugin": True}


async def run_harness():
    async def installed_tool(arguments):
        return ToolResult(
            output=arguments["value"],
            tokens=1,
            cost_microunits=2,
        )

    path = Path("installed-harness.jsonl")
    result = await Experiment(
        experiment_id="installed-harness",
        version="1",
        baseline="baseline",
        provenance={"distribution": "installed"},
        trials={
            "baseline": (
                Trial(
                    task=Task(id="installed-task", input=None),
                    agent=ScriptedAgent(
                        [
                            Action.invoke("installed-tool", {"value": "observed"}),
                            Action.finish("done"),
                        ],
                        name="installed-agent",
                        version="1",
                    ),
                    environment=ControlledToolEnvironment(
                        tools=(
                            Tool(
                                ToolSpec(
                                    name="installed-tool",
                                    version="1",
                                    input_schema={
                                        "type": "object",
                                        "properties": {"value": {"type": "string"}},
                                        "required": ["value"],
                                        "additionalProperties": False,
                                    },
                                    permission_name="installed.read",
                                    reserved_tokens=1,
                                    reserved_cost_microunits=2,
                                ),
                                installed_tool,
                            ),
                        ),
                        policy=ExecutionPolicy(
                            version="1",
                            allowed_tools=("installed-tool",),
                            allowed_permissions=("installed.read",),
                        ),
                        budget=ExecutionBudget(
                            max_tool_calls=1,
                            max_tokens=1,
                            max_cost_microunits=2,
                            tool_timeout_seconds=1,
                            currency="USD",
                            pricing_version="installed-fixture-1",
                        ),
                        name="installed-environment",
                        version="1",
                    ),
                    evaluator=ExactEvaluator("done", version="1"),
                    config=TrialConfig(trial_id="installed-trial", max_actions=2),
                ),
            )
        },
    ).run(JsonlTrajectoryStore(path))
    loaded = JsonlTrajectoryStore(path).load()
    trajectory = result.results["baseline"][0].trajectory
    tool_outcome = next(
        record for record in trajectory.records if record.kind == "tool.call.outcome"
    )
    return {
        "complete": result.complete,
        "round_trip": loaded == result,
        "status": result.results["baseline"][0].status.value,
        "tool_status": tool_outcome.payload["status"],
    }


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
        "schema": runtime.config_schema(),
        "conformance": asyncio.run(run_conformance(runtime, plugin, adapter)),
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
            "harness": asyncio.run(run_harness()),
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
        "--refresh-package",
        "iamai",
        "--no-editable",
        "--no-default-groups",
        "--frozen",
        "--project",
        str(PROJECT_ROOT),
        "--with",
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
    assert payload["harness"] == {
        "complete": True,
        "round_trip": True,
        "status": "completed",
        "tool_status": "succeeded",
    }
    for run in payload["runs"]:
        assert run["plugins"] == ["reference_plugin"]
        assert run["adapters"] == ["reference_adapter"]
        assert run["conformance"] == {"adapter": True, "plugin": True}
        assert any(Path(run["plugin_module"]).is_relative_to(path) for path in site_packages)
        assert any(Path(run["adapter_module"]).is_relative_to(path) for path in site_packages)
        assert str(FIXTURES_ROOT) not in run["plugin_module"]
        assert str(FIXTURES_ROOT) not in run["adapter_module"]
        schema = run["schema"]
        plugin_schema = schema["properties"]["plugin"]["properties"]["reference_plugin"]
        adapter_schema = schema["properties"]["adapter"]["properties"]["reference_adapter"]
        assert plugin_schema["$id"] == ("urn:iamai:config-schema:v1:plugin:reference_plugin")
        assert plugin_schema["properties"]["greeting"]["default"] == (
            "hello from the installed plugin"
        )
        assert plugin_schema["properties"]["credential"]["writeOnly"] is True
        assert "writeOnly" not in plugin_schema["properties"]["max_tokens"]
        assert adapter_schema["$id"] == ("urn:iamai:config-schema:v1:adapter:reference_adapter")
        assert adapter_schema["properties"]["endpoint"]["default"] == (
            "https://example.invalid/events"
        )
        assert adapter_schema["properties"]["access_token"]["writeOnly"] is True
        assert "writeOnly" not in adapter_schema["properties"]["token_hint"]


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
