"""Pydantic and dataclass-backed plugin configuration validation helpers."""

from __future__ import annotations

from dataclasses import MISSING, asdict, fields, is_dataclass
from typing import Any

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError


class PluginConfigValidationError(ValueError):
    """Raised when a plugin configuration payload does not match its model."""

    pass


def validate_plugin_config(
    plugin_cls: type[Any],
    plugin_name: str,
    raw_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], Any | None]:
    """Validate plugin config and return normalized data plus the model instance."""
    raw = dict(raw_config or {})
    model = getattr(plugin_cls, "config_model", None)
    if model is None:
        return raw, None

    try:
        if isinstance(model, type) and issubclass(model, BaseModel):
            config_obj = model.model_validate(raw)
            return config_obj.model_dump(mode="python"), config_obj
        if isinstance(model, type) and is_dataclass(model):
            dataclass_config = model(**raw)
            return asdict(dataclass_config), dataclass_config
    except PydanticValidationError as exc:
        raise PluginConfigValidationError(
            f"invalid config for plugin {plugin_name!r}: {exc}"
        ) from exc
    except Exception as exc:
        raise PluginConfigValidationError(
            f"invalid config for plugin {plugin_name!r}: {exc}"
        ) from exc

    raise TypeError(
        f"unsupported config_model for plugin {plugin_name!r}: {model!r}"
    )


def plugin_config_schema(plugin_cls: type[Any]) -> dict[str, Any] | None:
    """Return a JSON Schema-like mapping for a plugin config model."""
    model = getattr(plugin_cls, "config_model", None)
    if model is None:
        return None
    if isinstance(model, type) and issubclass(model, BaseModel):
        return model.model_json_schema()
    if isinstance(model, type) and is_dataclass(model):
        properties: dict[str, Any] = {}
        required: list[str] = []
        for item in fields(model):
            properties[item.name] = {"title": item.name, "type": _schema_type(item.type)}
            if item.default is MISSING and item.default_factory is MISSING:
                required.append(item.name)
        return {"type": "object", "properties": properties, "required": required}
    return {"type": "object", "description": f"Unsupported config model: {model!r}"}


def _schema_type(annotation: Any) -> str:
    if annotation in (str, "str"):
        return "string"
    if annotation in (int, "int"):
        return "integer"
    if annotation in (float, "float"):
        return "number"
    if annotation in (bool, "bool"):
        return "boolean"
    if annotation in (list, "list"):
        return "array"
    return "object"
