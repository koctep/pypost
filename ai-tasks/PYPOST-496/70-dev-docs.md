# PYPOST-496 — Developer Documentation

## Summary

Updated `doc/dev/environments_dialog.md` to document the split widget architecture.

## Components

| Module | Role |
| --- | --- |
| `pypost/ui/dialogs/env_dialog.py` | Dialog shell; wires list + variables widgets |
| `pypost/ui/widgets/environments/environment_list_widget.py` | Environment list pane |
| `pypost/ui/widgets/environments/environment_variables_widget.py` | Variables table + MCP |

## Related

- [PYPOST-435](https://pypost.atlassian.net/browse/PYPOST-435) — original debt item proposing this split
- [PYPOST-497](https://pypost.atlassian.net/browse/PYPOST-497) — validation extraction follow-up
