# PYPOST-739: Observability

## Error-Path Observability

This task documents how logging and user alerts relate — it does not add metrics or new log
events.

### Pattern → observability sink

| Pattern | Log sink | User sink | Metrics |
| --- | --- | --- | --- |
| Log-only | `logger.error` / `warning` | Status bar or degraded UI (optional) | Sometimes (e.g. GUI action outcome) |
| Log + dialog | Same, before dialog | `collection_item_dialogs` QMessageBox | Often on presenter action |
| Silent pass | Usually none; `debug` optional | None | None |

### Logging conventions

- Prefer **`logger.exception`** when handling unexpected `Exception` (includes stack trace).
- Use **`logger.error("event_name key=%s", value)`** for expected failure categories.
- Event names follow [logging.md](../../doc/dev/logging.md) — snake_case first token.

### Gaps (unchanged by this task)

- No correlation ID between log line and dialog text (acceptable for desktop app — O-003).
- Not all legacy handlers use structured event names; migrate when touching files (PYPOST-747).
- Direct `QMessageBox` outside `collection_item_dialogs` remains in a few modules (tech debt).

## Verification

- [x] Three patterns mapped to log and UI sinks
- [x] Cross-reference to logging convention doc
- [x] No new runtime instrumentation required
