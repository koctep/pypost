# PYPOST-947: Dev Docs

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/ui_actions.md` | `delay` kwarg on opt-in keyClicks fill; session mirror |
| `doc/dev/testing.md` | Delay forwarding smoke test cross-ref |

## Unchanged (still accurate)

| File | Note |
| --- | --- |
| `doc/dev/logging.md` | Fill row documents `via_key_clicks` only; delay not logged |

## Cross-links added

- API / Usage — `ui_fill` signature and mode table include `delay`
- Troubleshooting — paced keyClicks via `delay`
- Testing — `test_ui_fill_via_key_clicks_forwards_delay_kwarg` (PYPOST-947)

## Verification

Docs describe keyword-only `delay: int = -1`, keyClicks-path-only semantics,
and Qt default when omitted.
