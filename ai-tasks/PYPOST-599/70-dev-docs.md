# PYPOST-599: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| `doc/dev/hotkeys.md` | **New** — registration helpers, properties, dialog collection |
| `doc/dev/solid_audit.md` | `hotkeys_dialog.py` finding resolved (dynamic collection) |
| `doc/dev/tech-debt/PYPOST-11.md` | Item #2 marked addressed by PYPOST-599 |

## Developer notes

When adding or changing a global shortcut:

1. Use `register_hotkey` or `tag_action` from `pypost/ui/hotkeys.py`.
2. Set `section`, `order`, and optional `label` for help display.
3. For multiple keys to one handler, pass all keys to `register_hotkey`.
4. For multiple keys to different handlers with one help row, use `register_hotkey_group`.
5. No edit to `hotkeys_dialog.py` is required.

See `doc/dev/hotkeys.md` for API summary.
