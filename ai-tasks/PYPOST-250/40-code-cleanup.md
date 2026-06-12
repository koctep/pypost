# PYPOST-250 — Code Cleanup

> Date: 2026-06-12

## Files Modified

| File | Change |
|------|--------|
| `pypost/ui/widgets/mixins.py` | Generic mixin typing; `QMouseEvent` hints; removed `type: ignore` |

## Linting

```bash
make lint
```

Scoped check:

```bash
.venv/bin/python3 -m flake8 pypost/ui/widgets/mixins.py
```

## Regression Check

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python3 -m pytest tests/test_variable_hover.py -q
```

## Style Compliance

- UTF-8, LF, line length ≤ 100 characters.
- Matches existing typing imports (`typing` module, explicit return types).
