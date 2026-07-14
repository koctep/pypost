# PYPOST-794: Code Cleanup

## Changes Reviewed

- `Makefile` only — no Python source touched.
- Help implementation is a single `grep | awk` pipeline; no duplicated target lists.
- Descriptions are concise and match existing comment intent where comments existed.

## Cleanup Actions

- Removed redundant standalone comment blocks above targets where `##` descriptions now serve
  the same purpose (e.g. "Create virtual environment" inline on `venv:`).
- Kept `$(VENV_MARKER)` rule without `##` — internal implementation detail, excluded from help.
- Added `help` to `.PHONY` alongside existing phony targets.

## Result

No dead code, no formatting issues. Makefile remains under 100 lines.
