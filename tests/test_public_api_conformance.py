from __future__ import annotations

import ast
import csv
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs/reference/public-api-conformance.csv"
NORMATIVE_DOCUMENTS = (
    "docs/reference/serialization-contract.rst",
    "docs/reference/public-api-lifecycle.rst",
    "docs/reference/extensions.rst",
    "docs/reference/public-api-conformance.rst",
    "docs/reference/deprecation-policy.rst",
    "docs/guides/migration-0.3-to-1.0.rst",
)
REQUIREMENT_PATTERN = re.compile(
    r"\b(?:SER|LIF|CTX|EXT|CFG|API|DEP|MIG|RC)-[A-Z]+-\d{3}\b"
)
REQUIRED_EXTENSION_REQUIREMENTS = {
    "EXT-ADAPTER-001",
    "EXT-ADAPTERCONFIG-001",
    "EXT-EVENT-001",
    "EXT-OUTBOUND-001",
    "EXT-ERROR-001",
    "EXT-LIFECYCLE-001",
    "EXT-PLUGIN-001",
    "EXT-PLUGINCONFIG-001",
    "EXT-DEPENDENCY-001",
    "EXT-HANDLER-001",
    "EXT-PERMISSION-001",
    "EXT-PLUGINLIFECYCLE-001",
}
REQUIRED_VERIFICATION_NODES = {
    "SER-ERROR-001": {
        "tests/test_serialization_contract.py::test_invalid_payload_goldens_have_stable_codes_and_paths",
        "tests/test_serialization_contract.py::test_json_reader_rejects_non_object_malformed_duplicate_and_nonfinite_json",
        "tests/test_serialization_contract.py::test_json_reader_rejects_fractional_numbers_outside_binary64_contract",
        "tests/test_serialization_contract.py::test_json_reader_rejects_oversized_number_literals_before_conversion",
        "tests/test_serialization_contract.py::test_integer_contract_accepts_4096_digit_boundary",
        "tests/test_serialization_contract.py::test_mapping_reader_and_writer_reject_integers_over_4096_digits",
        "tests/test_serialization_contract.py::test_python_payload_and_writer_reject_nonfinite_numbers",
        "tests/test_serialization_contract.py::test_python_event_payload_rejects_non_json_raw_values",
        "tests/test_serialization_contract.py::test_python_payload_reader_and_writer_reject_cycles",
        "tests/test_serialization_contract.py::test_readers_reject_excessive_nesting_with_stable_error",
        "tests/test_serialization_contract.py::test_event_writer_rejects_invalid_message_state_with_stable_error",
        "tests/test_serialization_contract.py::test_event_required_strings_must_be_present_and_non_empty",
    },
    "EXT-DISCOVERY-001": {
        "tests/test_installed_extensions.py::test_installed_entry_points_support_explicit_and_opt_in_auto_discovery",
        "tests/test_package_discovery.py::test_plugin_entry_point_name_can_be_loaded_explicitly",
        "tests/test_package_discovery.py::test_dotted_plugin_entry_point_survives_hot_reload",
        "tests/test_package_discovery.py::test_auto_discover_plugins_loads_entry_points_and_honors_dependencies",
        "tests/test_package_discovery.py::test_adapter_entry_point_name_can_be_loaded_explicitly",
        "tests/test_package_discovery.py::test_auto_discover_adapters_loads_entry_points",
        "tests/test_package_discovery.py::test_duplicate_entry_points_report_every_distribution_in_sorted_order",
        "tests/test_package_discovery.py::test_plugin_entry_point_cannot_shadow_builtin_name",
        "tests/test_package_discovery.py::test_adapter_entry_point_cannot_shadow_builtin_name",
        "tests/test_package_discovery.py::test_plugin_entry_point_rejects_non_plugin_object",
        "tests/test_package_discovery.py::test_adapter_entry_point_rejects_non_adapter_object",
        "tests/test_package_discovery.py::test_plugin_entry_point_name_must_match_plugin_name",
        "tests/test_package_discovery.py::test_adapter_entry_point_name_must_match_adapter_name",
        "tests/test_package_discovery.py::test_entry_point_load_failure_preserves_original_cause",
        "tests/test_package_discovery.py::test_auto_discovery_order_is_deterministic_across_groups",
        "tests/test_package_discovery.py::test_auto_discovery_appends_sorted_entries_without_reordering_explicit_references",
        "tests/test_package_discovery.py::test_explicit_loading_ignores_unrequested_broken_entry_points",
        "tests/test_package_discovery.py::test_auto_discovery_reports_first_error_in_entry_point_name_order",
    },
    "CFG-SCHEMA-001": {
        "tests/test_config_schema.py::test_root_schema_matches_versioned_contract_golden",
        "tests/test_config_schema.py::test_extension_schemas_are_sorted_stable_and_open_to_unknown_tables",
        "tests/test_config_schema.py::test_pydantic_and_dataclass_config_models_are_supported",
        "tests/test_config_schema.py::test_schema_generation_does_not_execute_default_factories",
        "tests/test_config_schema.py::test_core_defaults_and_false_state_are_explicit",
        "tests/test_config_schema.py::test_write_only_is_explicit_and_not_inferred_from_field_names",
        "tests/test_config_schema.py::test_builtin_extension_secret_annotations_and_defaults_are_visible",
        "tests/test_config_schema.py::test_runtime_schema_uses_metadata_only_and_never_leaks_configured_secrets",
        "tests/test_adapter_config_contract.py::test_builtin_adapter_secret_fields_are_explicitly_write_only",
        "tests/test_adapter_config_contract.py::test_builtin_adapter_factory_defaults_are_static_in_schema",
        "tests/test_installed_extensions.py::test_installed_entry_points_support_explicit_and_opt_in_auto_discovery",
    },
    "CFG-EQUIVALENCE-001": {
        "tests/test_config_schema.py::test_root_schema_matches_versioned_contract_golden",
        "tests/test_config_schema.py::test_build_config_schema_exactly_matches_runtime_schema_for_loaded_extensions",
        "tests/test_config_schema.py::test_no_argument_cli_schema_exactly_matches_runtime_schema",
        "tests/test_config_schema.py::test_cli_schema_applies_configured_python_paths",
        "tests/test_config_schema.py::test_cli_plugin_selector_remains_backward_compatible",
        "tests/test_config_schema.py::test_cli_plugin_selector_applies_configured_python_paths",
        "tests/test_management_api.py::test_management_api_exposes_read_only_runtime_payloads",
    },
}


def _normative_requirement_ids() -> set[str]:
    return {
        requirement_id
        for path in NORMATIVE_DOCUMENTS
        for requirement_id in REQUIREMENT_PATTERN.findall(
            (ROOT / path).read_text(encoding="utf-8")
        )
    }


def _pytest_node_exists(node_id: str) -> bool:
    parts = node_id.split("::")
    if len(parts) != 2 or not parts[0].startswith("tests/"):
        return False
    path = ROOT / parts[0]
    if not path.is_file() or path.suffix != ".py":
        return False
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == parts[1]
        for node in tree.body
    )


def _pytest_nodes(verification: str) -> list[str]:
    return [node_id.strip() for node_id in verification.split(";") if node_id.strip()]


def test_public_api_conformance_matrix_is_complete() -> None:
    with MATRIX_PATH.open(encoding="utf-8", newline="") as matrix_file:
        reader = csv.DictReader(matrix_file)
        assert reader.fieldnames == [
            "requirement_id",
            "scope",
            "source",
            "verification",
            "mode",
            "status",
        ]
        rows = list(reader)

    assert rows
    requirement_ids = [row["requirement_id"] for row in rows]
    assert len(requirement_ids) == len(set(requirement_ids))
    assert set(requirement_ids) == _normative_requirement_ids()
    assert REQUIRED_EXTENSION_REQUIREMENTS <= set(requirement_ids)

    for row in rows:
        requirement_id = row["requirement_id"]
        assert all(row.values()), requirement_id
        source_path, source_anchor = row["source"].split("#", 1)
        assert source_path in NORMATIVE_DOCUMENTS, requirement_id
        assert source_anchor == requirement_id.lower(), requirement_id
        source = (ROOT / source_path).read_text(encoding="utf-8")
        assert f".. _{source_anchor}:" in source, requirement_id
        assert requirement_id in source

        if row["mode"] == "automated":
            assert row["status"] == "verified", requirement_id
            node_ids = _pytest_nodes(row["verification"])
            assert node_ids, requirement_id
            assert len(node_ids) == len(set(node_ids)), requirement_id
            assert all(
                re.fullmatch(r"tests/.+\.py::test_[A-Za-z0-9_]+", node_id)
                for node_id in node_ids
            ), requirement_id
            required_node_ids = REQUIRED_VERIFICATION_NODES.get(requirement_id, set())
            assert required_node_ids <= set(node_ids), (
                requirement_id,
                sorted(required_node_ids - set(node_ids)),
            )
            missing_node_ids = [
                node_id for node_id in node_ids if not _pytest_node_exists(node_id)
            ]
            assert not missing_node_ids, (requirement_id, missing_node_ids)
            continue

        assert row["mode"] == "manual", requirement_id
        assert requirement_id == "RC-VALIDATE-001"
        evidence = row["verification"]
        for required_text in (
            "release.yml",
            "workflow_dispatch",
            "1.0.0rc1",
            "validate",
            "wheels",
            "sdist",
            "artifact",
            "attestation",
        ):
            assert required_text in evidence, required_text
        assert row["status"] == "external-required"
        assert "record run URL and headSha externally" in evidence
        assert "https://github.com/retrofor/iamai/issues/434" in evidence
