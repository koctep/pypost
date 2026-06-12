# PYPOST-64: Code Cleanup

## Changes

- Added `QSizePolicy` import to `history_panel.py`.
- Removed fixed-height constraints on detail `QTextEdit` widgets.

## Verification

- `make test` targeted: `tests/test_history_panel.py` passes.
- No new flake8 violations in modified files.
