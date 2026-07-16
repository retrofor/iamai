# Post-v0.3 execution TODO

This ledger tracks the ordered work defined in
[`docs/reference/post-v0.3-execution-spec.rst`](docs/reference/post-v0.3-execution-spec.rst).
Evidence must be a commit, PR, CI run, test output, issue comment, or an explicit external blocker.

Status values:

- `TODO`: not started.
- `IN_PROGRESS`: the current sequential workstream.
- `BLOCKED_EXTERNAL`: requires credentials, an external owner, or a future deadline; the checkbox stays open.
- `DONE`: every acceptance criterion is satisfied and linked.

## Execution status

| Workstream | Status | Evidence | Blocker / last verified / resume condition |
| --- | --- | --- | --- |
| 0. Specification baseline | `DONE` | [PR #445](https://github.com/retrofor/iamai/pull/445); [post-merge CI](https://github.com/retrofor/iamai/actions/runs/29400584855); [CodeQL](https://github.com/retrofor/iamai/actions/runs/29400584086) | Completed 2026-07-15 |
| 1. FOSSA governance | `BLOCKED_EXTERNAL` | [PR #446](https://github.com/retrofor/iamai/pull/446); [baseline](docs/reference/fossa-governance-baseline.rst); [#436 update](https://github.com/retrofor/iamai/issues/436#issuecomment-4978607129) | Last verified 2026-07-15; no FOSSA CLI, token, or login; resume with project-admin login or API key |
| 2. Low-risk dependencies | `DONE` | [#437](https://github.com/retrofor/iamai/pull/437), [#439](https://github.com/retrofor/iamai/pull/439), [#441](https://github.com/retrofor/iamai/pull/441), [#442](https://github.com/retrofor/iamai/pull/442), [#443](https://github.com/retrofor/iamai/pull/443); [final CI](https://github.com/retrofor/iamai/actions/runs/29404149717) | Completed 2026-07-15 at [`dev@47e4b8a`](https://github.com/retrofor/iamai/commit/47e4b8a7a671ce82826c6f4e1238ec255cff1506) |
| 3. Gated dependencies | `DONE` | [#438](https://github.com/retrofor/iamai/pull/438), [release rehearsal](https://github.com/retrofor/iamai/actions/runs/29404691605), [#449](https://github.com/retrofor/iamai/pull/449), [#440](https://github.com/retrofor/iamai/pull/440), [final CI](https://github.com/retrofor/iamai/actions/runs/29407069117), [CodeQL](https://github.com/retrofor/iamai/actions/runs/29407068347) | Completed 2026-07-15 at [`dev@44a237a`](https://github.com/retrofor/iamai/commit/44a237a7c75fb0ca52ac87a0fed862b6186968ae) |
| 4. Version 0.4 contract | `DONE` | [#435](https://github.com/retrofor/iamai/issues/435); [0.4-A PR #451](https://github.com/retrofor/iamai/pull/451); [0.4-B PR #453](https://github.com/retrofor/iamai/pull/453); [0.4-C PR #454](https://github.com/retrofor/iamai/pull/454); [post-merge CI](https://github.com/retrofor/iamai/actions/runs/29467188102); [CodeQL](https://github.com/retrofor/iamai/actions/runs/29467187810) | Completed 2026-07-16 at [`dev@3a83c9f`](https://github.com/retrofor/iamai/commit/3a83c9f986f25e9522b6cfa1dcddb11b12845f13) |
| 5. Version 1.0 contract | `IN_PROGRESS` | [#434](https://github.com/retrofor/iamai/issues/434); [v1.0-A PR #455](https://github.com/retrofor/iamai/pull/455); [merge `d67d639`](https://github.com/retrofor/iamai/commit/d67d639b1abbce9c846a63c3efc98de0cdfe3574); [v1.0-A CI](https://github.com/retrofor/iamai/actions/runs/29469491022); [v1.0-A CodeQL](https://github.com/retrofor/iamai/actions/runs/29469490546); [v1.0-B PR #456](https://github.com/retrofor/iamai/pull/456); [v1.0-B CI](https://github.com/retrofor/iamai/actions/runs/29471659626); [v1.0-B CodeQL](https://github.com/retrofor/iamai/actions/runs/29471657366) | v1.0-B required CI green; final ledger commit and merge pending |
| 6. needs-info closure | `TODO` | Issues #294, #295, #297, #306 | Time-triggered exception: execute after 2026-07-29 23:59 UTC even if workstreams 4-5 remain active |

## 0. Specification baseline

- [x] Publish the execution spec and this ledger through a reviewed PR with green CI.

## 1. FOSSA and release governance

Tracking: [#436](https://github.com/retrofor/iamai/issues/436)

- [x] Confirm whether a FOSSA project-admin login or API token is available: none is present in the current environment.
- [ ] Repoint the FOSSA project and revision analysis from `master` to `dev`.
- [ ] Confirm the project license is SPDX `MIT` and remove the phantom AGPL conclusion.
- [ ] Change the project policy from `Single-Binary Distribution` to `Standard Bundle`.
- [ ] Export the current issue inventory with dependency, version, license, policy, locator, and disposition.
- [ ] Resolve, allow, or time-bound waive every current finding.
- [ ] Verify one `dev` revision and one PR revision; attach evidence to #436.
- [ ] Remove or replace the v0.3.0 waiver before 2026-08-15.
- [ ] Close #436 only after the spec completion definition is met.

## 2. Low-risk dependency PRs

- [x] Update, verify, and merge [#437](https://github.com/retrofor/iamai/pull/437) (`serde_json`).
- [x] Update, verify, and merge [#439](https://github.com/retrofor/iamai/pull/439) (Ruff/FastMCP).
- [x] Update, verify, and merge [#441](https://github.com/retrofor/iamai/pull/441) (Mypy 2).
- [x] Update, verify, and merge [#442](https://github.com/retrofor/iamai/pull/442) (Pytest 9).
- [x] Update, verify, and merge [#443](https://github.com/retrofor/iamai/pull/443) (Sphinx 9).
- [x] Verify final `dev` lockfiles and post-merge CI.

## 3. Dependency PRs with special gates

- [x] Update [#438](https://github.com/retrofor/iamai/pull/438) to the latest `dev`.
- [x] Run a non-tag release rehearsal for #438 and verify every build and attestation job.
- [x] Merge #438 and verify post-merge `dev` CI.
- [x] Add real WebSocket loopback regression tests for #440.
- [x] Run the loopback tests on Python 3.11 and 3.13.
- [x] Update, verify, and merge [#440](https://github.com/retrofor/iamai/pull/440).
- [x] Verify post-merge `dev` CI.

## 4. Version 0.4 extension contract

Tracking: [#435](https://github.com/retrofor/iamai/issues/435)

- [x] 0.4-A: publish packaging/discovery metadata and deterministic error contracts.
- [x] 0.4-A: add installable reference adapter and plugin fixtures with isolated-install tests.
- [x] 0.4-B: implement one root/runtime/adapter/plugin schema generator.
- [x] 0.4-B: add stable IDs, contract version, defaults, and secret annotations.
- [x] 0.4-B: prove CLI and management API schema equivalence.
- [x] 0.4-C: publish adapter and plugin conformance helpers.
- [x] 0.4-C: run the helpers against both reference distributions in isolated environments.
- [x] Document ecosystem admission evidence; #435 closes through PR #454 when merged.

## 5. Version 1.0 public API contract

Tracking: [#434](https://github.com/retrofor/iamai/issues/434)

- [x] Publish the versioned Event/Message serialization contract through PR #455.
- [x] Add valid/invalid golden round-trip tests through PR #455.
- [x] Publish and test Runtime/Adapter/Plugin lifecycle ordering and failure semantics through PR #456.
- [x] Define and test Context event scope, reply routing, dependency injection, and invalidation semantics through PR #456.
- [x] Expose the serialization contract version and test supported evolution rules through PR #455.
- [ ] Publish the normative conformance matrix.
- [ ] Publish the deprecation policy and minimum support window.
- [ ] Publish the final 0.x to 1.0 migration guide.
- [ ] Validate the complete contract against a 1.0 RC and close #434.

## 6. needs-info issue closure

Deadline: 2026-07-29 23:59 UTC.

- [ ] Recheck [#294](https://github.com/retrofor/iamai/issues/294), [#295](https://github.com/retrofor/iamai/issues/295), and [#297](https://github.com/retrofor/iamai/issues/297) after the deadline.
- [ ] Close them if unanswered, or replace them with one owned, testable i18n issue.
- [ ] Recheck [#306](https://github.com/retrofor/iamai/issues/306) after the deadline.
- [ ] Close or migrate #306 unless it proves a core runtime scheduling contract.
- [ ] Confirm no unowned wishlist remains on the core roadmap.

## Cross-cutting verification

- [ ] Recheck GitHub Dependabot alerts after dependency-graph recomputation; do not dismiss fixed alerts manually.
- [ ] Keep `dev` protection, release evidence, and the working tree clean after every merge.
