from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys
from typing import Any

from pydantic import BaseModel, Field

from iamai import Runtime
from iamai.adapters.onebot11 import OneBot11Adapter
from iamai.adapters.telegram import TelegramAdapter
from iamai.adapters.webhook import WebhookAdapter
from iamai.config_schema import (
    CONFIG_SCHEMA_CONTRACT_VERSION,
    CONFIG_SCHEMA_ID,
    build_config_schema,
)
from iamai.plugins.management_api import ManagementApiPlugin
from iamai.runtime import dump_config_schema, main

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_ROOT = PROJECT_ROOT / "tests" / "golden"


def _property(schema: dict[str, Any], section: str, extension: str, field: str) -> dict[str, Any]:
    return schema["properties"][section]["properties"][extension]["properties"][field]


def _write_config(path: Path, body: str = "") -> Path:
    config_path = path / "config.toml"
    config_path.write_text(
        """
[runtime]
adapters = []
plugins = []
builtin_plugins = false
""".lstrip()
        + body,
        encoding="utf-8",
    )
    return config_path


def test_root_schema_matches_versioned_contract_golden() -> None:
    schema = build_config_schema(adapters={}, plugins={})
    projection = {
        "$schema": schema["$schema"],
        "$id": schema["$id"],
        "x-iamai-contract-version": schema["x-iamai-contract-version"],
        "type": schema["type"],
        "property_order": list(schema["properties"]),
        "property_ids": {
            name: property_schema["$id"]
            for name, property_schema in schema["properties"].items()
        },
        "additionalProperties": schema["additionalProperties"],
    }

    assert schema["$id"] == CONFIG_SCHEMA_ID
    assert schema["x-iamai-contract-version"] == CONFIG_SCHEMA_CONTRACT_VERSION
    assert projection == json.loads(
        (GOLDEN_ROOT / "config_schema_v1.json").read_text(encoding="utf-8")
    )


def test_extension_schemas_are_sorted_stable_and_open_to_unknown_tables() -> None:
    class ConfiglessExtension:
        config_model = None

    schema = build_config_schema(
        adapters={"zeta": ConfiglessExtension, "alpha": ConfiglessExtension},
        plugins={"two words": ConfiglessExtension, "beta": ConfiglessExtension},
    )
    adapter_schema = schema["properties"]["adapter"]
    plugin_schema = schema["properties"]["plugin"]

    assert list(adapter_schema["properties"]) == ["alpha", "zeta"]
    assert list(plugin_schema["properties"]) == ["beta", "two words"]
    assert adapter_schema["properties"]["alpha"] == {
        "$id": "urn:iamai:config-schema:v1:adapter:alpha",
        "type": "object",
        "additionalProperties": True,
    }
    assert plugin_schema["properties"]["two words"]["$id"] == (
        "urn:iamai:config-schema:v1:plugin:two%20words"
    )
    assert adapter_schema["additionalProperties"] == {
        "type": "object",
        "additionalProperties": True,
    }
    assert plugin_schema["additionalProperties"] == {
        "type": "object",
        "additionalProperties": True,
    }


def test_pydantic_and_dataclass_config_models_are_supported() -> None:
    class PydanticConfig(BaseModel):
        enabled: bool = True

    @dataclass
    class DataclassConfig:
        port: int = 4321

    class PydanticExtension:
        config_model = PydanticConfig

    class DataclassExtension:
        config_model = DataclassConfig

    schema = build_config_schema(
        adapters={"dataclass": DataclassExtension},
        plugins={"pydantic": PydanticExtension},
    )

    assert _property(schema, "adapter", "dataclass", "port")["default"] == 4321
    assert _property(schema, "plugin", "pydantic", "enabled")["default"] is True


def test_schema_generation_does_not_execute_default_factories() -> None:
    calls: list[str] = []

    def forbidden_factory() -> list[str]:
        calls.append("executed")
        raise AssertionError("schema generation executed a default factory")

    class FactoryConfig(BaseModel):
        values: list[str] = Field(
            default_factory=forbidden_factory,
            json_schema_extra={"default": ["declared"]},
        )

    class FactoryExtension:
        config_model = FactoryConfig

    first = build_config_schema(adapters={}, plugins={"factory": FactoryExtension})
    second = build_config_schema(adapters={}, plugins={"factory": FactoryExtension})

    assert calls == []
    assert _property(first, "plugin", "factory", "values")["default"] == ["declared"]
    assert first == second


def test_core_defaults_and_false_state_are_explicit() -> None:
    schema = build_config_schema(adapters={}, plugins={})
    runtime = schema["properties"]["runtime"]
    logging = schema["properties"]["logging"]
    state = schema["properties"]["state"]

    assert runtime["default"] == {}
    assert runtime["properties"]["log_level"]["default"] == "INFO"
    assert runtime["properties"]["command_prefixes"]["default"] == ["/"]
    assert runtime["properties"]["adapters"]["default"] == []
    assert logging["default"] == {}
    assert logging["properties"]["level"]["default"] == "INFO"
    assert state["default"] == {}
    assert {branch.get("const") for branch in state["anyOf"] if "const" in branch} == {False}


def test_write_only_is_explicit_and_not_inferred_from_field_names() -> None:
    class SecretConfig(BaseModel):
        credential: str = Field(default="", json_schema_extra={"writeOnly": True})
        max_tokens: int = 128
        token_hint: str = "not-secret-metadata"

    class SecretExtension:
        config_model = SecretConfig

    schema = build_config_schema(adapters={}, plugins={"secrets": SecretExtension})

    assert _property(schema, "plugin", "secrets", "credential")["writeOnly"] is True
    assert "writeOnly" not in _property(schema, "plugin", "secrets", "max_tokens")
    assert "writeOnly" not in _property(schema, "plugin", "secrets", "token_hint")


def test_builtin_extension_secret_annotations_and_defaults_are_visible() -> None:
    schema = build_config_schema(
        adapters={
            "onebot11": OneBot11Adapter,
            "telegram": TelegramAdapter,
            "webhook": WebhookAdapter,
        },
        plugins={"management_api": ManagementApiPlugin},
    )

    assert _property(schema, "adapter", "onebot11", "access_token")["writeOnly"] is True
    assert _property(schema, "adapter", "webhook", "access_token")["writeOnly"] is True
    assert _property(schema, "adapter", "webhook", "signature_secret")["writeOnly"] is True
    assert _property(schema, "adapter", "telegram", "token")["writeOnly"] is True
    assert _property(schema, "plugin", "management_api", "token")["writeOnly"] is True
    assert _property(schema, "adapter", "webhook", "reply_url_allowlist")["default"] == []
    assert _property(schema, "adapter", "telegram", "allowed_updates")["default"] == ["message"]


def test_runtime_schema_uses_metadata_only_and_never_leaks_configured_secrets(
    tmp_path: Path,
) -> None:
    sentinel = "runtime-secret-sentinel-0.4-b"
    runtime = Runtime(
        {
            "runtime": {
                "adapters": ["onebot11", "telegram", "webhook"],
                "plugins": ["management_api"],
                "builtin_plugins": False,
            },
            "adapter": {
                "onebot11": {"access_token": sentinel},
                "telegram": {"token": sentinel},
                "webhook": {"access_token": sentinel, "signature_secret": sentinel},
            },
            "plugin": {"management_api": {"token": sentinel}},
            "state": {},
            "__meta__": {"root_dir": str(tmp_path)},
        },
        base_path=tmp_path,
    )
    runtime.load_plugins()
    runtime.load_adapters()

    serialized = json.dumps(runtime.config_schema(), sort_keys=True)

    assert sentinel not in serialized


def test_no_argument_cli_schema_exactly_matches_runtime_schema(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    config_path = _write_config(tmp_path)
    runtime = Runtime.from_config_file(config_path)
    runtime.load_plugins()
    runtime.load_adapters()
    expected = runtime.config_schema()

    monkeypatch.setattr(sys, "argv", ["iamai", "--config", str(config_path), "config-schema"])
    main()

    assert json.loads(capsys.readouterr().out) == expected


def test_cli_plugin_selector_remains_backward_compatible(
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    config_path = tmp_path / "config.toml"
    # Use the built-in management API through its import reference while keeping
    # the root fixture independent of the built-in plugin selection policy.
    config_path.write_text(
        """
[runtime]
adapters = []
plugins = ["iamai.plugins.management_api:ManagementApiPlugin"]
builtin_plugins = false

[plugin.management_api]
token = "configured-token-that-must-not-appear"
""".lstrip(),
        encoding="utf-8",
    )
    expected = dump_config_schema(config_path, "management_api")

    monkeypatch.setattr(
        sys,
        "argv",
        ["iamai", "--config", str(config_path), "config-schema", "management_api"],
    )
    main()
    actual = json.loads(capsys.readouterr().out)

    assert actual == expected
    assert actual["properties"]["token"]["writeOnly"] is True
    assert "configured-token-that-must-not-appear" not in json.dumps(actual)
