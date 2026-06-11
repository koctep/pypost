# PYPOST-399: Architecture — JsonHighlighter test coverage

## Summary

Extend `tests/test_json_highlighter.py` only. Reuse the existing `_hex_color_at` helper and
`_edit_with_highlighted` fixture pattern from PYPOST-103/PYPOST-124. No changes to
`JsonHighlighter` or editor wiring.

## Design

### Test harness (unchanged)

| Helper | Role |
| ------ | ---- |
| `_hex_color_at(doc, position)` | Read foreground hex from `QTextBlock.layout().formats()` |
| `_edit_with_highlighted(text)` | Attach highlighter, set text, `rehighlight()` |

### New test cases

| Test | Input snippet | Assert position | Expected color |
| ---- | ------------- | --------------- | -------------- |
| Integer | `{"count": 42}` | `4` in `42` | blue |
| Zero | `{"n": 0}` | `0` digit | blue |
| Scientific | `{"x": 1.5e10}` | digit in mantissa/exponent | blue |
| Array string | `["item"]` | `i` in `item` | green (not purple) |
| Escaped string | `{"m": "a\"b"}` | char inside quotes | green |
| Combined syntax | multi-token JSON | per-token positions | keyword/number/string/key |

### Files

| File | Change |
| ---- | ------ |
| `tests/test_json_highlighter.py` | Add 5–6 JSON syntax tests; update module docstring |
| `doc/dev/json_syntax_highlighting.md` | List new tests under Testing |

### Out of scope

- New test modules or shared fixtures outside this file.
- Parametrized color table (keep explicit tests for readability).

## Verification

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```
