# PYPOST-164: Observability

## Summary

No observability changes. Context menu paths in `ResponseView` do not emit metrics or structured
logs today; this task adds test coverage only.

## Existing Behavior (unchanged)

- `show_context_menu` does not call `MetricsTrackerProtocol`.
- No new log lines introduced.

## Verification

Tests assert signal emission and menu wiring only; no metric or log assertions required.
