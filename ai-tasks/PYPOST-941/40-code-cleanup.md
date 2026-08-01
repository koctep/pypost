# PYPOST-941: Code Cleanup

## Changes

- Removed duplicate `_find_tree_index_by_text` from `ui_actions.py`.
- `agent_e2e_tree.py` no longer uses `QStandardItemModel`-specific depth-2 scan.
- Added focused `tests/test_tree_index_walk.py` with module timeout 30s.

## Lint / Format

- `make lint` — clean on touched files.
- No trailing whitespace; line length within 100 chars.

## Notes

- `find_tree_index_by_display_text` is the single implementation; thin wrappers
  preserve error types at boundaries.
