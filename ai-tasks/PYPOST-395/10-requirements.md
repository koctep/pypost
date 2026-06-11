# PYPOST-395: Dark-theme JSON syntax palette

## Context

- Parent epic: [PYPOST-9](https://pypost.atlassian.net/browse/PYPOST-9) — JsonHighlighter.
- [PYPOST-398](https://pypost.atlassian.net/browse/PYPOST-398) moved colors to
  `json_syntax_theme.py`; hardcoded literals no longer live in the highlighter widget.
- Remaining debt: no dark-background palette and no runtime theme coordination.

## Problem

Default JSON syntax colors (`darkblue`, `blue`, `green`, `purple`) are tuned for light
editor backgrounds. On a dark palette they lose contrast. Users switching to a dark system
or future app theme need readable syntax colors without editing widget code.

## Goals

- Provide a dark-theme `JsonSyntaxColors` palette with sufficient contrast on dark backgrounds.
- Resolve light vs dark colors from the application `QPalette` (same approach as gutter
  colors in `CodeEditor`).
- Allow runtime rebinding when settings are applied (open tabs refresh colors).
- Keep light-theme defaults and existing tests stable.

## Functional requirements

1. **FR-1:** `DARK_JSON_SYNTAX_COLORS` defines all five token classes for dark backgrounds.
2. **FR-2:** `resolve_json_syntax_colors()` returns light or dark palette based on palette
   lightness when `dark` is not specified.
3. **FR-3:** `JsonHighlighter` uses the resolver when `colors` is omitted.
4. **FR-4:** `JsonHighlighter.set_colors()` rebuilds formats and re-highlights.
5. **FR-5:** `TabsPresenter.apply_settings` updates JSON highlighters on open request tabs.

## Acceptance criteria

1. **AC-1:** No color string literals in `json_highlighter.py` beyond `JsonSyntaxColors` fields.
2. **AC-2:** All `tests/test_json_highlighter.py` cases pass.
3. **AC-3:** Tests cover dark palette application and `set_colors` rebinding.
4. **AC-4:** `doc/dev/json_syntax_highlighting.md` documents dark palette and resolver.

## Out of scope

- `AppSettings` theme toggle or settings UI.
- QSS dark stylesheet (StyleManager remains QSS-only).
- User-configurable per-token colors in settings.

## Assumptions

- Light palette remains the product baseline when `QPalette.Window` lightness ≥ 128.
- Hex colors in `DARK_JSON_SYNTAX_COLORS` are stable API for tests and docs.
