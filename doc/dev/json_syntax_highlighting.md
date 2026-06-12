# JSON syntax highlighting

## Overview

`JsonHighlighter` (`pypost/ui/widgets/json_highlighter.py`) provides syntax coloring for
JSON text in the request body editor (`RequestEditor`) and response viewer (`ResponseView`).
It extends `QSyntaxHighlighter` and runs on each `QTextDocument` block during edit and
`rehighlight()`.

## Regex-based highlighting

`JsonHighlighter` colors tokens with `QRegularExpression` rules. It does not parse JSON
into an AST. Approximate boundaries are sufficient for request/response editing where
invalid JSON is still useful to read.

### Patterns

| Token | Pattern (summary) |
| ----- | ----------------- |
| Keywords | `\b(true|false|null)\b` |
| Numbers | `\b-?(?:0\|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b` |
| Strings | `"[^"\\]*(\\.[^"\\]*)*"` |
| Object keys | `("[^"\\]*(\\.[^"\\]*)*")\s*:` (group 1 colored) |
| Placeholders | `TEMPLATE_PLACEHOLDER_PATTERN` (`{{...}}`) |

### Known limitations

Accepted by design (PYPOST-97):

1. **Per-block scope** — `highlightBlock` receives one line at a time. A string or key
   that spans multiple lines is highlighted independently per line; an opening `"` on one
   line and a closing `"` on the next may not color as a single string.
2. **String escapes** — The string pattern handles common `\"` and `\\` sequences but is
   not a full JSON string lexer. Rare escape forms may leave suffix characters uncolored
   or misclassified.
3. **Object keys** — Keys are matched only when the quoted name and trailing `:` appear
   on the same block. Indented keys on continuation lines may appear as green strings
   instead of purple keys.
4. **Numeric literals** — The number rule targets typical API values (integers, decimals,
   scientific notation). Spec edge cases such as `01` or non-finite literals are not goals.
5. **Nesting depth** — Regex rules do not track `{`/`[` nesting; deeply nested structures
   still color per-token and remain readable for normal payloads.

Upgrading to an incremental JSON lexer would improve edge-case accuracy but add complexity
and per-keystroke cost. Structural validation belongs in `ValidationController` (see
`doc/dev/body_editor_validation.md`).

### Large blocks (PYPOST-101)

Minified JSON may place an entire payload in one `QTextBlock`. String and key regexes scan
the full block on the UI thread, which can stall the app on megabyte-scale lines.

`JsonHighlighter` defines `MAX_HIGHLIGHT_BLOCK_CHARS` (32_768) in
`pypost/ui/widgets/json_highlighter.py`. When `len(text)` exceeds this limit,
`highlightBlock` returns without applying rules. Text remains readable; only syntax colors
are omitted for that block. Pretty-printed JSON (many short lines) is unaffected.

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

- [PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99) — closed PYPOST-11 hardcoded-colors
  debt; theme module and resolver verified
- [PYPOST-102](https://pypost.atlassian.net/browse/PYPOST-102) — duplicate closure confirming
  PYPOST-99 already satisfied "move colors to theme or config"
- Variable hover tooltips: `VariableHoverMixin` in `pypost/ui/widgets/mixins.py`
- Template expressions: `doc/dev/template_expression_functions.md`
