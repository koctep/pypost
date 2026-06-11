# JSON syntax highlighting

## Overview

`JsonHighlighter` (`pypost/ui/widgets/json_highlighter.py`) provides syntax coloring for
JSON text in the request body editor (`RequestEditor`) and response viewer (`ResponseView`).
It extends `QSyntaxHighlighter` and runs on each `QTextDocument` block during edit and
`rehighlight()`.

## Highlighted elements

Colors are defined in `pypost/ui/theme/json_syntax_theme.py` as `JsonSyntaxColors` and
applied by `JsonHighlighter`. Light-theme defaults (`DEFAULT_JSON_SYNTAX_COLORS`):

| Pattern | Color field | Default | Weight |
| ------- | ----------- | ------- | ------ |
| `true`, `false`, `null` | `keyword` | darkblue | bold |
| Numeric literals | `number` | blue | normal |
| Quoted strings | `string` | green | normal |
| Object keys (`"key":`) | `key` | purple | normal |
| Template placeholders `{{...}}` | `placeholder` | darkorange | bold |

Dark-theme palette (`DARK_JSON_SYNTAX_COLORS`) uses lighter hex colors for readability on
dark backgrounds. `resolve_json_syntax_colors()` picks light or dark based on the application
`QPalette` window lightness (`is_dark_palette()`). `TabsPresenter.apply_settings` refreshes
highlighter colors on open tabs when settings are applied.

Placeholder detection uses `TEMPLATE_PLACEHOLDER_PATTERN` from
`pypost.core.template_expression_tokenizer` — the same regex as template expression parsing
and hover preview (PYPOST-536). Plain variables (`{{host}}`) and function expressions
(`{{urlencode(db)}}`) are highlighted identically.

## Rule order

Rules apply in sequence; later formats overwrite overlaps on the same span:

1. Keywords, numbers, generic strings
2. Object keys (string before `:`)
3. Template placeholders

Placeholders inside JSON string values are first colored green, then overridden to
darkorange for the full `{{...}}` token.

## Wiring

```python
from pypost.ui.theme.json_syntax_theme import (
    DARK_JSON_SYNTAX_COLORS,
    resolve_json_syntax_colors,
)

JsonHighlighter(self.body_edit.document())  # resolves palette at construction
JsonHighlighter(self.body_view.document())

# Runtime rebinding (used by TabsPresenter.apply_settings):
highlighter.set_colors(resolve_json_syntax_colors())

# Explicit palette override:
JsonHighlighter(document, colors=DARK_JSON_SYNTAX_COLORS)
```

`RequestEditor` and `ResponseView` construct `JsonHighlighter` without `colors`, so the
active palette is resolved automatically. Call `set_colors` to refresh after palette changes.

## Testing

`tests/test_json_highlighter.py` asserts foreground colors via `QTextBlock.layout().formats()`
because `QTextCursor.charFormat()` ignores `QSyntaxHighlighter` ranges.

JSON syntax coverage includes keywords (`true`/`false`/`null`), integers and floats (including
zero and scientific notation), string values, object keys, array strings, escaped characters
inside strings, and multiline documents. Template placeholder tests cover plain variables and
function expressions overriding string green.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## Related

- Variable hover tooltips: `VariableHoverMixin` in `pypost/ui/widgets/mixins.py`
- Template expressions: `doc/dev/template_expression_functions.md`
