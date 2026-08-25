# PYPOST-1176 — Architecture

## Tokenizer split

- `PLAIN_VARIABLE_PATTERN` — strict `{{name}}` (no inner whitespace); used by `is_plain_variable_token`.
- `LOOSE_PLAIN_VARIABLE_PATTERN` — optional whitespace for hover resolution only.
- `VariableHoverResolver.resolve_text` uses loose matching so `{{ SECRET_TOKEN }}` still masks secrets.

## Test hygiene

Shared `qapp` fixture in `tests/conftest.py` (module scope) replaces per-file duplicates.
