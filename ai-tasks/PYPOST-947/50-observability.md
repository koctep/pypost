# PYPOST-947: Observability

## Verdict

**N/A for new production telemetry** — existing fill logging unchanged.

## Current state (unchanged)

Successful `ui_fill` emits DEBUG `ui_action_applied` with:

- `primitive=fill`
- `widget_id`
- `outcome=ok`
- `duration_ms`
- `via_key_clicks=true|false` (lowercase)

Fill **text** and per-key **delay** are **never logged** (PYPOST-917 /
NFR3 contract). Positive `delay` values increase wall-clock `duration_ms` on
the keyClicks path but are not emitted as a separate scalar.

## Rationale

- `delay` is harness tuning (paced typing), not a product mode flag.
- Callers who need delay proof use tests or local instrumentation.
- Avoids log cardinality / secret-adjacent timing leaks.

## Regression coverage

- Parametrized `test_ui_action_applied_caplog` still green for both fill modes.
- New smoke test asserts `QTest.keyClicks` receives `delay=42` when requested.

## Follow-up (non-blocker)

Optional caplog or metric for non-default delay — out of scope; ticket only if
operators need audit of paced fills in production harness logs.
