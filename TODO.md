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
| 1. FOSSA governance | `BLOCKED_EXTERNAL` | [PR #446](https://github.com/retrofor/iamai/pull/446); [baseline](docs/reference/fossa-governance-baseline.rst); [#436 latest gate recheck](https://github.com/retrofor/iamai/issues/436#issuecomment-5042576430) | Blocking owner: retrofor FOSSA project/organization owners; last verified 2026-07-22; project/tracking branch, exact `dev@50db02b`, and PR #467 are analyzed, but the target policy, full inventories/dispositions, and waiver retirement remain incomplete |
| 2. Low-risk dependencies | `DONE` | [#437](https://github.com/retrofor/iamai/pull/437), [#439](https://github.com/retrofor/iamai/pull/439), [#441](https://github.com/retrofor/iamai/pull/441), [#442](https://github.com/retrofor/iamai/pull/442), [#443](https://github.com/retrofor/iamai/pull/443), [#464](https://github.com/retrofor/iamai/pull/464); [post-#464 CI](https://github.com/retrofor/iamai/actions/runs/29556409168); [CodeQL](https://github.com/retrofor/iamai/actions/runs/29556408804) | Original batch completed 2026-07-15; follow-up #464 verified 2026-07-17 at [`dev@be678ba`](https://github.com/retrofor/iamai/commit/be678ba70c8f90904839845cc977460b55dd3719) |
| 3. Gated dependencies | `DONE` | [#438](https://github.com/retrofor/iamai/pull/438), [release rehearsal](https://github.com/retrofor/iamai/actions/runs/29404691605), [#449](https://github.com/retrofor/iamai/pull/449), [#440](https://github.com/retrofor/iamai/pull/440), [final CI](https://github.com/retrofor/iamai/actions/runs/29407069117), [CodeQL](https://github.com/retrofor/iamai/actions/runs/29407068347) | Completed 2026-07-15 at [`dev@44a237a`](https://github.com/retrofor/iamai/commit/44a237a7c75fb0ca52ac87a0fed862b6186968ae) |
| 4. Version 0.4 contract | `DONE` | [#435](https://github.com/retrofor/iamai/issues/435); [0.4-A PR #451](https://github.com/retrofor/iamai/pull/451); [0.4-B PR #453](https://github.com/retrofor/iamai/pull/453); [0.4-C PR #454](https://github.com/retrofor/iamai/pull/454); [metadata follow-up PR #460](https://github.com/retrofor/iamai/pull/460); [post-merge CI](https://github.com/retrofor/iamai/actions/runs/29485373909); [CodeQL](https://github.com/retrofor/iamai/actions/runs/29485371056) | Completed 2026-07-16 at [`dev@a2aaa6d`](https://github.com/retrofor/iamai/commit/a2aaa6d2e25744e7a172d221ae177a8b190597f6) after resolving the actionable #454 review thread |
| 5. Version 1.0 contract | `DONE` | [#434](https://github.com/retrofor/iamai/issues/434); [v1.0-A PR #455](https://github.com/retrofor/iamai/pull/455); [v1.0-B PR #456](https://github.com/retrofor/iamai/pull/456); [v1.0-C PR #457](https://github.com/retrofor/iamai/pull/457); [ledger PR #458](https://github.com/retrofor/iamai/pull/458); [post-merge CI](https://github.com/retrofor/iamai/actions/runs/29476469346); [CodeQL](https://github.com/retrofor/iamai/actions/runs/29476468746); [final exact-head RC rehearsal](https://github.com/retrofor/iamai/actions/runs/29476523367); [closure evidence](https://github.com/retrofor/iamai/issues/434#issuecomment-4988890101) | Contract acceptance completed 2026-07-16 at [`dev@b6b47ae`](https://github.com/retrofor/iamai/commit/b6b47ae19ec2446cc598ade71afbacfcf8388c84); any release tag still requires a fresh exact-head rehearsal after final version and ledger changes |
| 6. needs-info closure | `BLOCKED_EXTERNAL` | [#294 clarification](https://github.com/retrofor/iamai/issues/294#issuecomment-4977531567), [#295 clarification](https://github.com/retrofor/iamai/issues/295#issuecomment-4977531779), [#297 clarification](https://github.com/retrofor/iamai/issues/297#issuecomment-4977532019), [#306 clarification](https://github.com/retrofor/iamai/issues/306#issuecomment-4977531163) | Last verified 2026-07-22; no external replies and the deadline has not passed; resume after 2026-07-29 23:59 UTC |

## 0. Specification baseline

- [x] Publish the execution spec and this ledger through a reviewed PR with green CI.

## 1. FOSSA and release governance

Tracking: [#436](https://github.com/retrofor/iamai/issues/436)

- [x] Confirm whether a usable FOSSA Full credential or UI session is available: none is present in the current environment.
- [x] Repoint the FOSSA project and revision analysis from `master` to `dev`; public evidence records
  `default_branch=dev`, `tracking_branches` includes `dev`, and a completed analysis for exact `dev@50db02b`.
- [x] Confirm analyzed `dev@50db02b` detects first-party SPDX `MIT`, exposes no AGPL license entry, and reports
  zero public unresolved counts; full active/ignored inventories remain a separate release gate below.
- [x] Analyze exact `dev@50db02b` and confirm FOSSA `last_analyzed_revision`, project head, `dev` reference,
  and GitHub `License Compliance` status all match; repeat after future release-input changes.
- [ ] Change the project policy from `Single-Binary Distribution` to `Standard Bundle Distribution`.
- [ ] Export active and ignored issue inventories with dependency, version, license, policy, locator, status,
  waiver/ignore reason, and disposition.
- [ ] Resolve, allow, or time-bound waive every current finding.
- [x] Verify one `dev` revision (`50db02b`) and one PR revision ([#467](https://github.com/retrofor/iamai/pull/467),
  `d9da203`); attach the evidence to [#436](https://github.com/retrofor/iamai/issues/436#issuecomment-5042576430).
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
- [x] Reject invalid explicit plugin names through PR #460 and resolve the actionable #454 review thread.

## 5. Version 1.0 public API contract

Tracking: [#434](https://github.com/retrofor/iamai/issues/434)

- [x] Publish the versioned Event/Message serialization contract through PR #455.
- [x] Add valid/invalid golden round-trip tests through PR #455.
- [x] Publish and test Runtime/Adapter/Plugin lifecycle ordering and failure semantics through PR #456.
- [x] Define and test Context event scope, reply routing, dependency injection, and invalidation semantics through PR #456.
- [x] Expose the serialization contract version and test supported evolution rules through PR #455.
- [x] Publish the normative conformance matrix through PR #457.
- [x] Publish the deprecation policy and minimum support window through PR #457.
- [x] Publish the final 0.x to 1.0 migration guide through PR #457.
- [x] Validate the complete contract against a 1.0 RC through the initial exact-head rehearsal.
- [x] Rerun the 18-job non-publishing rehearsal at final ledger SHA `b6b47ae`, attach the evidence, and close #434.

## 6. needs-info issue closure

Deadline: 2026-07-29 23:59 UTC.

- [ ] Recheck [#294](https://github.com/retrofor/iamai/issues/294), [#295](https://github.com/retrofor/iamai/issues/295), and [#297](https://github.com/retrofor/iamai/issues/297) after the deadline.
- [ ] Close them if unanswered, or replace them with one owned, testable i18n issue.
- [ ] Recheck [#306](https://github.com/retrofor/iamai/issues/306) after the deadline.
- [ ] Close or migrate #306 unless it proves a core runtime scheduling contract.
- [ ] Confirm no unowned wishlist remains on the core roadmap.

## Cross-cutting verification

- [x] Recheck GitHub Dependabot alerts after dependency-graph recomputation: 0 open alerts on 2026-07-16; none dismissed manually.
- [x] Verify the latest implementation merge preceding this ledger at `dev@a2aaa6d`: required checks and CodeQL green, branch protection intact, and working tree clean.
- [x] Recheck follow-up dependency merge [#464](https://github.com/retrofor/iamai/pull/464) at `dev@be678ba`:
  required checks and CodeQL are green, branch protection is intact, the working tree is clean, and the latest
  non-publishing release rehearsal still targets older `dev@b6b47ae`; a fresh exact-head rehearsal remains required
  before any release tag.
- [ ] At the release-candidate freeze, record the final implementation SHA, branch protection, clean tree, and a
  fresh exact-head non-publishing release rehearsal; reopen this item if implementation changes after that evidence.
