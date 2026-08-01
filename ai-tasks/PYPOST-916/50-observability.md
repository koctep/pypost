# PYPOST-916: Observability

## Requirements Analysis

Select remains an in-process agent harness primitive. Critical path is
successful/failed `ui_select` after ready. No new Prometheus series required
(same posture as PYPOST-836 / PYPOST-851).

## Logging Added / Reused

| Event | Level | Scalars | Notes |
| --- | --- | --- | --- |
| `ui_action_applied` | DEBUG | `primitive=select`, `widget_id`, `outcome=ok`, `duration_ms` | Unchanged format; still **no** option text/index in the message (NFR3) |

Failures continue to surface as `UiTargetNotFoundError` /
`UiTargetNotInteractableError` with `widget_id=` and `reason=` in the
exception string (not a separate ERROR log line), matching existing action
primitives.

## Metrics

None added. Harness actions are not production request traffic.

## Validation

- Existing `test_ui_action_applied_caplog` still asserts DEBUG scalars and
  absence of fill body text.
- List/tree success paths emit the same `ui_action_applied` DEBUG line as
  combo select.

## Self-Review (50-observability.mdc)

- [x] Key path covered by existing structured DEBUG event
- [x] No large payloads / option labels in logs
- [x] Documented in this file
