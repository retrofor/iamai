# FOSSA PR #432 dependency license investigation — worker 1

Date: 2026-07-14
Task: enumerate repo-local Python and Rust dependency license risks for PR #432 / head `b8247136a8aa74e77faee630656d5894d54655be` and try to account for the reported 11 FOSSA License Compliance issues.

## Confirmed facts

- The PR investigation brief says FOSSA reports `11 issues found` on PR #432 head `b8247136a8aa74e77faee630656d5894d54655be`; `master` independently reports 24 issues; no local FOSSA API token is available; public issue detail is expected to require authentication.
- The worktree is checked out at `b8247136a8aa74e77faee630656d5894d54655be`.
- Python dependency resolution is locked in `uv.lock` with 127 packages.
- Rust dependency resolution is locked in `Cargo.lock` with 27 packages.
- No repo-local `.fossa.yml`/`fossa.yml` was present in the worktree scan.

## Highest-confidence local issue class: Python workspace packages without declared project license

All current Python workspace projects below have `[project]` metadata but no `project.license` and no `project.license-files` entry in their `pyproject.toml` files:

| Package | Path | Notes |
| --- | --- | --- |
| `iamai` | `pyproject.toml` | Root Python package. `origin/master` had `license = { text = "AGPL-3.0" }`; this PR head has no Python project license field. |
| `iamai-example-utils` | `examples/_shared/pyproject.toml` | New workspace helper package relative to `origin/master`. |
| `arcade-runtime` | `examples/arcade-runtime/pyproject.toml` | New workspace example package. |
| `echo-runtime` | `examples/echo-runtime/pyproject.toml` | New workspace example package. |
| `group-assistant-runtime` | `examples/group-assistant-runtime/pyproject.toml` | New workspace example package. |
| `life-sim-runtime` | `examples/life-sim-runtime/pyproject.toml` | New workspace example package. |
| `persona-rp-runtime` | `examples/persona-rp-runtime/pyproject.toml` | New workspace example package. |
| `planner-executor-runtime` | `examples/planner-executor-runtime/pyproject.toml` | New workspace example package. |
| `react-runtime` | `examples/react-runtime/pyproject.toml` | New workspace example package; adds `fastmcp`. |
| `skill-chat-runtime` | `examples/skill-chat-runtime/pyproject.toml` | New workspace example package. |
| `state-runtime` | `examples/state-runtime/pyproject.toml` | New workspace example package. |
| `story-runtime` | `examples/story-runtime/pyproject.toml` | New workspace example package. |
| `supervisor-team-runtime` | `examples/supervisor-team-runtime/pyproject.toml` | New workspace example package. |

This is 13 repo-local Python packages with missing declared license metadata. Because the FOSSA check reports 11 issues, the exact 11 cannot be proven from local files alone. The strongest local explanation is that FOSSA is flagging a subset of these workspace packages as unlicensed/unknown-license projects, likely excluding some combination of the root package, `_shared`, or packages not materialized as standalone projects in its scan. Exact selection is credential-gated by FOSSA issue detail.

## External dependency license spot checks

Targeted published-metadata checks for high-impact Python dependencies showed permissive declared metadata/classifiers:

| Package | Locked / relevant version source | Published metadata observed |
| --- | --- | --- |
| `loguru` | `uv.lock` `0.7.3` | PyPI classifier: MIT License. |
| `pydantic` | `uv.lock` `2.13.4` | PyPI `license_expression`: MIT. |
| `tomli` | `uv.lock` `2.4.1` | PyPI `license_expression`: MIT. |
| `websockets` | direct bound `>=15,<16`; lock had `15.0.1` | PyPI latest metadata observed `license_expression`: BSD-3-Clause. Exact locked-version endpoint should be checked if FOSSA reports this package. |
| `openai` | `_shared` direct dependency, lock had `1.109.1` | PyPI latest metadata observed `license`: Apache-2.0 plus Apache classifier. Exact locked-version endpoint should be checked if FOSSA reports this package. |
| `fastmcp` | `react-runtime` direct dependency, lock had `3.4.2` | PyPI latest metadata observed `license_expression`: Apache-2.0 plus Apache classifier. Exact locked-version endpoint should be checked if FOSSA reports this package. |
| `sphinx` | docs group / docs requirements | PyPI latest metadata observed `license_expression`: BSD-2-Clause. |
| `furo` | docs group / docs requirements | PyPI classifier: MIT License. |
| `mypy` | dev group | PyPI latest metadata observed `license_expression`: MIT. |
| `pytest` | dev group | PyPI latest metadata observed `license_expression`: MIT. |

Targeted crates.io exact-version checks for Rust dependencies also showed permissive license expressions:

| Crate | Locked version | crates.io version metadata observed |
| --- | --- | --- |
| `pyo3` | `0.27.2` | `MIT OR Apache-2.0`. |
| `serde` | `1.0.228` | `MIT OR Apache-2.0`. |
| `serde_json` | `1.0.149` | `MIT OR Apache-2.0`. |
| `proc-macro2` | `1.0.106` | `MIT OR Apache-2.0`. |
| `quote` | `1.0.45` | `MIT OR Apache-2.0`. |
| `syn` | `2.0.117` | `MIT OR Apache-2.0`. |
| `libc` | `0.2.186` | `MIT OR Apache-2.0`. |
| `target-lexicon` | `0.13.5` | `Apache-2.0 WITH LLVM-exception`. |

## Inference

1. The Rust lockfile is unlikely to account for the 11 FOSSA issues: direct and sampled transitive crates use common permissive SPDX expressions, and the local Rust crate declares `license = "MIT"` in `Cargo.toml`.
2. The best repo-local accounting for the 11 issues is Python workspace package metadata, especially newly added example packages without `project.license` or `project.license-files`.
3. The count mismatch (13 missing local Python package licenses vs. 11 FOSSA issues) means worker 1 cannot truthfully name the exact 11 without FOSSA issue detail or reproducing FOSSA's exact project-discovery model.

## Smallest safe remediation to propose to the leader

Do not disable FOSSA. Do not loosen the policy. Retrieve the authenticated FOSSA issue details first if available. If the issue list confirms `No license found` / `Unknown license` for local workspace Python packages, the smallest remediation is to add consistent declared license metadata to the affected `[project]` tables, aligned with the repo's intended license for v0.3.0, then refresh `uv.lock` if the build backend emits changed metadata.

## Sources / verification commands used

- Repo context: `/Users/Admin/Gitprojects/iamai/.omx/context/fossa-compliance-investigation-20260714T120000Z.md`.
- Local revision: `git rev-parse HEAD` → `b8247136a8aa74e77faee630656d5894d54655be`.
- Python local package scan: parsed `pyproject.toml` and `examples/*/pyproject.toml` for `[project]` `name`, `license`, and `license-files`.
- Python lock summary: parsed `uv.lock` with Python `tomllib`.
- Rust lock summary: parsed `Cargo.lock` with Python `tomllib`.
- Master comparison: `git show origin/master:pyproject.toml`; example package manifests are absent from `origin/master`.
- Published metadata: PyPI JSON API and crates.io API targeted probes. For a final compliance fix, prefer exact-version endpoints such as `https://pypi.org/pypi/<project>/<version>/json` and `https://crates.io/api/v1/crates/<crate>/<version>`.
