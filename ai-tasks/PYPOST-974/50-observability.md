# PYPOST-974: Observability

## Analysis

This task adds a fixture contract test for an error path that already raises
`UiTargetNotInteractableError` with `reason=option index out of range`. No new
logging, metrics, or tracing is required (NFR-4).

## Logging

| Component | Change |
| --- | --- |
| `pypost/agent/ui_actions.py` | None — existing raise path unchanged |
| New test | Asserts actionable substring already present in exception |

## Metrics

None added. Negative-path fixture tests are synchronous and do not emit
business or performance metrics.

## Validation

- Contract test asserts `"option index out of range"` in the exception string,
  matching list/tree observability of the same failure pattern.
- Developer docs (`doc/dev/ui_actions.md`) already document the shared
  `option index out of range` reason for combo/list/tree; Step 8 cites the new
  combo index test.

## Residual Notes

No observability gaps for acceptance criteria. Follow-ups, if any, belong in
`60-tech-debt.md`.
