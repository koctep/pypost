# PYPOST-399 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-399](https://pypost.atlassian.net/browse/PYPOST-399)

---

## 1. What Changed and Why

Extended `tests/test_json_highlighter.py` with explicit JSON syntax cases (integers, zero,
scientific notation, array strings, escaped strings, combined document). Closes the
PYPOST-9 follow-up for missing `JsonHighlighter` unit tests beyond variable highlighting.

## 2. New tests

| Test | Covers |
| ---- | ------ |
| `test_highlights_integer_number` | Positive integer literals |
| `test_highlights_zero_number` | Zero literal |
| `test_highlights_scientific_notation_number` | `e`/`E` exponent form |
| `test_highlights_array_string_green_not_purple` | Non-key quoted strings |
| `test_highlights_escaped_characters_in_string` | Escaped quote inside value |
| `test_combined_json_syntax_colors` | Keywords, key, string, number in one doc |

## 3. Run

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## 4. Related

- [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9) — original JsonHighlighter epic
- [PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124) — placeholder highlighting tests
- `doc/dev/json_syntax_highlighting.md` — maintained dev reference
