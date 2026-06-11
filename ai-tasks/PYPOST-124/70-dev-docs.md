# PYPOST-124 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-124](https://pypost.atlassian.net/browse/PYPOST-124)

---

## 1. What Changed and Why

`JsonHighlighter` now highlights `{{...}}` template placeholders in JSON body and response
editors. This completes the deferred follow-up from PYPOST-13 variable tooltips: users can
see placeholders visually without hovering.

## 2. Implementation

`pypost/ui/widgets/json_highlighter.py`:

- Imports `TEMPLATE_PLACEHOLDER_PATTERN` from `pypost.core.template_expression_tokenizer`.
- Adds `variable_format` (darkorange, bold).
- After keyword/number/string/key rules, iterates matches and calls `setFormat`.

## 3. Color scheme

| Token kind | Color | Notes |
| ---------- | ----- | ----- |
| `true` / `false` / `null` | darkblue bold | unchanged |
| Numbers | blue | unchanged |
| String values | green | overridden inside placeholders |
| Object keys | purple | unchanged |
| `{{...}}` placeholders | darkorange bold | new |

## 4. Tests

`tests/test_json_highlighter.py`:

- `test_highlights_template_variable_in_string_value`
- `test_highlights_function_expression_placeholder`
- `test_variable_highlight_overrides_string_green`

Run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## 5. Related

- [PYPOST-13](https://pypost.atlassian.net/browse/PYPOST-13) — variable hover tooltips
- [PYPOST-536](https://pypost.atlassian.net/browse/PYPOST-536) — canonical placeholder regex
- `doc/dev/json_syntax_highlighting.md` — maintained dev reference
