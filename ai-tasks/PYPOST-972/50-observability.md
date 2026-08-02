# PYPOST-972: Observability Implementation

## Scope

Test-only coverage task — no production logging or metrics changes. The
missing-model gate for flat item views is already implemented in
`_select_item_view` (`pypost/agent/ui_actions.py`); Step 4 added a contract test
only.

## Logging Implementation

### Added Logs

No new log statements — test-only task (NFR-4).

Existing production observability for the path under test:

- **ERR** (via exception): `UiTargetNotInteractableError` with actionable
  `reason` (`item view has no model`) and `widget_id` — raised when
  `widget.model()` is `None` before option handling.
- Successful `ui_select` DEBUG `ui_action_applied` scalars unchanged (not
  reached on this error path).

### Log Structure

- Structured logs: N/A (no new logging)
- Includes context: existing exception includes `widget_id` and `reason`
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

- [x] No new logs required — existing error contract covered by Step 4 test
- [x] Metrics N/A
- [x] CI failure output remains actionable (`UiTargetNotInteractableError`
  / `item view has no model` asserted in `tests/test_ui_actions.py`)
- [x] Large data structures are not logged — unchanged
- [x] N/A for production observability documented

## Notes

- Caplog contract (C1–C5) N/A — path raises an exception; no deliberate
  production ERROR log emission added.
- Pytest assertion failure output is the diagnostic surface for maintainers.
