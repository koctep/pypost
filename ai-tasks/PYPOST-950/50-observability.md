# PYPOST-950: Observability Implementation

## Logging Implementation

### Added Logs

None. Test-harness alignment only; no production logging changes.

### Log Structure

N/A — existing `wait_for_text` timeout diagnostics unchanged in
`pypost/agent/ui_wait.py`.

## Metrics Implementation

N/A — no new metrics.

## Harness observability (test path)

The golden timeout companion now exercises the same diagnostic carrier as
happy-path Send settle:

| Field | Source | Purpose |
| --- | --- | --- |
| `step` | Test wrap | `wait_response_after_send` triage fingerprint |
| `response_excerpt` | `response_panel_excerpt(ui_snapshot())` | Panel context on failure |
| `widget_id` | Inner `wait_for_text` timeout | Confirms text-wait path (PYPOST-950) |
| `expected` | Inner `wait_for_text` timeout | Shows mismatched label (`Status: 999`) |
| `actual_text` | Inner `wait_for_text` timeout | May show arrived status when response is fast |

Replacing `wait_for_snapshot` removes snapshot-only keys (`node_count`,
`named_count`) from the forced-timeout lock — intentional; triage should use
text-wait fingerprints consistent with production settle helpers.

## Monitoring Integration

N/A.

## Validation Results

Validation results:

- [x] Forced-timeout test asserts `widget_id` and `expected` in diagnostics
- [x] `step` and `response_excerpt` preserved through wrap
- [x] No large structures logged on success

## Notes

Primary observability for this task is pytest failure output from
`test_agent_golden_settle_timeout_includes_step_and_excerpt`, not new
production instrumentation.
