# PYPOST-1224: [Libraries] Modernize examples to unified library format and preserve legacy fixtures in tests

## Goals

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), PyPost has introduced:
- Collection format v2 with embedded variable metadata ([PYPOST-1220](https://pypost.atlassian.net/browse/PYPOST-1220)).
- Library manifest schema (`pypost-library.yaml` / `.json`) and local user secret overlay management ([PYPOST-1221](https://pypost.atlassian.net/browse/PYPOST-1221)).
- Git library backend service ([PYPOST-1222](https://pypost.atlassian.net/browse/PYPOST-1222)).
- Desktop UI Library Manager panel ([PYPOST-1223](https://pypost.atlassian.net/browse/PYPOST-1223)).

With all core library and collection formats in place, the `examples/` directory in the repository must be modernized to serve as a complete, canonical example of a version-controlled Git collection library.

At the same time, existing tests and backward compatibility checks that rely on legacy collection format v1 / separate environment JSON fixtures must continue to work without regression. Moving legacy fixtures into dedicated test fixture paths ensures that future refactors don't inadvertently break legacy import paths.

**Business Goal:**
Modernize `examples/` into a unified, self-contained Collection Library with a valid `pypost-library.yaml` manifest, self-contained collections with embedded variable declarations, and preserve all legacy collection and environment fixtures under `tests/fixtures/legacy_collections/` with automated backward-compatibility regression tests.

## User Stories

- As a **Developer adopting PyPost**, I want the `examples/` directory to serve as a reference implementation of a Git-based Collection Library, containing a valid `pypost-library.yaml` manifest and clear instructions, so that I can easily create my team's own collection library repository.
- As a **PyPost Maintainer**, I want legacy format fixtures preserved in `tests/fixtures/legacy_collections/` with automated regression tests, so that existing user collections and environments created in previous PyPost versions continue to import and function seamlessly.
- As an **Agent or MCP Client**, I want the Jira MCP example to remain fully operational and verified, allowing zero-downtime migration to the modern library format.

## Definition of Done

1. `examples/` contains a valid `pypost-library.yaml` manifest that passes `read_library_manifest` and `validate_manifest_collections`.
2. Collections in `examples/collections/` are modernized to collection format v2 with embedded variable declarations (`jira_base_url`, `jira_project_key`, `jira_credentials`).
3. Legacy fixtures are copied and preserved under `tests/fixtures/legacy_collections/` (`jira_mcp.json`, `jira_cloud.json`, `mcp.json`).
4. Automated tests verify:
   - Modern `examples/` manifest and collections load and validate cleanly.
   - Legacy fixtures under `tests/fixtures/legacy_collections/` continue to import cleanly via legacy import pathways (`CollectionStorageGateway`, `EnvironmentStorageGateway`, etc.).
5. `examples/README.md` is updated with modern library usage instructions, clone commands, and manifest explanations.
6. Full quality gates pass (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`).
