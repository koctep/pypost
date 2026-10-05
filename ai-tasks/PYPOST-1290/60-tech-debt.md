# PYPOST-1290: Technical Debt Analysis

## Shortcuts Taken

No shortcuts or temporary workarounds were introduced. The solution:
1. Observes `QShortcut.activatedAmbiguously` on all secondary/group shortcuts in `pypost/ui/hotkeys.py`
   via standard parameter-binding lambdas, logging `hotkey_ambiguous key=%s` at WARNING level.
2. Implements `collect_live_shortcuts(root: QWidget)` to perform full inspection of live window key
   sequences across `QShortcut` instances and functional `QAction` objects.
3. Leaves `pypost/ui/main_window.py` completely untouched, respecting its strict LOC limits (459 / 477 cap).

## Code Quality Issues

No new code quality issues were introduced.
- Function breakdown is clean and localized in `pypost/ui/hotkeys.py`.
- Typing adheres strictly to mypy baseline requirements without introducing any new type errors.
- PEP 8 and 100-character line length limits are fully satisfied.

## Missing Tests

- No missing tests for the implemented functionality.
- `tests/test_main_window_hotkeys.py` covers:
  - Triggering `activatedAmbiguously` on hotkey shortcuts and capturing the structured WARNING log.
  - Window-wide live shortcut collection confirming zero duplicate key sequences across `MainWindow`.
  - Deliberately injecting duplicate shortcuts on `MainWindow` to verify collision detection.
- All test functions in `tests/test_main_window_hotkeys.py` are covered by the module-level timeout
  marker `pytestmark = pytest.mark.timeout(120)`, satisfying the blocker-class test requirement.

## Performance Concerns

No performance concerns. `collect_live_shortcuts` is only invoked during automated testing and
diagnostic checks. The runtime ambiguous activation handler is a zero-cost signal-slot connection
that only executes if Qt detects an ambiguous keystroke.

## Follow-up Tasks

No new technical debt follow-up issues required for this task.

Pre-existing baseline test failures remain tracked under their respective existing Jira issues:
- **NON-BLOCKER — pre-existing**: `PYPOST-1261` (Malformed template expression classification in
  `tests/test_function_expression_resolver.py` and `tests/test_template_service.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1287` (Dialog inventory in
  `tests/test_pypost_1077_verification_artifacts.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1286` (WebSocket stream export in
  `tests/test_websocket_stream_view_repro.py`).
- **NON-BLOCKER — pre-existing**: `PYPOST-1262` (Makefile and exit-policy timeouts in
  `tests/test_makefile_lifecycle.py`, `tests/test_makefile_targets.py`, and `tests/test_pytest_exit_policy.py`).
