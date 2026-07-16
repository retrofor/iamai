"""Pydantic and dataclass-backed extension configuration helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter
from pydantic import ValidationError as PydanticValidationError


class ExtensionConfigValidationError(ValueError):
    """Raised when an extension configuration payload does not match its model."""

    pass


class PluginConfigValidationError(ExtensionConfigValidationError):
    """Raised when a plugin configuration payload does not match its model."""

    pass


class AdapterConfigValidationError(ExtensionConfigValidationError):
    """Raised when an adapter configuration payload does not match its model."""

    pass


def validate_plugin_config(
    plugin_cls: type[Any],
    plugin_name: str,
    raw_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], Any | None]:
    """Validate plugin config and return normalized data plus the model instance."""
    return _validate_extension_config(
        plugin_cls,
        plugin_name,
        raw_config,
        kind="plugin",
        error_type=PluginConfigValidationError,
    )


def validate_adapter_config(
    adapter_cls: type[Any],
    adapter_name: str,
    raw_config: dict[str, Any] | None,
) -> tuple[dict[str, Any], Any | None]:
    """Validate adapter config and return normalized data plus the model instance."""
    return _validate_extension_config(
        adapter_cls,
        adapter_name,
        raw_config,
        kind="adapter",
        error_type=AdapterConfigValidationError,
    )


def plugin_config_schema(plugin_cls: type[Any]) -> dict[str, Any] | None:
    """Return the JSON Schema for a plugin config model."""
    model = getattr(plugin_cls, "config_model", None)
    if model is None:
        return None
    try:
        return config_model_schema(model)
    except TypeError:
        return {"type": "object", "description": f"Unsupported config model: {model!r}"}


def config_model_schema(model: Any) -> dict[str, Any]:
    """Return a validation-mode JSON Schema without instantiating the model."""
    if not _is_supported_config_model(model):
        raise TypeError(f"unsupported config model: {model!r}")
    return TypeAdapter(model).json_schema(mode="validation")


def _validate_extension_config(
    extension_cls: type[Any],
    extension_name: str,
    raw_config: dict[str, Any] | None,
    *,
    kind: str,
    error_type: type[ExtensionConfigValidationError],
) -> tuple[dict[str, Any], Any | None]:
    raw = dict(raw_config or {})
    model = getattr(extension_cls, "config_model", None)
    if model is None:
        return raw, None

    if not _is_supported_config_model(model):
        raise TypeError(f"unsupported config_model for {kind} {extension_name!r}: {model!r}")

    try:
        config_obj = TypeAdapter(model).validate_python(raw)
        if isinstance(config_obj, BaseModel):
            return config_obj.model_dump(mode="python"), config_obj
        if is_dataclass(config_obj) and not isinstance(config_obj, type):
            return asdict(config_obj), config_obj
    except PydanticValidationError as exc:
        raise error_type(f"invalid config for {kind} {extension_name!r}: {exc}") from exc
    except Exception as exc:
        raise error_type(f"invalid config for {kind} {extension_name!r}: {exc}") from exc

    raise TypeError(f"unsupported config_model for {kind} {extension_name!r}: {model!r}")


def _is_supported_config_model(model: Any) -> bool:
    return isinstance(model, type) and (
        issubclass(model, BaseModel) or is_dataclass(model)
    )
