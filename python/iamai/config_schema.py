"""Deterministic JSON Schema composition for iamai configuration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

from .config import LoggingConfigModel, RuntimeConfigModel, StateConfigModel
from .validation import config_model_schema

CONFIG_SCHEMA_CONTRACT_VERSION = "1"
CONFIG_SCHEMA_ID = "urn:iamai:config-schema:v1:root"

_SCHEMA_PREFIX = "urn:iamai:config-schema:v1"
_OPEN_TABLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": True,
}


def build_config_schema(
    *,
    adapters: Mapping[str, Any],
    plugins: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the versioned root schema for core and extension configuration."""
    properties = {
        "runtime": _core_schema("runtime", RuntimeConfigModel),
        "logging": _core_schema("logging", LoggingConfigModel),
        "state": _state_schema(),
        "adapter": _extension_table_schema("adapter", adapters),
        "plugin": _extension_table_schema("plugin", plugins),
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": CONFIG_SCHEMA_ID,
        "x-iamai-contract-version": CONFIG_SCHEMA_CONTRACT_VERSION,
        "title": "iamai configuration",
        "type": "object",
        "properties": properties,
        "additionalProperties": True,
        "default": {},
    }


def _core_schema(name: str, model: type[Any]) -> dict[str, Any]:
    schema = config_model_schema(model)
    schema["$id"] = _child_id(name)
    schema["default"] = {}
    return schema


def _state_schema() -> dict[str, Any]:
    model_schema = config_model_schema(StateConfigModel)
    return {
        "$id": _child_id("state"),
        "anyOf": [
            model_schema,
            {"const": False, "type": "boolean"},
        ],
        "default": {},
    }


def _extension_table_schema(
    kind: str,
    extensions: Mapping[str, Any],
) -> dict[str, Any]:
    properties = {
        name: _extension_schema(kind, name, extension)
        for name, extension in sorted(extensions.items())
    }
    return {
        "$id": _child_id(kind),
        "type": "object",
        "properties": properties,
        "additionalProperties": dict(_OPEN_TABLE_SCHEMA),
        "default": {},
    }


def _extension_schema(kind: str, name: str, extension: Any) -> dict[str, Any]:
    model = _extension_config_model(extension)
    if model is None:
        schema = dict(_OPEN_TABLE_SCHEMA)
    else:
        schema = config_model_schema(model)
    schema["$id"] = _child_id(kind, name)
    return schema


def _extension_config_model(extension: Any) -> Any:
    if extension is None:
        return None
    marker = object()
    model = getattr(extension, "config_model", marker)
    return extension if model is marker else model


def _child_id(*parts: str) -> str:
    encoded = ":".join(quote(str(part), safe="") for part in parts)
    return f"{_SCHEMA_PREFIX}:{encoded}"
