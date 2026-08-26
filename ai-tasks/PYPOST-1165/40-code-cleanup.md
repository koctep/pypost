# PYPOST-1165: Code Cleanup Report

## Linter Fixes

No in-scope linter errors or warnings. `make lint` passed (flake8 on `pypost/` plus
documentation checks). `make analyze` is not a Makefile target (`No rule to make
target 'analyze'`).

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting — no project auto-format Make target; PEP 8 import
  grouping applied by hand in `tabs_presenter.py` and the PYPOST-1165 picker tests
- [x] Indentation and alignment fixes — none required beyond the import regroup
- [x] Line length correction — all in-scope production lines are at most 100
  characters (`flake8` `max-line-length = 100`)

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none

Other cleanup:

- `NewTabProtocolPicker.prompt()` maps `QAction.data()` through `TabProtocol(data)`
  instead of three equality branches, so string or enum payloads both resolve (Qt
  may unwrap `setData` values)
- `tabs_presenter.py` imports `McpClientTab` from the package
  (`pypost.ui.widgets.mcp_client`) instead of the leaf module
- Hoisted `NewTabProtocolPicker` / `TabProtocol` to module scope in
  `tests/test_new_tab_protocol_picker.py`
- Hoisted `McpClientTab` to module scope in `tests/test_tabs_presenter.py` and
  dropped redundant per-test `TabProtocol` / `McpClientTab` imports

No unused imports, unused variables, commented-out code, or debug prints remain
in the other in-scope production files (`mcp_client/`, `widget_ids.py`,
`metrics_registry.py`). Unrelated dirty files were left untouched.

## Validation Results

Validation results:

- [x] All targeted tests passed (`make test PYTEST_ARGS=` six files: 6 passed,
  0 failed, 0 skipped)
- [x] All tests have explicit timeout markers
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — no new type issues in in-scope files;
  `make typecheck` was not required for this step

Timeout markers (module `pytestmark`):

- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_new_tab_protocol_picker.py` — `timeout(60)`
- `tests/test_metrics_manager.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`
- `tests/test_metrics_registry.py` — existing module marker (unchanged)

Commands:

- `make lint` — passed
- `make analyze` — failed before analysis (target missing); closest gate is
  `make lint`
- Targeted `make test` files:
  - `tests/test_new_tab_protocol_picker.py`
  - `tests/test_tabs_presenter.py`
  - `tests/test_metrics_manager.py`
  - `tests/test_metrics_otel.py`
  - `tests/test_metrics_registry.py`
  - `tests/test_solid_audit_baseline.py` (LOC snapshot still matches after
    import-only `tabs_presenter.py` change)

## Notes

- Scope was limited to PYPOST-1165 files. PYPOST-1164, `mcp_server.py`,
  `port_allocation.py`, `AGENTS.md`, and `ai-sprints/168` were not cleaned.
- `tabs_presenter.py` line count is unchanged (import path shortened on the same
  line); SOLID snapshot did not need regeneration.
