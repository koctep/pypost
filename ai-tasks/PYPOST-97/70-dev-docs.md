# PYPOST-97: Developer Documentation

## What Changed

Documented regex-based JSON highlighting limitations on `JsonHighlighter` and in dev docs.
Debt from PYPOST-11 is closed as an accepted trade-off for `QSyntaxHighlighter` block
coloring.

---

## Files Modified

| File | Change |
| --- | --- |
| `pypost/ui/widgets/json_highlighter.py` | Class docstring: approach, limitations, doc pointer |
| `doc/dev/json_syntax_highlighting.md` | Regex patterns table and known limitations section |

---

## Reading Order

1. IDE hover on `JsonHighlighter` — quick summary of regex approach and limits.
2. `doc/dev/json_syntax_highlighting.md` — patterns, rule order, limitations, tests.

---

## Verification

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```
