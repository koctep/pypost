# PYPOST-98: Dev Docs

## Updates

- `doc/dev/json_syntax_highlighting.md` — already documents that structural validation
  belongs in `ValidationController` (Regex-based highlighting section).
- `doc/dev/body_editor_validation.md` — canonical reference for JSON body validation
  (no change required).
- `JsonHighlighter` class docstring — added explicit pointer to validation docs.

## Reader path

1. Syntax coloring limits → `json_syntax_highlighting.md`
2. Invalid JSON feedback in the editor → `body_editor_validation.md`
