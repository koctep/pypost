# PYPOST-939: Observability

## Existing Signals

- Successful `ui_select` continues to emit DEBUG `ui_action_applied` with
  scalars only: `primitive=select`, `widget_id`, `outcome=ok`, `duration_ms`.
- No option text or model payload logged (NFR3 preserved).

## New Paths

- `QListView` / flat `QAbstractItemView` branch uses the same log line after
  `_pump()` — no new metrics or log fields required.

## Verification

- Existing `test_ui_action_applied_caplog` covers fill; select logging contract
  unchanged from PYPOST-916. No additional caplog test needed for this debt.
