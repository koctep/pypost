# PYPOST-1285: Code Cleanup Report

## Linter Fixes

- `make lint` (flake8 on `pypost/`, Markdown lint, relative link check) was already clean
  after Step 4. Nothing to fix.
- `make typecheck` was already clean (mypy baseline OK, 181 known errors, none new).

## Code Formatting

- [x] Automatic code formatting: not needed. The changed code already follows project style.
- [x] Indentation and alignment fixes: none needed.
- [x] Line length correction: every changed file is within 100 characters (checked).

## Code Cleanup

- Removed unused imports: 0 in this step. Step 4 already removed the `QApplication` /
  `QWidget` import from `pypost/ui/presenters/tabs_presenter_hotkeys.py`.
- Removed unused variables: 0.
- Removed commented-out code: none found.
- Removed debug prints: none found.
- Dead code: none. No references remain to the removed `handle_send_request_global`,
  `handle_websocket_send_global`, `handle_mcp_client_send_global`, `_focus_in_composer`,
  `_focus_in_invoke_form` or `_is_descendant` in `pypost/`, `tests/` or `doc/user/`.
- Docstrings (Step 4 reviewer note): added one-line docstrings to the new `TabsPresenter`
  facade methods `handle_f5_global`, `handle_ctrl_return_global` and
  `handle_websocket_send_message_global` in `pypost/ui/presenters/tabs_presenter.py`.
- Test hygiene: in `tests/test_main_window_hotkeys.py` and `tests/test_hotkeys.py`, rewrote
  the Step 3 docstrings that still said "RED today ..." or "Guard (green today) ...". They
  now describe the behavior each test checks. Also removed "Step 3" / "red repro" from the
  section banner comments. Assertions are unchanged.
- `ai-tasks/PYPOST-376/baseline-metrics.md`: updated the `tabs_presenter.py` LOC snapshot
  from 1070 to 1073 to cover the new docstrings (cap 1165 unchanged). The `main_window.py`
  numbers from Step 4 (459 / 411) are unchanged.

## Validation Results

- [x] All tests passed: `make test PYTEST_ARGS='tests/test_main_window_hotkeys.py
  tests/test_hotkeys.py tests/test_solid_audit_baseline.py
  tests/test_websocket_tab_mode_user_docs.py'` gave 4/4 files passing.
- [x] All tests have explicit timeout markers: module `pytestmark` (`timeout(120)` in
  `tests/test_main_window_hotkeys.py`, `timeout(30)` in `tests/test_hotkeys.py`).
- [x] No merge conflicts: no conflict markers in the changed files.
- [x] Syntax is valid: `make lint` OK.
- [x] Types are correct: `make typecheck` OK (mypy baseline 181).

## Notes

- No behavior changes in this step. The only edits are docstrings, comments and the LOC
  snapshot.
- `make lint` runs flake8 on `pypost/` only, so the test files were checked by hand for
  line length.
