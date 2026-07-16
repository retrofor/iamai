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
        source_path = row["source"].split("#", 1)[0]
        assert source_path in NORMATIVE_DOCUMENTS, requirement_id
        assert requirement_id in (ROOT / source_path).read_text(encoding="utf-8")

        if row["mode"] == "automated":
            assert row["status"] == "verified", requirement_id
            node_ids = _pytest_nodes(row["verification"])
            assert node_ids, requirement_id
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
