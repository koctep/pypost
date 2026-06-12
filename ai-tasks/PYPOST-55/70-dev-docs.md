# PYPOST-55: Dev Docs (Step 7)

## Updates

| Document | Change |
| --- | --- |
| [doc/dev/environments_dialog.md](../../doc/dev/environments_dialog.md) | Document `environment_messages` module |
| [pypost/core/environment_messages.py](../../pypost/core/environment_messages.py) | New constants module (inline docstring) |

## Developer notes

- Import user-visible environment strings from `pypost.core.environment_messages`.
- Use formatter helpers for messages with dynamic names (`format_copy_of_name`, etc.).
- Tests: `tests/test_environment_messages.py`, rename cases in `tests/test_environment_ops.py`.
- Qt coverage unchanged: `tests/test_env_dialog.py`.

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: 500
