# PYPOST-99 — Developer Documentation

> Date: 2026-06-12
> Parent: [PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99)

---

## 1. What Changed and Why

PYPOST-99 closes the PYPOST-11 hardcoded-colors debt. JsonHighlighter foreground colors
live in `pypost/ui/theme/json_syntax_theme.py` (`JsonSyntaxColors`, light/dark palettes,
`resolve_json_syntax_colors`). The highlighter accepts optional `colors` and supports
`set_colors` for runtime rebinding when settings change.

## 2. Key APIs

```python
from pypost.ui.theme.json_syntax_theme import (
    DEFAULT_JSON_SYNTAX_COLORS,
    DARK_JSON_SYNTAX_COLORS,
    resolve_json_syntax_colors,
)

JsonHighlighter(document)  # resolves palette at construction
highlighter.set_colors(resolve_json_syntax_colors())
```

## 3. Tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## 4. Related

- [PYPOST-11](https://pypost.atlassian.net/browse/PYPOST-11) — original epic debt source
- [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398) — theme extraction
- [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395) — dark palette + resolver
- `doc/dev/json_syntax_highlighting.md` — maintained dev reference
