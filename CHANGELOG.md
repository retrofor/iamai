# Changelog

All notable changes to iamai are documented in this file.

## [0.3.0] - 2026-07-15

### Added

- Added the Skill Chat runtime example with memory, skills, tool routing, and management integration.
- Extended the ReAct runtime with MCP tools, persona-aware chat mode, configurable model request bodies, and deterministic mock coverage.
- Added configurable handler concurrency backpressure and bounded session backlogs with per-key limits and expiry.

### Changed

- Raised the supported Python baseline to 3.11 and expanded CI coverage through Python 3.13.
- Restored Ruff, Mypy, Pytest, Rust, docs, and example-config checks as release gates.
- Consolidated tag publishing into one workflow that signs artifacts, publishes to PyPI, and creates a GitHub Release.
- Upgraded PyO3 to 0.29.0, enabled the CPython 3.11 stable ABI for portable wheels, and refreshed the example Starlette lock to resolve published security advisories.
- Made handler admission fail closed per event: capacity pressure rejects the complete matched handler set instead of executing a partial fan-out.
- Synchronized the MIT license file and package metadata across the Python, Rust, and example workspaces.

### Fixed

- Fixed plugin loading on Windows paths and tightened example runtime type safety.
- Fixed example LLM environment precedence, extra request body validation, and test-time log pollution.

[0.3.0]: https://github.com/retrofor/iamai/releases/tag/v0.3.0
