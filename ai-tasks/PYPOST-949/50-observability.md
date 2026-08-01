# PYPOST-949: Observability

## Existing signals (unchanged)

Tab-scoped waits route through the same `pypost.agent.ui_wait` poll loop. No new
log lines or metrics.

| Event | When | Fields |
| --- | --- | --- |
| `ui_wait_settled` | Condition met | timing scalars, condition name |
| `ui_wait_timeout` | Budget exhausted | `widget_id`, `actual_text`, `found`, etc. |

`UiWaitTimeoutError.diagnostics` still carries `widget_id` and text mismatch
details regardless of search root (window vs current tab).

## Test observability

Multi-tab red/green test (`test_session_wait_for_text_in_current_tab_after_multi_tab_send`)
asserts:

- Window-scoped wait raises `UiWaitTimeoutError` (proves wrong-tab match).
- Tab-scoped wait succeeds without extra diagnostics wrapper (unit-level).

Harness `wait_response_after_send` unchanged timeout contract (`step`,
`response_excerpt` on failure).

## Deliberately not added

- No log field for `in_current_tab` — call sites are test/harness only; flag is
  boolean and inferable from session state when debugging.
- No metrics counter for tab-scoped waits — low-volume test path.

## Worklog

```
tokens_used: 2500
role: execution
step: 6
step_name: Observability
```
