# PYPOST-1158: Code Cleanup Report

## Linter Fixes

No in-scope linter errors or warnings. `make lint` passed (flake8 on
`pypost/` plus documentation checks). `make analyze` is not a Makefile
target (`No rule to make target 'analyze'`). Closest gate is `make lint`.

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting — no project auto-format Make target;
  PEP 8 import wrapping applied by hand in `tabs_presenter.py` and
  stdlib-before-third-party import order in two test modules
- [x] Indentation and alignment fixes — none required
- [x] Line length correction — all in-scope lines are at most 100
  characters (`flake8` `max-line-length = 100`); wrapped the draft
  helper import in `tabs_presenter.py` without growing the file

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: stale Step-4 ImportError comment in
  `tests/test_websocket_client_ui_repro.py`
- Removed debug prints: none

Other cleanup:

- Replaced the lazy import of `prompt_unsaved_draft_tab_close` in
  `tabs_presenter_draft.py` with a module-level import
- Hoisted `WebSocketConnection` to module scope in
  `tests/test_tabs_presenter.py` and dropped per-test imports
- Removed `create=True` from `prompt_unsaved_draft_tab_close` patches
  now that `tabs_presenter.py` imports the symbol
- Restored PEP 8 E305 (two blank lines before `if __name__`) in
  `tests/test_collection_item_dialogs.py`

`tabs_presenter.py` remains **785 / 785** LOC.

Unrelated dirty files (`mcp_server.py`, `mcp_live_server.py`,
`test_mcp_server_manager.py`, `port_allocation.py`, PYPOST-1176,
`AGENTS.md`, `ai-sprints/168/`) were left untouched.

## Validation Results

Validation results:

- [x] All targeted tests passed (`make test PYTEST_ARGS=` five files:
  5 passed, 0 failed, 0 skipped)
- [x] All tests have explicit timeout markers
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — no new mypy errors in
  in-scope files; `make typecheck` failed on unrelated baseline files
  (see Notes)

Timeout markers (module `pytestmark`):

- `tests/test_websocket_persisted_fields.py` — `timeout(10)`
- `tests/test_websocket_client_ui_repro.py` — `timeout(30)`
- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_collection_item_dialogs.py` — `timeout(60)`
- `tests/test_agent_e2e_websocket.py` — `timeout(60)` (plus `agent_e2e`)

Commands:

- `make lint` — passed
- `make analyze` — not available (target missing); closest gate is
  `make lint`
- `make typecheck` — failed in unrelated files (baseline-out-of-scope)
- Targeted `make test`:
  - `tests/test_tabs_presenter.py`
  - `tests/test_websocket_persisted_fields.py`
  - `tests/test_collection_item_dialogs.py`
  - `tests/test_websocket_client_ui_repro.py`
  - `tests/test_agent_e2e_websocket.py`

## Notes

- Scope was limited to PYPOST-1158 draft-tab files listed for Step 5.
  Leftover dirty files listed above were not cleaned.
- Little cleanup was needed: Step 4 already left production modules
  flake8-clean, under 100 characters, and free of debug prints.
- `make typecheck` new errors are in
  `pypost/core/qt/websocket_stream_export_worker.py` and
  `pypost/ui/dialogs/settings_dialog.py` (not this task). Documented as
  baseline-out-of-scope; not fixed here.
- `tabs_presenter.py` is at the 785 LOC audit cap. Cleanup kept the
  count at 785 (wrapped import, compacted `close_tab` call).
- Further observability belongs in Step 6.
