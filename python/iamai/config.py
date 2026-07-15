"""Configuration loading, validation, redaction, and warning collection."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import tomli
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .core import merge_dicts
from .net import is_loopback_host
from .webhook_security import SUPPORTED_SIGNATURE_PROVIDERS

SENSITIVE_KEY_MARKERS = ("token", "secret", "password", "api_key", "authorization")


class ConfigValidationError(ValueError):
    """Raised when a TOML config file fails structural validation."""

    pass


class HotReloadConfig(BaseModel):
    """Hot reload settings for plugin and optional config reload polling."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    interval: float = 1.0
    config: bool = True

    @field_validator("interval")
    @classmethod
    def _validate_interval(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("interval must be greater than 0")
        return float(value)


class LoggingConfigModel(BaseModel):
    """Validated logging configuration consumed by the Loguru bridge."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    level: str = "INFO"
    format: str = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}"
    )
    colorize: bool | None = None
    serialize: bool = False
    backtrace: bool = False
    diagnose: bool = False
    enqueue: bool = False
    catch: bool = True
    stderr: bool = True
    file: str | None = None
    rotation: str | None = "10 MB"
    retention: str | None = "14 days"
    compression: str | None = None
    capture_warnings: bool = True
    intercept_stdlib: bool = True

    @field_validator("level")
    @classmethod
    def _normalize_level(cls, value: str) -> str:
        normalized = str(value).strip().upper()
        if not normalized:
            raise ValueError("level cannot be empty")
        return normalized


class RuntimeConfigModel(BaseModel):
    """Validated top-level ``[runtime]`` configuration."""

    model_config = ConfigDict(extra="forbid")

    log_level: str = "INFO"
    command_prefixes: list[str] = Field(default_factory=lambda: ["/"])
    adapters: list[str] = Field(default_factory=list)
    plugins: list[str] = Field(default_factory=list)
    plugin_dirs: list[str] = Field(default_factory=list)
    python_paths: list[str] = Field(default_factory=list)
    auto_discover_plugins: bool = False
    auto_discover_adapters: bool = False
    superusers: list[str] = Field(default_factory=list)
    builtin_plugins: list[str] | bool | None = None
    disable_builtin_plugins: list[str] = Field(default_factory=list)
    hot_reload: HotReloadConfig | bool = False
    allow_external_paths: bool = False
    max_concurrent_handlers: int = 64
    max_pending_handlers: int = 256
    handler_shutdown_timeout_seconds: float = 5.0
    session_backlog_max_keys: int = 1024
    session_backlog_per_key: int = 3
    session_backlog_ttl_seconds: float = 300.0

    @field_validator(
        "command_prefixes",
        "adapters",
        "plugins",
        "plugin_dirs",
        "python_paths",
        "superusers",
        "disable_builtin_plugins",
        mode="before",
    )
    @classmethod
    def _normalize_str_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("value must be a list")
        return [str(item) for item in value]

    @field_validator("command_prefixes")
    @classmethod
    def _validate_prefixes(cls, value: list[str]) -> list[str]:
        if any(not item for item in value):
            raise ValueError("command_prefixes cannot contain empty strings")
        return value or ["/"]

    @field_validator(
        "max_concurrent_handlers",
        "max_pending_handlers",
        "session_backlog_max_keys",
        "session_backlog_per_key",
    )
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("value must be greater than 0")
        return int(value)

    @field_validator("handler_shutdown_timeout_seconds", "session_backlog_ttl_seconds")
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if float(value) <= 0:
            raise ValueError("value must be greater than 0")
        return float(value)


class OneBot11ConfigModel(BaseModel):
    """Validated ``[adapter.onebot11]`` configuration."""

    model_config = ConfigDict(extra="forbid")

    mode: str = "ws-reverse"
    url: str = "ws://127.0.0.1:6700"
    host: str = "127.0.0.1"
    port: int = 8080
    path: str = "/onebot/v11/ws"
    path_event: str | None = None
    path_api: str | None = None
    api_base_url: str = "http://127.0.0.1:5700"
    access_token: str = ""
    allow_query_token: bool = False
    allow_insecure_no_token: bool = False
    platform: str = "qq"
    reconnect_interval: float = 5.0
    api_timeout: float = 10.0
    ping_interval: float = 20.0
    ping_timeout: float = 20.0
    open_timeout: float = 10.0
    max_size: int = 1_048_576
    origins: list[str] | None = None
    read_timeout: float = 10.0
    max_body_bytes: int = 1_048_576

    @field_validator("mode")
    @classmethod
    def _normalize_mode(cls, value: str) -> str:
        mode = str(value)
        return "ws-reverse" if mode == "reverse-ws" else mode

    @field_validator("port", "max_size", "max_body_bytes")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("value must be greater than 0")
        return int(value)

    @field_validator(
        "reconnect_interval",
        "api_timeout",
        "ping_interval",
        "ping_timeout",
        "open_timeout",
        "read_timeout",
    )
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if float(value) <= 0:
            raise ValueError("value must be greater than 0")
        return float(value)

    @field_validator("origins", mode="before")
    @classmethod
    def _normalize_origins(cls, value: Any) -> list[str] | None:
        if value in (None, False):
            return None
        if not isinstance(value, list):
            raise TypeError("origins must be a list")
        return [str(item) for item in value]

    @model_validator(mode="after")
    def _validate_security(self) -> "OneBot11ConfigModel":
        if (
            self.mode in {"ws-reverse", "http"}
            and not self.access_token
            and not self.allow_insecure_no_token
        ):
            if not is_loopback_host(self.host):
                raise ValueError(
                    "access_token is required when binding OneBot11 on a non-loopback host"
                )
        return self


class WebhookConfigModel(BaseModel):
    """Validated ``[adapter.webhook]`` configuration."""

    model_config = ConfigDict(extra="forbid")

    host: str = "127.0.0.1"
    port: int = 8090
    path: str = "/webhook"
    platform: str = "webhook"
    access_token: str = ""
    allow_insecure_no_token: bool = False
    allow_query_token: bool = False
    signature_provider: str = "generic"
    signature_secret: str = ""
    signature_header: str = "x-iamai-signature"
    signature_prefix: str = "sha256="
    timestamp_header: str = "x-iamai-timestamp"
    timestamp_tolerance_seconds: int = 300
    response_format: str = "segments"
    http_timeout: float = 10.0
    read_timeout: float = 10.0
    max_body_bytes: int = 1_048_576
    allow_event_reply_url: bool = False
    reply_url_allowlist: list[str] = Field(default_factory=list)
    allow_private_reply_hosts: bool = False
    allowed_reply_schemes: list[str] = Field(default_factory=lambda: ["https"])

    @field_validator("port", "max_body_bytes", "timestamp_tolerance_seconds")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("value must be greater than 0")
        return int(value)

    @field_validator("http_timeout", "read_timeout")
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if float(value) <= 0:
            raise ValueError("value must be greater than 0")
        return float(value)

    @field_validator("reply_url_allowlist", "allowed_reply_schemes", mode="before")
    @classmethod
    def _normalize_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise TypeError("value must be a list")
        return [str(item) for item in value]

    @field_validator("signature_header", "timestamp_header")
    @classmethod
    def _normalize_header_name(cls, value: str) -> str:
        return str(value).strip().lower()

    @field_validator("signature_provider")
    @classmethod
    def _normalize_signature_provider(cls, value: str) -> str:
        normalized = str(value).strip().lower() or "generic"
        if normalized not in SUPPORTED_SIGNATURE_PROVIDERS:
            allowed = ", ".join(SUPPORTED_SIGNATURE_PROVIDERS)
            raise ValueError(f"signature_provider must be one of: {allowed}")
        return normalized

    @model_validator(mode="after")
    def _validate_security(self) -> "WebhookConfigModel":
        if (
            not self.access_token
            and not self.allow_insecure_no_token
            and not is_loopback_host(self.host)
        ):
            raise ValueError("access_token is required when binding Webhook on a non-loopback host")
        if self.signature_secret and not self.signature_header:
            raise ValueError("signature_header is required when signature_secret is configured")
        return self


class TelegramConfigModel(BaseModel):
    """Validated ``[adapter.telegram]`` configuration."""

    model_config = ConfigDict(extra="forbid")

    token: str = ""
    api_base_url: str = "https://api.telegram.org"
    platform: str = "telegram"
    poll_timeout: int = 30
    request_timeout: float = 40.0
    reconnect_interval: float = 3.0
    limit: int = 100
    offset: int | None = None
    allowed_updates: list[str] = Field(default_factory=lambda: ["message"])

    @field_validator("poll_timeout", "limit")
    @classmethod
    def _positive_int(cls, value: int) -> int:
        if int(value) <= 0:
            raise ValueError("value must be greater than 0")
        return int(value)

    @field_validator("request_timeout", "reconnect_interval")
    @classmethod
    def _positive_float(cls, value: float) -> float:
        if float(value) <= 0:
            raise ValueError("value must be greater than 0")
        return float(value)

    @field_validator("allowed_updates", mode="before")
    @classmethod
    def _normalize_allowed_updates(cls, value: Any) -> list[str]:
        if value is None:
            return ["message"]
        if not isinstance(value, list):
            raise TypeError("allowed_updates must be a list")
        return [str(item) for item in value]


class StateConfigModel(BaseModel):
    """Validated persistent state backend configuration."""

    model_config = ConfigDict(extra="forbid")

    backend: str = "memory"
    path: str = ".iamai/state.json"


def load_config(path: str | Path) -> dict[str, Any]:
    """Load, validate, and annotate a TOML config file."""
    config_path = Path(path).expanduser().resolve()
    _load_env_files(config_path.parent)
    data = tomli.loads(config_path.read_text(encoding="utf-8"))
    validated = _validate_root_config(data)
    warnings = _collect_warnings(validated)
    validated["__meta__"] = {
        "config_path": str(config_path),
        "root_dir": str(config_path.parent),
        "warnings": warnings,
    }
    return validated


def load_env_file(path: str | Path, *, override: bool = False) -> None:
    """Load simple KEY=VALUE pairs from one dotenv file into ``os.environ``."""
    env_path = Path(path).expanduser()
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or (not override and key in os.environ):
            continue
        os.environ[key] = _parse_env_value(value.strip())


def merge_config(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two config dictionaries."""
    return merge_dicts(base, overlay)


def redact_config_value(value: Any) -> Any:
    """Return a copy of a config value with secret-like fields redacted."""
    if isinstance(value, dict):
        return {str(key): _redact_pair(str(key), item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_config_value(item) for item in value]
    return value


def _load_env_files(config_dir: Path) -> None:
    """Load project and config-local dotenv files without overriding process env."""
    candidates = [Path.cwd() / ".env", config_dir / ".env"]
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        load_env_file(resolved)


def _parse_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.encode("utf-8").decode("unicode_escape") if "\\" in value else value


def _redact_pair(key: str, value: Any) -> Any:
    lowered = key.lower()
    if any(marker in lowered for marker in SENSITIVE_KEY_MARKERS):
        if value in ("", None):
            return ""
        return "***"
    return redact_config_value(value)


def _validate_root_config(raw: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(raw)
    if not isinstance(data, dict):
        raise ConfigValidationError("config root must be a TOML table")

    try:
        runtime_data = RuntimeConfigModel.model_validate(data.get("runtime", {})).model_dump(
            mode="python"
        )
        logging_raw = data.get("logging", {})
        if logging_raw is None:
            logging_raw = {}
        if not isinstance(logging_raw, dict):
            raise TypeError("logging section must be a table")
        logging_data = LoggingConfigModel.model_validate(
            {"level": runtime_data.get("log_level", "INFO"), **logging_raw}
        ).model_dump(mode="python")
        adapter_data = _validate_adapter_config(data.get("adapter", {}))
        plugin_data = data.get("plugin", {})
        if not isinstance(plugin_data, dict):
            raise TypeError("plugin section must be a table")
        state_data = _validate_state_config(data.get("state", {}))
    except ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc
    except Exception as exc:
        raise ConfigValidationError(str(exc)) from exc

    data["runtime"] = runtime_data
    data["logging"] = logging_data
    data["adapter"] = adapter_data
    data["plugin"] = plugin_data
    data["state"] = state_data
    return data


def _validate_adapter_config(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise TypeError("adapter section must be a table")

    data = copy.deepcopy(raw)
    if "onebot11" in data:
        data["onebot11"] = OneBot11ConfigModel.model_validate(data["onebot11"]).model_dump(
            mode="python"
        )
    if "webhook" in data:
        data["webhook"] = WebhookConfigModel.model_validate(data["webhook"]).model_dump(
            mode="python"
        )
    if "telegram" in data:
        data["telegram"] = TelegramConfigModel.model_validate(data["telegram"]).model_dump(
            mode="python"
        )
    return data


def _validate_state_config(raw: Any) -> dict[str, Any] | bool:
    if raw is False:
        return False
    if raw in (None, {}):
        return {}
    if not isinstance(raw, dict):
        raise TypeError("state section must be a table or false")
    return StateConfigModel.model_validate(raw).model_dump(mode="python")


def _collect_warnings(config: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    runtime = config.get("runtime", {})
    adapters = config.get("adapter", {})
    plugin = config.get("plugin", {})
    hot_reload = runtime.get("hot_reload", False)
    hot_reload_enabled = (
        bool(hot_reload.get("enabled", True)) if isinstance(hot_reload, dict) else bool(hot_reload)
    )

    if hot_reload_enabled and any(
        section.get("host") and not is_loopback_host(str(section.get("host")))
        for section in (adapters.get("onebot11", {}), adapters.get("webhook", {}))
        if isinstance(section, dict)
    ):
        warnings.append("hot reload is enabled on a non-loopback network adapter")

    if runtime.get("allow_external_paths"):
        warnings.append("runtime.allow_external_paths is enabled")

    management = plugin.get("management", {})
    if isinstance(management, dict):
        if management.get("allow_reload") and not runtime.get("superusers"):
            warnings.append("management reload is enabled but runtime.superusers is empty")
        if management.get("allow_reload") and not management.get("reload_requires_superuser", True):
            warnings.append("management reload is enabled without requiring a superuser")
        if management.get("allow_introspection") and not runtime.get("superusers"):
            warnings.append("management introspection is enabled but runtime.superusers is empty")
        if management.get("allow_introspection") and not management.get(
            "introspection_requires_superuser", True
        ):
            warnings.append("management introspection is enabled without requiring a superuser")

    management_api = plugin.get("management_api", {})
    if isinstance(management_api, dict) and management_api.get("host"):
        if not is_loopback_host(str(management_api.get("host"))):
            warnings.append("management_api is exposed on a non-loopback host")

    onebot11 = adapters.get("onebot11", {})
    if isinstance(onebot11, dict) and onebot11.get("allow_query_token"):
        warnings.append("onebot11 allow_query_token is enabled")

    webhook = adapters.get("webhook", {})
    if isinstance(webhook, dict):
        if webhook.get("allow_query_token"):
            warnings.append("webhook allow_query_token is enabled")
        if (
            webhook.get("host")
            and not is_loopback_host(str(webhook.get("host")))
            and not webhook.get("signature_secret")
        ):
            warnings.append("webhook is exposed on a non-loopback host without signature_secret")
        if webhook.get("allow_event_reply_url") and not webhook.get("reply_url_allowlist"):
            warnings.append(
                "webhook allow_event_reply_url is enabled without a reply_url_allowlist"
            )

    return warnings
