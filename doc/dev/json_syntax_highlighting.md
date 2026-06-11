# JSON syntax highlighting

## Overview

`JsonHighlighter` (`pypost/ui/widgets/json_highlighter.py`) provides syntax coloring for
JSON text in the request body editor (`RequestEditor`) and response viewer (`ResponseView`).
It extends `QSyntaxHighlighter` and runs on each `QTextDocument` block during edit and
`rehighlight()`.

## Highlighted elements

| Pattern | Color | Weight |
| ------- | ----- | ------ |
| `true`, `false`, `null` | darkblue | bold |
| Numeric literals | blue | normal |
| Quoted strings | green | normal |
| Object keys (`"key":`) | purple | normal |
| Template placeholders `{{...}}` | darkorange | bold |

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
JsonHighlighter(self.body_edit.document())   # RequestEditor
JsonHighlighter(self.body_view.document())    # ResponseView
```

No configuration surface — colors are fixed for the default light editor theme. Dark-theme
support is tracked separately (PYPOST-395).

## Testing

`tests/test_json_highlighter.py` asserts foreground colors via `QTextBlock.layout().formats()`
because `QTextCursor.charFormat()` ignores `QSyntaxHighlighter` ranges.

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_json_highlighter.py -q
```

## Related

- Variable hover tooltips: `VariableHoverMixin` in `pypost/ui/widgets/mixins.py`
- Template expressions: `doc/dev/template_expression_functions.md`
