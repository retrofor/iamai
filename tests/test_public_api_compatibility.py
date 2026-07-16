from __future__ import annotations

import inspect
import json
import warnings
from pathlib import Path
from typing import Any

import iamai
import iamai.runtime as runtime_module
import iamai.testing
import pytest
from iamai import (
    ADAPTER_ENTRY_POINT_GROUP,
    IamaiDeprecationWarning,
    PLUGIN_ENTRY_POINT_GROUP,
    PUBLIC_API_CONTRACT_VERSION,
)
from iamai.contract import _warn_deprecated

MANIFEST_PATH = Path(__file__).parent / "golden" / "public_api_v1.json"


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_public_api_contract_version_and_entry_point_groups_are_public() -> None:
    manifest = _manifest()

    assert PUBLIC_API_CONTRACT_VERSION == "1"
    assert ADAPTER_ENTRY_POINT_GROUP == "iamai.adapters"
    assert PLUGIN_ENTRY_POINT_GROUP == "iamai.plugins"
    assert runtime_module.ADAPTER_ENTRY_POINT_GROUP is ADAPTER_ENTRY_POINT_GROUP
    assert runtime_module.PLUGIN_ENTRY_POINT_GROUP is PLUGIN_ENTRY_POINT_GROUP
    assert manifest["contract_versions"] == {
        "config_schema": iamai.CONFIG_SCHEMA_CONTRACT_VERSION,
        "public_api": PUBLIC_API_CONTRACT_VERSION,
        "serialization": iamai.SERIALIZATION_CONTRACT_VERSION,
    }
    assert manifest["entry_point_groups"] == {
        "adapters": ADAPTER_ENTRY_POINT_GROUP,
        "plugins": PLUGIN_ENTRY_POINT_GROUP,
    }


def test_v1_public_api_matches_golden_manifest() -> None:
    manifest = _manifest()
    stable_names = manifest["top_level"]["stable"]
    provisional_names = manifest["top_level"]["provisional"]
    assert stable_names == sorted(set(stable_names))
    assert provisional_names == sorted(set(provisional_names))
    stable = set(stable_names)
    provisional = set(provisional_names)
    exported = set(iamai.__all__)

    assert stable.isdisjoint(provisional)
    assert stable <= exported
    assert stable | provisional == exported
    assert len(iamai.__all__) == len(exported)
    for name in stable | provisional:
        assert getattr(iamai, name) is not None

    testing_stable_names = manifest["testing"]["stable"]
    testing_provisional_names = manifest["testing"]["provisional"]
    assert testing_stable_names == sorted(set(testing_stable_names))
    assert testing_provisional_names == sorted(set(testing_provisional_names))
    testing_stable = set(testing_stable_names)
    testing_provisional = set(testing_provisional_names)
    testing_exported = set(iamai.testing.__all__)
    assert testing_provisional == set()
    assert testing_stable == testing_exported
    assert len(iamai.testing.__all__) == len(testing_exported)
    for name in testing_stable:
        assert getattr(iamai.testing, name) is not None


def test_deprecation_warning_exposes_stable_metadata() -> None:
    warning = IamaiDeprecationWarning(
        code="IAMAI-D001",
        kind="symbol",
        subject="iamai.old_name",
        since="1.0",
        remove_in="2.0",
        replacement="iamai.new_name",
    )

    assert isinstance(warning, FutureWarning)
    assert warning.code == "IAMAI-D001"
    assert warning.kind == "symbol"
    assert warning.subject == "iamai.old_name"
    assert warning.since == "1.0"
    assert warning.remove_in == "2.0"
    assert warning.replacement == "iamai.new_name"
    assert str(warning) == (
        "iamai deprecation: code=IAMAI-D001; kind=symbol; subject=iamai.old_name; "
        "since=1.0; remove_in=2.0; replacement=iamai.new_name"
    )

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("default")
        warnings.warn(warning)

    assert len(captured) == 1
    assert captured[0].category is IamaiDeprecationWarning
    assert captured[0].message is warning


@pytest.mark.parametrize("kind", ["", "config", "serialized-field"])
def test_deprecation_warning_rejects_unknown_kind(kind: str) -> None:
    with pytest.raises(ValueError, match="kind must be one of"):
        IamaiDeprecationWarning(
            code="IAMAI-D003",
            kind=kind,  # type: ignore[arg-type]
            subject="iamai.old_name",
            since="1.0",
            remove_in="2.0",
        )


@pytest.mark.parametrize("field", ["code", "subject", "since", "remove_in"])
@pytest.mark.parametrize("value", ["", "  ", " padded"])
def test_deprecation_warning_rejects_invalid_required_metadata(
    field: str,
    value: str,
) -> None:
    metadata = {
        "code": "IAMAI-D003",
        "subject": "iamai.old_name",
        "since": "1.0",
        "remove_in": "2.0",
    }
    metadata[field] = value

    with pytest.raises(ValueError, match=field):
        IamaiDeprecationWarning(kind="symbol", **metadata)


@pytest.mark.parametrize("replacement", ["", "  ", " padded"])
def test_deprecation_warning_rejects_invalid_replacement(replacement: str) -> None:
    with pytest.raises(ValueError, match="replacement"):
        IamaiDeprecationWarning(
            code="IAMAI-D003",
            kind="symbol",
            subject="iamai.old_name",
            since="1.0",
            remove_in="2.0",
            replacement=replacement,
        )


def _emit_deprecation_from_wrapper() -> None:
    _warn_deprecated(
        code="IAMAI-D002",
        kind="config_key",
        subject="runtime.old_key",
        since="1.0",
        remove_in="2.0",
        replacement=None,
        stacklevel=2,
    )


def test_deprecation_helper_honors_caller_stacklevel() -> None:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        frame = inspect.currentframe()
        assert frame is not None
        expected_line = frame.f_lineno + 1
        _emit_deprecation_from_wrapper()

    assert len(captured) == 1
    assert captured[0].filename == __file__
    assert captured[0].lineno == expected_line
    assert captured[0].message.replacement is None
    assert str(captured[0].message).endswith("replacement=none")
