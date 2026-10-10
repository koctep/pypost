# PYPOST-1350: Technical Debt Analysis

## Shortcuts Taken

None. The implementation strictly adheres to the architectural design specified in `ai-tasks/PYPOST-1350/20-architecture.md` and `ai-tasks/PYPOST-1335/decomposition.md`:
- Pure read-only view layer implemented cleanly in `pypost/core/builtin_collections.py` without mutating shipped assets or introducing stateful cache invalidation complexity.
- Built-in collections are defined declaratively in `examples/builtin-collections.yaml`, curating exactly the three required entries (`jira-cloud-mcp`, `gitlab-mcp`, `github-mcp`) while strictly excluding `collections/mcp.json`.
- Fresh loading semantics (`load_collection()`, `load_paired_environment()`) are guaranteed on each invocation to ensure modifications to shipped files are immediately reflected in memory without side effects across callers.
- Graceful error handling and diagnostic reporting: missing, corrupted, or non-manifest-declared catalog files or collection entries append explicit diagnostic messages without raising unhandled exceptions or crashing the host process.
- No monkey patches, environment overrides, or ad-hoc path heuristics were introduced.

## Code Quality Issues

None identified:
- All new and modified code is fully type-annotated and passes static analysis (`make lint` flake8, `make typecheck` mypy baseline gate).
- Line length across all modified files (`examples/builtin-collections.yaml`, `pypost/core/builtin_collections.py`, `tests/test_builtin_collections.py`) strictly respects the project <= 100 character limit.
- Structured logging adheres to syslog-aligned severity levels (DEBUG, INFO, WARNING) with standard key=value attributes for entry loading, completion, and diagnostic events.
- Code cleanly separates domain models (`BuiltinCollectionEntry`, `BuiltinCollectionView`) and delegates underlying root discovery to `PredefinedLibraryService`.
- No dead code, unused imports, or lingering debug statements exist.

## Missing Tests

None.
- The unit and contract test suite in `tests/test_builtin_collections.py` contains 12 comprehensive test functions covering happy paths, edge cases, seeded defects, and caplog logging contracts:
  1. `test_builtin_collections_list_entries`: Verifies listing of exactly the 3 curated entries matching `builtin-collections.yaml` and exclusion of `mcp.json`.
  2. `test_builtin_collection_entry_selection`: Validates identity dictionary emitted by `selection()`.
  3. `test_builtin_collections_load_collection_and_environment`: Verifies successful parsing of domain models for all 3 entries.
  4. `test_builtin_collections_load_fresh`: Ensures successive loads return distinct object instances and in-memory mutations do not leak.
  5. `test_builtin_collections_is_builtin`: Validates filtering logic for configurations matching built-in entries versus external/unlisted collections.
  6. `test_builtin_collections_invalid_view_file_graceful_handling`: Verifies non-existent or malformed catalog files return empty lists with diagnostics rather than raising.
  7. `test_builtin_collections_non_manifest_entry_rejected`: Verifies entries not declared in the library manifest are filtered out with diagnostic notices.
  8. `test_builtin_collections_logging_and_diagnostics`: Validates structured log records across DEBUG, INFO, and WARNING levels using `caplog`.
  9. `test_paired_environments_structural_consistency`: Validates structural consistency across all paired environments against manifest declarations without comparing values.
  10. `test_paired_environments_seeded_defect_missing_key`: Validates structural assertion catches missing variable keys.
  11. `test_paired_environments_seeded_defect_extra_key`: Validates structural assertion catches unexpected extraneous keys.
  12. `test_paired_environments_seeded_defect_unhidden_secret`: Validates structural assertion catches secret keys omitted from `hidden_keys`.
- Module-level timeout marker `pytestmark = pytest.mark.timeout(30)` is present per `do-testing` rules.
- Fast tests execute cleanly in under 2 seconds.

## Performance Concerns

Minimal:
- `BuiltinCollectionView.list_entries()` performs cheap, local filesystem checks and parses lightweight YAML/JSON files.
- `load_collection()` and `load_paired_environment()` perform fresh disk reads on-demand, which is appropriate for server creation/startup dialogs and configuration flows.
- If repeated frequent queries are performed in interactive UI controls, calling presenters or controllers may cache the list entries in memory during the lifetime of the dialog without impacting domain isolation.

## Follow-up Tasks

### Pre-Existing Test Failures (Non-Blockers)

The following pre-existing baseline failures were identified in the broader test suite and do not stem from PYPOST-1350 changes:
- `NON-BLOCKER — pre-existing`: **PYPOST-1358** — Native UI environment-list teardown crash during concurrent dialog cleanup.
- `NON-BLOCKER — pre-existing`: **PYPOST-1359** — dev-lock check stale with CI-pinned uv compiler resolution drift.
- `NON-BLOCKER — pre-existing`: **PYPOST-1360** — install-smoke timeout on clean base container environment.

### Planned Epic Stories (Next Steps)

The following stories decompose epic [PYPOST-1335](https://pypost.atlassian.net/browse/PYPOST-1335) and will build directly on `BuiltinCollectionView`:
- **PYPOST-1351** (C3a): Built-in identity in MCP server configuration and startup (`bundled_library` settings field and startup resolution).
- **PYPOST-1352** (C3b): Built-in rows in MCP registry lifecycle and controller save (`reconcile_references`, `refresh_environment`, transactional save).
- **PYPOST-1353** (C4): "Built-in" source with read-only marker in the MCP server dialog.
- **PYPOST-1354** (C5): Editable copy of the paired environment for Built-in MCP servers.
- **PYPOST-1355** (C6): Copy for editing a built-in MCP collection.
- **PYPOST-1356** (C7): End-to-end test and user documentation for the Built-in MCP source.
- **PYPOST-1347** (DEBT): Library MCP rows stopped as missing collection on reconcile/reconfigure; env refresh drops manifest defaults.
