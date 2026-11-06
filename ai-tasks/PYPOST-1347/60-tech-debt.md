# PYPOST-1347: Technical Debt Analysis

## Shortcuts Taken

- **Collection-resolve helper mirrors resolver checks**: `_ordinary_library_collection_resolves`
  reimplements the connected-library / manifest / readable-file checks from
  `LibraryRuntimeResolver` instead of calling `resolve()` and discarding the layered
  environment. This avoids running variable-layer merge on every reconcile tick, but means
  two code paths can drift if resolver validation categories change.
- **Silent skip on refresh resolve failure (pre-widening behavior retained)**: when
  `LibraryRuntimeResolver.resolve` raises `ValueError` during `refresh_environment`, the row
  is left on its previous snapshot after a WARNING log. The server is not stopped. That matches
  Built-in’s prior silent `continue`, now observable; operators must still rely on a later
  reconcile/start to force a hard stop if the library became invalid mid-session.
- **No controller/UI changes**: ordinary-library save/edit UX is unchanged; Debt scope stayed in
  `MCPServerRegistry` only (per requirements Scope Out).

## Code Quality Issues

- **Duplicated connection probe**: reconcile checks `get_connection` for `lib_valid`, then
  `_ordinary_library_collection_resolves` probes the connection again. Harmless but redundant;
  could fold into a single “ordinary library inputs valid” helper later.
- **`getattr` duck-typing on `library_service`**: `get_connection` / `resolve_path` remain
  optional attributes (existing registry style for injectable fakes). Stronger Protocol typing
  would clarify the ordinary-library service contract.
- **Lazy imports** inside `_ordinary_library_collection_resolves` and `refresh_environment`
  match surrounding registry style but keep import cost/error surfaces local rather than
  module-top.

## Missing Tests

- No dedicated automated case asserting
  `mcp_registry_refresh_library_environment_failed` when resolve raises during refresh
  (success + collection-miss paths are covered in
  `test_ordinary_library_lifecycle_observability_and_logging`).
- No explicit unit test that `_validate_replacement_references` raises
  `missing library collection` for an ordinary row with a deleted collection file (covered
  indirectly by reconfigure success when valid; stop-on-reconcile covers the same helper).
- Overlay/preset-heavy refresh equality is asserted via full snapshot equality against
  `LibraryRuntimeResolver` for the fixture library; additional fixtures with non-empty
  overlays/presets would harden edge cases beyond the default `base_url` manifest key.

## Performance Concerns

- Reconcile now may read the library manifest and collection file once per ordinary library
  row when the connection is still present. Cost is local filesystem I/O on UI-driven
  reconcile (Environment Manager close / collection sync), not on the hot request path.
  Acceptable for typical row counts; if large libraries + many concurrent rows become common,
  cache manifest readability for a single reconcile pass.

## Follow-up Tasks

Recorded during Step 4 `make check` triage (baseline commit
`519eabf1dd7ffbadb34f93662b62cfeb651562c3`). These failures predate this task’s
production changes and are **NON-BLOCKER**. Do not create new Jira from this Step 7 pass —
keys already exist.

| Test ids | Verdict | Jira |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples`<br>`tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | NON-BLOCKER — pre-existing (same at base) | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_pypost_1077_verification_opcodes.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`<br>`tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | NON-BLOCKER — pre-existing (same at base) | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | NON-BLOCKER — pre-existing lockfile drift / env-sensitive (`check-lock-dev` stale); already tracked | [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |

Repro: `make check` (or narrowed `make test PYTEST_ARGS=...` per ticket).

Additional follow-ups from this Step 7 analysis (not filed; document only per orchestrator
instruction):

1. Consider extracting shared “collection still readable” validation used by
   `LibraryRuntimeResolver` and `_ordinary_library_collection_resolves` to eliminate drift risk.
2. Optional: assert WARNING event when refresh resolve fails; optional overlay/preset refresh
   fixture.
3. Optional: stop-or-mark-failed on refresh resolve failure for library-sourced rows (product
   decision; currently retain previous snapshot + WARNING).
