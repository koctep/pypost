# PYPOST-942: Observability Implementation

## Scope

Test-only coverage task — no production logging or metrics changes. List and tree
negative-path error behavior is already implemented in `_select_list` /
`_select_tree` (`pypost/agent/ui_actions.py`); Step 4 added contract tests only.

## Logging Implementation

### Added Logs

No new log statements — test-only task.

Existing production observability for the paths under test:

- **ERR** (via exception): `UiTargetNotInteractableError` with actionable
  `reason` (`option not found: …` / `option index out of range: …`) and
  `widget_id` — raised by `_select_list` / `_select_tree` when select fails.

### Log Structure

- Structured logs: N/A (no new logging)
- Includes context: existing exceptions include `widget_id` and `reason`
- Log levels: none added

## Metrics Implementation

Not applicable — test-only task; no metrics changes.

### Performance Metrics

N/A

### Business Metrics

N/A

### System Health Metrics

N/A

## Monitoring Integration

- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

## Validation Results

- [x] No new logs required — existing error contract covered by Step 4 tests
- [x] Metrics N/A
- [x] CI failure output remains actionable (`UiTargetNotInteractableError`
  substrings asserted in `tests/test_ui_actions.py`)
- [x] Large data structures are not logged — unchanged
- [x] N/A for production observability documented

## Notes

- Negative-path tests mirror `test_select_missing_option_raises`; pytest output
  on failure is the diagnostic surface for harness authors.
- No DEBUG scalars or teardown logging added — fixtures follow established
  `try`/`finally` teardown in `tests/test_ui_actions.py`.
