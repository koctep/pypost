# PYPOST-431 — Code Cleanup

> Date: 2026-06-11

## Files Modified

| File | Change |
|------|--------|
| `pypost/ui/widgets/mixins.py` | `globalPos()` → `globalPosition().toPoint()` |
| `pypost/ui/widgets/variable_aware_widgets.py` | `globalPos()` / `pos()` → `globalPosition()` / `position().toPoint()` |

No other files modified for implementation.

## Linting

```bash
.venv/bin/python3 -m flake8 pypost/ui/widgets/mixins.py pypost/ui/widgets/variable_aware_widgets.py
```

Pre-existing flake8 findings may remain; this ticket did not introduce new ones.

## Regression Check

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python3 -m pytest tests/test_variable_hover.py -q
```

All hover tests must pass.

## Style Compliance

- Minimal diff (two one-line replacements).
- UTF-8, LF, no trailing whitespace.
- Matches existing patterns in test helpers (`event.position().toPoint()`).
