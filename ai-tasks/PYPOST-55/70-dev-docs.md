# PYPOST-55: Dev Docs

## Updated

- `doc/dev/environments_dialog.md` — documents `environment_messages` module and string
  ownership.

## Key points for developers

1. Add or change user-visible environment manager text in `pypost/core/environment_messages.py`.
2. Use `format_*` helpers when messages include dynamic names.
3. Do not reintroduce literals in widgets; import constants from the module above.
