from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_ecosystem_comparison_contains_matrix_and_roadmap_link() -> None:
    content = _read("docs/guides/ecosystem-comparison.rst")

    assert "能力矩阵" in content
    assert "NoneBot" in content
    assert "Hermes Agent" in content
    assert "iamai-table-scroll" in content
    assert "差距到实现" in content
    assert ":doc:`roadmap`" in content


def test_extensions_reference_contains_public_extension_specs() -> None:
    content = _read("docs/reference/extensions.rst")

    assert "适配器兼容性规范草案" in content
    assert '[project.entry-points."iamai.adapters"]' in content
    assert "Agent tool 必须额外声明" in content
    assert "/schema" in content
    assert "iamai.testing.adapters" in content
    assert "``assert_adapter_lifecycle``" in content
    assert "``assert_plugin_startup_failure_cleanup``" in content
    assert "先调用 ``close()``" in content
    assert "``iamai_requires``" in content
    assert "``conformance_evidence``" in content
    assert "``Requires-Dist``" in content


def test_fossa_governance_docs_preserve_permission_and_evidence_boundaries() -> None:
    baseline = _read("docs/reference/fossa-governance-baseline.rst")
    execution_spec = _read("docs/reference/post-v0.3-execution-spec.rst")
    todo = _read("TODO.md")

    assert "不得直接输出或先保存" in baseline
    assert "| jq '{locator, public, default_branch, tracking_branches," in baseline
    assert "``status=active``" in baseline
    assert "``status=ignored``" in baseline
    assert "过滤前后的 match inventory" in baseline
    assert "不能把 correction 的组织级权限要求套用到 dispute" in baseline
    assert "项目 View 权限" in execution_spec
    assert "项目 Edit 权限" in execution_spec
    assert "``SetPolicy``" in execution_spec
    assert "Push-Only token" in execution_spec
    assert "``Standard Bundle Distribution``" in execution_spec
    assert "source-license 字段" in execution_spec
    assert "active and ignored issue inventories" in todo
    assert "Blocking owner: retrofor FOSSA project/organization owners" in todo
    assert "At the release-candidate freeze" in todo
    assert "after every future implementation merge" not in todo


def test_serialization_reference_contains_v1_contract_rules() -> None:
    content = _read("docs/reference/serialization-contract.rst")

    assert "``SERIALIZATION_CONTRACT_VERSION``" in content
    assert '``contract_version`` 必须是 ``"1.0"``' in content
    assert "未知字段" in content
    assert "标准 JSON 类型" in content
    assert "IEEE-754 binary64" in content
    assert "``Event.to_payload()``" in content
    assert "``Event.from_payload()``" in content
    assert "同一 major" in content
    assert "legacy normalization" in content


def test_public_api_lifecycle_reference_contains_v1_normative_rules() -> None:
    content = _read("docs/reference/public-api-lifecycle.rst")
    index = _read("docs/reference/index.rst")
    execution_spec = _read("docs/reference/post-v0.3-execution-spec.rst")

    normative_ids = {
        "LIF-START-001",
        "LIF-START-002",
        "LIF-ADAPTER-001",
        "LIF-SHUTDOWN-001",
        "LIF-RELOAD-001",
        "LIF-RELOAD-002",
        "LIF-RELOAD-003",
        "LIF-RELOAD-004",
        "LIF-ORDER-001",
        "CTX-SCOPE-001",
        "CTX-ROUTE-001",
        "CTX-DI-001",
        "CTX-DI-002",
        "CTX-INVALID-001",
        "CTX-LIFECYCLE-001",
    }
    for normative_id in normative_ids:
        assert normative_id in content
    assert "原始异常" in content
    assert "handler_shutdown_timeout_seconds" in content
    assert "ContextInvalidatedError" in content
    assert "Depends(use_cache=False)" in content
    assert "Context 不拥有生命周期" in content
    assert "public-api-lifecycle" in index
    assert execution_spec.count(":doc:`public-api-lifecycle`") == 2


def test_v1_public_api_docs_cover_compatibility_policy_and_migration() -> None:
    conformance = _read("docs/reference/public-api-conformance.rst")
    deprecation = _read("docs/reference/deprecation-policy.rst")
    migration = _read("docs/guides/migration-0.3-to-1.0.rst")
    reference_index = _read("docs/reference/index.rst")
    guides_index = _read("docs/guides/index.rst")

    assert "public-api-conformance" in reference_index
    assert "deprecation-policy" in reference_index
    assert "migration-0.3-to-1.0" in guides_index

    assert "PUBLIC_API_CONTRACT_VERSION" in conformance
    assert "CONFIG_SCHEMA_CONTRACT_VERSION" in conformance
    assert "SERIALIZATION_CONTRACT_VERSION" in conformance
    assert "public-api-conformance.csv" in conformance
    assert "Stable at 1.0.0" in conformance
    assert "Provisional" in conformance
    assert "RC-VALIDATE-001" in conformance

    assert "IamaiDeprecationWarning" in deprecation
    assert "FutureWarning" in deprecation
    assert "两个后续 minor release" in deprecation
    assert "180 天" in deprecation
    assert "下一个" in deprecation
    assert "安全与法律例外" in deprecation

    assert "MIG-COVERAGE-001" in migration
    assert "v0.3.0" in migration
    assert "1.0.0rc1" in migration
    assert "Event.to_payload()" in migration
    assert "Requires-Dist" in migration
    assert "ExtensionDiscoveryError.code" in migration
    assert "ContextInvalidatedError" in migration
    assert "iamai.testing" in migration


def test_ecosystem_submission_surfaces_carry_admission_evidence_fields() -> None:
    browser = _read("docs/_static/iamai-store.js")
    issue_template = _read(".github/ISSUE_TEMPLATE/ecosystem-submission.yml")
    tutorial = _read("docs/tutorials/part-6-ecosystem-publishing.rst")

    assert 'field("iamai_requires"' in browser
    assert 'textarea("conformance_evidence"' in browser
    assert 'conformance_evidence: splitLines(data.get("conformance_evidence"))' in browser
    assert "isPublicHttpUrl(url)" in browser
    assert "id: iamai_requires" in issue_template
    assert "id: conformance_evidence" in issue_template
    iamai_section = issue_template.split("id: iamai_requires", 1)[1].split("- type:", 1)[0]
    evidence_section = issue_template.split("id: conformance_evidence", 1)[1].split("- type:", 1)[0]
    assert "required: true" in iamai_section
    assert "required: true" in evidence_section
    assert "``iamai_requires``" in tutorial
    assert "``conformance_evidence``" in tutorial
    assert "iamai>=1,<2" in tutorial
    assert "iamai>=1,<2" in iamai_section
    assert 'placeholder: "iamai>=1,<2"' in browser
    assert "iamai>=0.4,<0.5" not in tutorial
    assert "iamai>=0.4,<0.5" not in iamai_section
    assert "iamai>=0.4,<0.5" not in browser


def test_ecosystem_browser_executes_admission_contracts() -> None:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node is required for ecosystem browser contract tests")
    source = _read("docs/_static/iamai-store.js")
    marker = '  if (document.readyState === "loading") {'
    instrumented = source.replace(
        marker,
        "  globalThis.__iamaiStoreTest = { splitLines, isPublicHttpUrl, buildIssueUrl };\n\n"
        + marker,
        1,
    )
    script = f"""
const vm = require("node:vm");
const context = {{
  console,
  URL,
  URLSearchParams,
  window: {{}},
  document: {{
    currentScript: null,
    documentElement: {{ lang: "en" }},
    readyState: "loading",
    addEventListener() {{}},
    querySelectorAll() {{ return []; }},
  }},
}};
vm.createContext(context);
vm.runInContext({json.dumps(instrumented)}, context);
const api = context.__iamaiStoreTest;
const issueUrl = api.buildIssueUrl(
  {{ dataset: {{ githubRepo: "retrofor/iamai" }} }},
  {{ id: "ruleset.demo", name: "Demo", type: "ruleset", summary: "Demo", package: "demo" }},
);
const query = Object.fromEntries(new URL(issueUrl).searchParams);
console.log(JSON.stringify({{
  lines: api.splitLines("https://ci.example.com/a,b\\nhttps://ci.example.com/c"),
  accepted: api.isPublicHttpUrl("https://github.com/example/actions/runs/123"),
  rejected: [
    "https://user:secret@github.com/example/run",
    "https://localhost/run",
    "https://100.64.0.1/run",
    "https://192.0.2.1/run",
    "https://[::ffff:127.0.0.1]/run",
    "https://[ff02::1]/run",
    "https://0177.0.0.1/run",
    "https://0x7f.0.0.1/run",
    "https://127.1/run",
    "https://foo..com/run",
    "https://-foo.com/run",
    "https://foo_.com/run",
  ].every((url) => !api.isPublicHttpUrl(url)),
  iamaiRequires: query.iamai_requires,
  evidence: query.conformance_evidence,
}}));
"""
    result = subprocess.run(
        [node, "-e", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "lines": ["https://ci.example.com/a,b", "https://ci.example.com/c"],
        "accepted": True,
        "rejected": True,
        "iamaiRequires": "Not applicable",
        "evidence": "Not applicable",
    }


def test_roadmap_contains_versioned_design_decisions() -> None:
    content = _read("docs/guides/roadmap.rst")

    assert "``0.1``" in content
    assert "``0.2``" in content
    assert "``0.3``\n   |latest-stable|" in content
    assert "``0.4``\n   |implemented|" in content
    assert "``1.0``\n   |release-candidate|" in content
    assert "WebUI 不进入核心" in content


def test_community_page_contains_blog_and_store_sections() -> None:
    content = _read("docs/community/index.rst")

    assert "BLOG" in content
    assert ".. iamai-blog::" in content
    assert "社区商店" in content
    assert "blog/index" in content
    assert "store" in content


def test_blog_and_store_pages_are_split_under_community() -> None:
    blog = _read("docs/community/blog/index.rst")
    store = _read("docs/community/store.rst")

    assert ".. iamai-blog::" in blog
    assert ".. iamai-store::" in store
    assert ".. iamai-store-submit::" not in store
