# PYPOST-431 — Observability

> Date: 2026-06-11

## 1. Application Runtime

No new log lines, metrics, or traces.  Tooltip behaviour is unchanged; only the
coordinate API used for `QToolTip.showText` is updated.

## 2. Test Observability Impact

### Before

`pytest tests/test_variable_hover.py` emitted `DeprecationWarning` from production
code calling `QMouseEvent.globalPos()`, adding noise to CI logs and local runs.

### After

Production hover paths use `globalPosition().toPoint()`.  The `globalPos`
deprecation warning from `mixins.py` and `variable_aware_widgets.py` is eliminated.

### Remaining warnings (out of scope)

Test code and some widgets may still use `event.pos()` (deprecated separately).
Track in follow-up debt items if warning noise persists.

## 3. CI Signals

No workflow changes.  Existing pytest verbosity, junit, and coverage reporting
unchanged.  Cleaner warning output improves signal-to-noise in test logs.
