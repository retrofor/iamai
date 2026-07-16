from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

from iamai import (
    SERIALIZATION_CONTRACT_VERSION,
    Event,
    Message,
    SerializationContractError,
)

GOLDEN_ROOT = Path(__file__).parent / "golden" / "serialization" / "v1"


def _golden(name: str) -> Any:
    return json.loads((GOLDEN_ROOT / name).read_text(encoding="utf-8"))


def _canonical(payload: Any) -> str:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_serialization_contract_version_is_public() -> None:
    assert SERIALIZATION_CONTRACT_VERSION == "1.0"


def test_message_valid_golden_round_trip_is_lossless_and_canonical() -> None:
    golden = _golden("message-valid.json")

    message = Message.from_payload(golden)

    assert message.to_payload() == golden
    assert message.to_json() == _canonical(golden)
    assert Message.from_json(message.to_json()).to_payload() == golden


def test_event_valid_golden_round_trip_is_lossless_and_canonical() -> None:
    golden = _golden("event-valid.json")

    event = Event.from_payload(golden)

    assert event.to_payload() == golden
    assert event.to_json() == _canonical(golden)
    assert Event.from_json(event.to_json()).to_payload() == golden


def test_minimal_event_defaults_are_emitted_in_canonical_form() -> None:
    golden = _golden("event-minimal-valid.json")
    minimal = {
        field: golden[field]
        for field in ("contract_version", "id", "adapter", "platform", "type", "message")
    }

    event = Event.from_payload(minimal)

    assert event.to_payload() == golden
    assert event.to_json() == _canonical(golden)


def test_same_major_readers_accept_additive_fields_and_emit_current_minor() -> None:
    event_payload = _golden("event-valid.json")
    event_payload["contract_version"] = "1.99"
    event_payload["future_event_field"] = {"kept_by_sender": True}
    event_payload["message"]["contract_version"] = "1.7"
    event_payload["message"]["future_message_field"] = [1, 2, 3]
    event_payload["message"]["segments"][0]["future_segment_field"] = "ignored"

    normalized = Event.from_payload(event_payload).to_payload()

    assert normalized["contract_version"] == SERIALIZATION_CONTRACT_VERSION
    assert normalized["message"]["contract_version"] == SERIALIZATION_CONTRACT_VERSION
    assert "future_event_field" not in normalized
    assert "future_message_field" not in normalized["message"]
    assert "future_segment_field" not in normalized["message"]["segments"][0]


@pytest.mark.parametrize("case", _golden("invalid-cases.json"), ids=lambda case: case["name"])
def test_invalid_payload_goldens_have_stable_codes_and_paths(case: dict[str, Any]) -> None:
    reader = Message.from_payload if case["target"] == "message" else Event.from_payload

    with pytest.raises(SerializationContractError) as caught:
        reader(case["payload"])

    assert caught.value.code == case["code"]
    assert caught.value.path == case["path"]
    assert str(caught.value).startswith(f"{case['code']} at {case['path']}:")


@pytest.mark.parametrize("reader", [Message.from_json, Event.from_json])
@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ("[]", "expected_object"),
        ('{"contract_version":"1.0",', "invalid_json"),
        ('{"contract_version":"1.0","contract_version":"1.1","segments":[]}', "duplicate_key"),
        ('{"contract_version":"1.0","segments":[],"future":NaN}', "invalid_number"),
    ],
)
def test_json_reader_rejects_non_object_malformed_duplicate_and_nonfinite_json(
    reader: Any,
    payload: str,
    code: str,
) -> None:
    with pytest.raises(SerializationContractError) as caught:
        reader(payload)

    assert caught.value.code == code
    assert caught.value.path == "$"


@pytest.mark.parametrize(
    "number",
    [
        "0.123456789012345678901234567890123456789",
        "1.000000000000000000000000000000000000001",
        "1e-400",
        "1e400",
    ],
)
def test_json_reader_rejects_fractional_numbers_outside_binary64_contract(
    number: str,
) -> None:
    payload = f'{{"contract_version":"1.0","segments":[{{"kind":"number","data":{{"value":{number}}}}}]}}'

    with pytest.raises(SerializationContractError) as caught:
        Message.from_json(payload)

    assert caught.value.code == "invalid_number"
    assert caught.value.path == "$"


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_python_payload_and_writer_reject_nonfinite_numbers(value: float) -> None:
    payload = _golden("message-valid.json")
    payload["segments"][1]["data"]["count"] = value

    with pytest.raises(SerializationContractError) as read_error:
        Message.from_payload(payload)
    assert read_error.value.code == "invalid_number"
    assert read_error.value.path == "$.segments[1].data.count"

    event = Event(
        id="event-001",
        adapter="reference",
        platform="test",
        type="message",
        raw={"value": value},
    )
    with pytest.raises(SerializationContractError) as write_error:
        event.to_json()
    assert write_error.value.code == "invalid_number"
    assert write_error.value.path == "$.raw.value"


def test_payload_readers_defensively_copy_mutable_json_values() -> None:
    event_payload = _golden("event-valid.json")
    event = Event.from_payload(event_payload)

    event_payload["raw"]["metadata"]["labels"].append("mutated")
    event_payload["message"]["segments"][1]["data"]["nested"]["items"].append("mutated")

    serialized = event.to_payload()
    assert serialized["raw"]["metadata"]["labels"] == ["alpha", None]
    assert serialized["message"]["segments"][1]["data"]["nested"]["items"] == [
        1,
        False,
        None,
    ]


@pytest.mark.parametrize(
    ("bad_value", "code", "path"),
    [
        ({1: "not a JSON key"}, "invalid_json_key", "$.raw"),
        ({"value": b"not JSON"}, "invalid_json_value", "$.raw.value"),
    ],
)
def test_python_event_payload_rejects_non_json_raw_values(
    bad_value: dict[Any, Any],
    code: str,
    path: str,
) -> None:
    payload = _golden("event-minimal-valid.json")
    payload["raw"] = bad_value

    with pytest.raises(SerializationContractError) as read_error:
        Event.from_payload(payload)
    assert read_error.value.code == code
    assert read_error.value.path == path

    event = Event(
        id="event-001",
        adapter="reference",
        platform="test",
        type="notice",
        raw=bad_value,
    )
    with pytest.raises(SerializationContractError) as write_error:
        event.to_payload()
    assert write_error.value.code == code
    assert write_error.value.path == path


def test_python_payload_reader_and_writer_reject_cycles() -> None:
    cycle: list[Any] = []
    cycle.append(cycle)
    payload = _golden("message-valid.json")
    payload["segments"][1]["data"]["cycle"] = cycle

    with pytest.raises(SerializationContractError) as read_error:
        Message.from_payload(payload)
    assert read_error.value.code == "cyclic_value"
    assert read_error.value.path == "$.segments[1].data.cycle[0]"

    event = Event(
        id="event-001",
        adapter="reference",
        platform="test",
        type="notice",
        raw={"cycle": cycle},
    )
    with pytest.raises(SerializationContractError) as write_error:
        event.to_payload()
    assert write_error.value.code == "cyclic_value"
    assert write_error.value.path == "$.raw.cycle[0]"


def test_readers_reject_excessive_nesting_with_stable_error() -> None:
    nested: list[Any] = []
    for _ in range(101):
        nested = [nested]
    payload = _golden("message-valid.json")
    payload["segments"][1]["data"]["nested"] = nested

    with pytest.raises(SerializationContractError) as payload_error:
        Message.from_payload(payload)
    assert payload_error.value.code == "nesting_too_deep"

    json_payload = '{"contract_version":"1.0","segments":' + "[" * 1500 + "]" * 1500 + "}"
    with pytest.raises(SerializationContractError) as json_error:
        Message.from_json(json_payload)
    assert json_error.value.code == "nesting_too_deep"
    assert json_error.value.path == "$"


def test_event_writer_rejects_invalid_message_state_with_stable_error() -> None:
    event = Event(
        id="event-001",
        adapter="reference",
        platform="test",
        type="message",
        message="not-a-message",  # type: ignore[arg-type]
    )

    with pytest.raises(SerializationContractError) as caught:
        event.to_payload()
    assert caught.value.code == "invalid_message"
    assert caught.value.path == "$.message"


def test_onebot_legacy_data_remains_string_normalized() -> None:
    message = Message.from_onebot11(
        [{"type": "at", "data": {"qq": 42, "enabled": True, "missing": None}}]
    )

    assert message.segments == [
        {
            "kind": "at",
            "data": {"qq": "42", "enabled": "true", "missing": ""},
        }
    ]
    assert message.to_onebot11() == [
        {
            "type": "at",
            "data": {"qq": "42", "enabled": "true", "missing": ""},
        }
    ]


def test_json_readers_accept_utf8_bytes() -> None:
    golden = _golden("message-valid.json")

    assert Message.from_json(_canonical(golden).encode("utf-8")).to_payload() == golden


def test_legacy_event_and_message_serializers_remain_unversioned() -> None:
    event = Event(
        id="legacy-1",
        adapter="reference",
        platform="test",
        type="message",
        message=Message("hello"),
    )

    legacy = event.to_dict()

    assert "contract_version" not in legacy
    assert isinstance(legacy["message"], list)
    assert Event.from_dict(legacy).to_dict() == legacy


@pytest.mark.parametrize("field", ["id", "adapter", "platform", "type"])
def test_event_required_strings_must_be_present_and_non_empty(field: str) -> None:
    missing = _golden("event-minimal-valid.json")
    missing.pop(field)
    with pytest.raises(SerializationContractError) as missing_error:
        Event.from_payload(missing)
    assert missing_error.value.code == "missing_field"
    assert missing_error.value.path == f"$.{field}"

    empty = _golden("event-minimal-valid.json")
    empty[field] = ""
    with pytest.raises(SerializationContractError) as empty_error:
        Event.from_payload(empty)
    assert empty_error.value.code == "empty_string"
    assert empty_error.value.path == f"$.{field}"
