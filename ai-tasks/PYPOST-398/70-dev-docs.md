# PYPOST-398 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398)

---

## 1. What Changed and Why

Moved JsonHighlighter foreground colors from inline literals in
`pypost/ui/widgets/json_highlighter.py` to `pypost/ui/theme/json_syntax_theme.py`.
Enables future theme variants (PYPOST-395) without editing highlighter regex logic.

## 2. Theme API

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class JsonSyntaxColors:
    keyword: str = "darkblue"
    number: str = "blue"
    string: str = "green"
    key: str = "purple"
    placeholder: str = "darkorange"

DEFAULT_JSON_SYNTAX_COLORS = JsonSyntaxColors()
```

`JsonHighlighter(document, colors=None)` uses `DEFAULT_JSON_SYNTAX_COLORS` when `colors`
is omitted.

## 3. Tests

- Existing default-color tests unchanged.
- `test_custom_theme_colors_are_applied` verifies injectable palette.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## 4. Related

- [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9) — original JsonHighlighter epic
- [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395) — dark-theme palette
- `doc/dev/json_syntax_highlighting.md` — maintained dev reference
