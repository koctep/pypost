# PYPOST-1042: Observability Implementation

## Scope

**N/A for new production logging and metrics — this task's changes are strictly test-only.**

The deliverables for PYPOST-1042 comprise:
- `tests/test_ui_actions.py`: Added dedicated contract test `test_select_tree_no_model_raises` parametrized over `["Alpha", 0]` (`ids=["by-text", "by-index"]`).
- `tests/test_ui_actions_tree_no_model_mutation.py`: Added 4 mutation-evidence items verifying guard sensitivity against guard removal and reason rewording.
- Task tracking artifacts under `ai-tasks/PYPOST-1042/`.

No production code in `pypost/` was modified. `_select_tree` in `pypost/agent/ui_actions.py` already raised `UiTargetNotInteractableError(widget_id, "tree has no model")` as its first statement prior to this task.

### Observability Assessment for Test-Only Scope

1. **No new production execution paths**: The production method `_select_tree` already implements the guard and error surfacing.
2. **Error propagation observability**: `ui_select` and `_select_tree` surface actionable, distinguishable diagnostics to callers and automated agents via `UiTargetNotInteractableError` (`reason="tree has no model"` vs `reason="item view has no model"`).
3. **Bounded test execution**: Both test modules declare explicit timeout bounds (`pytestmark = [pytest.mark.timeout(60), ...]` in `test_ui_actions.py` and `pytestmark = pytest.mark.timeout(60)` in `test_ui_actions_tree_no_model_mutation.py`) fulfilling NFR-1.
4. **Existing production observability intact**: Existing logging in `pypost/agent/ui_actions.py` (e.g., `ui_action_applied primitive=select widget_id=%s outcome=ok duration_ms=%s` at `DEBUG`) remains untouched and effective.

## Logging Implementation

### Added Logs

No production log statements were added:
- **EMERG**: none — no system-failure path introduced
- **ALERT**: none — no alert condition introduced
- **CRIT**: none — no critical system error path introduced
- **ERR**: none — errors are propagated via `UiTargetNotInteractableError`
- **WARNING**: none — no warning condition introduced
- **NOTICE**: none — no notice condition introduced
- **INFO**: none added — existing `ui_action_applied` logging preserved at DEBUG
- **DEBUG**: none added — `ui_actions.py` existing debug logging preserved

### Log Structure

Log format used:
- Structured logs: N/A (no new log statements added)
- Includes context: N/A (existing logs include widget id, duration, primitive)
- Log levels: none added

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: none added (test suite runs in ~9.8s for `test_ui_actions.py` and ~3.0s for `test_ui_actions_tree_no_model_mutation.py`, bounded by explicit 60s per-test timeout)
- **Throughput**: none — not a throughput-bearing change
- **Error rate**: none — error signaling handled via exceptions

### Business Metrics

Business metrics:
- None — test contract coverage and mutation resistance verification only.

### System Health Metrics

System health metrics:
- **Resource usage**: CPU/Memory minimal during headless Qt test execution; clean teardown via `close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)`.
- **Component status**: QTreeView widget and QApplication lifecycle managed and released in tests.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A (CI test failure on contract breakage acts as notification channel)
- [ ] Log aggregation (ELK, Loki, etc.) — N/A

## Validation Results

Validation results:
- [x] Logs are correctly formatted (existing logging untouched)
- [x] Metrics are collected correctly (N/A — no metrics added)
- [x] Logging works in error scenarios (N/A — error propagation verified via `UiTargetNotInteractableError`)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (N/A)
- [x] Test timeout bounds confirmed (`pytestmark = pytest.mark.timeout(60)`)
- [x] `make test PYTEST_ARGS="tests/test_ui_actions.py tests/test_ui_actions_tree_no_model_mutation.py"` passed (2 files passed, 0 failures)
- [x] `make lint` passed cleanly

## Notes

- Observability for this task is centered on contract error propagation (`UiTargetNotInteractableError(widget_id, "tree has no model")`) and test runtime bounding (`timeout(60)`).
- Adding new logging or telemetry in `_select_tree` was explicitly non-goal to avoid cluttering agent execution loops and modifying locked error contracts.
