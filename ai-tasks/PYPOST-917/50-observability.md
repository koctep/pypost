# PYPOST-917: Observability

## Requirements Analysis

Optional fill-via-keyClicks remains an in-process agent harness primitive.
Critical path is successful `ui_fill` (default setters or opt-in keyClicks)
after ready. No new Prometheus series required (same posture as PYPOST-851 /
PYPOST-916).

## Logging Added / Reused

| Event | Level | Scalars | Notes |
| --- | --- | --- | --- |
| `ui_action_applied` | DEBUG | `primitive=fill`, `widget_id`, `outcome=ok`, `duration_ms`, `via_key_clicks` | Same event as PYPOST-851; new boolean scalar (`true`/`false` lowercase). Fill **text is never logged** (NFR3). |

Emitted once after a successful fill, for both code paths (setters and
`QTest.keyClicks`). Location: `pypost/agent/ui_actions.py` `ui_fill`.

Example shapes:

```text
ui_action_applied primitive=fill widget_id=... outcome=ok
  duration_ms=... via_key_clicks=false
ui_action_applied primitive=fill widget_id=... outcome=ok
  duration_ms=... via_key_clicks=true
```

Failures continue to surface as `UiTargetNotFoundError` /
`UiTargetNotInteractableError` with `widget_id=` and `reason=` in the
exception string (not a separate ERROR log line), matching existing action
primitives.

## Metrics

None added. Harness actions are not production request traffic.

## Validation

- `test_ui_action_applied_caplog` asserts DEBUG scalars including
  `via_key_clicks=false` and absence of fill body text (default path).
- Opt-in path (`via_key_clicks=True`) uses the same `logger.debug` call with
  `str(via_key_clicks).lower()`; no separate True-path caplog test — green
  fill tests already exercise that branch, and the log line cannot omit or
  redact the scalar differently from the false path.
- Large payloads / fill text are not logged.

## Self-Review (50-observability.mdc)

- [x] Key path covered by structured DEBUG event with mode scalar
- [x] No large payloads / fill text in logs
- [x] Documented in this file
