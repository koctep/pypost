# PYPOST-940: Code Cleanup

## Changes Reviewed

- `tests/helpers/qt_item_view.py` — new shared teardown module (≤30 LOC).
- `tests/test_ui_actions.py` — removed duplicate `_close_tree_fixture` /
  `_close_list_view_fixture`; imports `close_item_view_fixture`.
- `tests/test_qt_item_view_teardown.py` — helper unit proofs.

## Cleanup Actions

- No dead code left in `test_ui_actions.py` after helper extraction.
- Line length ≤ 100; LF / UTF-8; module timeout markers present.
- `make lint` clean on touched files (no production code changed).

## Self-Review

- [x] Static analysis clean
- [x] Formatting / line length
- [x] Tests green with explicit timeouts
- [x] Cleanup report written
