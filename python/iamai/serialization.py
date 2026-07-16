"""Shared primitives for the public Event and Message serialization contract."""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
import json
import math
import re
from typing import Any, NoReturn

SERIALIZATION_CONTRACT_VERSION = "1.0"

_CONTRACT_VERSION_PATTERN = re.compile(r"^(?P<major>0|[1-9][0-9]*)\.(?P<minor>0|[1-9][0-9]*)$")
_SUPPORTED_CONTRACT_MAJOR = SERIALIZATION_CONTRACT_VERSION.partition(".")[0]
_MAX_JSON_NESTING = 100


class SerializationContractError(ValueError):
    """Stable validation error raised by the public serialization contract."""

    def __init__(self, code: str, path: str, message: str | None = None) -> None:
        self.code = code
        self.path = path
        detail = message or "serialization contract validation failed"
        super().__init__(f"{code} at {path}: {detail}")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    _validate_json_value(payload, path="$")
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except RecursionError as error:
        raise SerializationContractError("nesting_too_deep", "$", str(error)) from error
    except (TypeError, ValueError) as error:
        raise SerializationContractError("invalid_json_value", "$", str(error)) from error


def _load_json_object(payload: str | bytes | bytearray) -> dict[str, Any]:
    def reject_constant(value: str) -> NoReturn:
        raise SerializationContractError(
            "invalid_number",
            "$",
            f"JSON number {value!r} is not finite",
        )

    def parse_binary64(value: str) -> float:
        decimal_value = Decimal(value)
        digits = list(decimal_value.as_tuple().digits)
        while digits and digits[-1] == 0:
            digits.pop()
        if len(digits) > 17:
            raise SerializationContractError(
                "invalid_number",
                "$",
                "fractional JSON numbers support at most 17 significant digits",
            )
        parsed = float(value)
        if not math.isfinite(parsed) or (parsed == 0.0 and decimal_value != 0):
            raise SerializationContractError(
                "invalid_number",
                "$",
                "fractional JSON number is outside the finite binary64 range",
            )
        return parsed

    def reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise SerializationContractError(
                    "duplicate_key",
                    "$",
                    f"JSON object contains duplicate key {key!r}",
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            payload,
            object_pairs_hook=reject_duplicate,
            parse_constant=reject_constant,
            parse_float=parse_binary64,
        )
    except SerializationContractError:
        raise
    except RecursionError as error:
        raise SerializationContractError("nesting_too_deep", "$", str(error)) from error
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as error:
        raise SerializationContractError("invalid_json", "$", str(error)) from error

    if not isinstance(value, dict):
        raise SerializationContractError(
            "expected_object",
            "$",
            "serialized payload must be a JSON object",
        )
    _validate_json_value(value, path="$")
    return value


def _require_object(value: Any, *, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SerializationContractError("expected_object", path, "value must be an object")
    for key in value:
        if not isinstance(key, str):
            raise SerializationContractError(
                "invalid_json_key",
                path,
                "object keys must be strings",
            )
    return value


def _require_array(value: Any, *, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise SerializationContractError("expected_array", path, "value must be an array")
    return value


def _require_field(payload: Mapping[str, Any], field: str, *, path: str) -> Any:
    if field not in payload:
        raise SerializationContractError(
            "missing_field",
            _child_path(path, field),
            f"required field {field!r} is missing",
        )
    return payload[field]


def _require_string(value: Any, *, path: str, non_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise SerializationContractError("expected_string", path, "value must be a string")
    if non_empty and not value:
        raise SerializationContractError("empty_string", path, "value must not be empty")
    return value


def _require_optional_string(value: Any, *, path: str) -> str | None:
    if value is None:
        return None
    return _require_string(value, path=path)


def _require_contract_version(payload: Mapping[str, Any], *, path: str) -> str:
    version_path = _child_path(path, "contract_version")
    version = _require_string(
        _require_field(payload, "contract_version", path=path),
        path=version_path,
        non_empty=True,
    )
    match = _CONTRACT_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise SerializationContractError(
            "invalid_contract_version",
            version_path,
            "contract version must use '<major>.<minor>' syntax",
        )
    if match.group("major") != _SUPPORTED_CONTRACT_MAJOR:
        raise SerializationContractError(
            "unsupported_contract_version",
            version_path,
            f"supported contract major is {_SUPPORTED_CONTRACT_MAJOR}",
        )
    return version


def _copy_json_value(value: Any, *, path: str) -> Any:
    _validate_json_value(value, path=path)
    if isinstance(value, Mapping):
        return {
            key: _copy_json_value(item, path=_child_path(path, key))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _copy_json_value(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    return value


def _validate_json_value(
    value: Any,
    *,
    path: str,
    active: set[int] | None = None,
    depth: int = 0,
) -> None:
    if depth > _MAX_JSON_NESTING:
        raise SerializationContractError(
            "nesting_too_deep",
            path,
            f"JSON nesting exceeds {_MAX_JSON_NESTING} levels",
        )
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SerializationContractError(
                "invalid_number",
                path,
                "JSON numbers must be finite",
            )
        return

    if active is None:
        active = set()
    if isinstance(value, Mapping):
        marker = id(value)
        if marker in active:
            raise SerializationContractError("cyclic_value", path, "JSON value contains a cycle")
        active.add(marker)
        try:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise SerializationContractError(
                        "invalid_json_key",
                        path,
                        "object keys must be strings",
                    )
                _validate_json_value(
                    item,
                    path=_child_path(path, key),
                    active=active,
                    depth=depth + 1,
                )
        finally:
            active.remove(marker)
        return
    if isinstance(value, list):
        marker = id(value)
        if marker in active:
            raise SerializationContractError("cyclic_value", path, "JSON value contains a cycle")
        active.add(marker)
        try:
            for index, item in enumerate(value):
                _validate_json_value(
                    item,
                    path=f"{path}[{index}]",
                    active=active,
                    depth=depth + 1,
                )
        finally:
            active.remove(marker)
        return

    raise SerializationContractError(
        "invalid_json_value",
        path,
        f"value of type {type(value).__name__!r} is not JSON-compatible",
    )


def _child_path(path: str, field: str) -> str:
    if field.isidentifier():
        return f"{path}.{field}"
    encoded = json.dumps(field, ensure_ascii=False)
    return f"{path}[{encoded}]"
