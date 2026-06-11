# PYPOST-395 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395)

---

## 1. What Changed and Why

Added dark-theme JSON syntax colors and palette-based resolution on top of PYPOST-398's
`JsonSyntaxColors` module. JsonHighlighter now auto-selects light or dark colors and supports
runtime rebinding when settings are applied.

## 2. Theme API

```python
DARK_JSON_SYNTAX_COLORS = JsonSyntaxColors(
    keyword="#79c0ff",
    number="#56d4dd",
    string="#7ee787",
    key="#d2a8ff",
    placeholder="#ffa657",
)

resolve_json_syntax_colors(dark: bool | None = None) -> JsonSyntaxColors
is_dark_palette(palette: QPalette | None = None) -> bool
```

`JsonHighlighter(document, colors=None)` calls `resolve_json_syntax_colors()` when `colors`
is omitted. `set_colors(colors)` rebuilds rules and calls `rehighlight()`.

## 3. Wiring

`TabsPresenter.apply_settings` resolves colors once and calls `set_colors` on each open tab's
`request_editor.json_highlighter` and `response_view.json_highlighter`.

## 4. Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

New cases: `test_dark_palette_colors_are_applied`, `test_resolve_json_syntax_colors_returns_light_by_default`,
`test_set_colors_rebinds_highlighting`.

## 5. Related

- [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9) — JsonHighlighter epic
- [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398) — theme color extraction
- `doc/dev/json_syntax_highlighting.md` — maintained dev reference
