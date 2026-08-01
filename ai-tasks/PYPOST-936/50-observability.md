# PYPOST-936: Observability

## Verdict

**N/A for new production observability** — test-only refactor.

## Preserved behavior

| Surface | Status |
| --- | --- |
| `UiWaitTimeoutError.diagnostics["step"]` | Unchanged — `SETTLE_STEP` passed through helper |
| Modal scalars (`dialog_title`, `dialog_object_name`, `active_modal_type`) | Unchanged — `modal_diag()` in helper |
| DEBUG `ui_wait_settled` / `ui_wait_timeout` | Unchanged — same `wait_until` calls |
| Fail-closed `reject()` | Unchanged — helper `finally` block |

## Regression signal

- Happy-path proof still asserts settle success.
- Timeout companion still asserts step + modal scalar keys.
- Convention test locks helper usage for future proofs.

No new metrics, log events, or production tracing required.
