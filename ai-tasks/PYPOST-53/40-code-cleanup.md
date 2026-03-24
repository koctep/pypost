# PYPOST-53: Code Cleanup

## Summary

Context menu **Copy** on the Manage Environments list duplicates an environment with
validation and logging. Pure clone logic lives in `pypost/core/environment_ops.py`.

## Files Changed

| File | Action |
|---|---|
| `pypost/ui/dialogs/env_dialog.py` | Context menu, duplicate flow |
| `pypost/core/environment_ops.py` | New — `clone_environment` |
| `tests/test_environment_ops.py` | New — unit tests |

## Cleanup Items Applied

- Imports grouped (stdlib, third party, local); line length within 100 characters.
- LF endings; no trailing whitespace; single final newline per file.
- English identifiers and log messages.

## Test execution (venv)

**Always run tests with the project virtualenv**, not the system interpreter:

- `make test` — uses `.venv/bin/python` and `QT_QPA_PLATFORM=offscreen` (see
  [Makefile](Makefile)).
- Or explicitly: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/`

Create the venv and install deps once: `make install`.

## Test Run Results

- `make test`: 125 passed (includes `tests/test_environment_ops.py`).
