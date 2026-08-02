# PYPOST-973: Code Cleanup

## Static Analysis

- `make lint` (flake8 on `pypost/`) — clean.
- Focused pytest for teardown + collections-tree consumers — 32 passed.
- Import order in rename-delegate e2e fixed (alphabetical helper imports).

## Formatting

- Line length ≤100 observed in new helpers and docs.
- No trailing whitespace introduced.

## Cleanup Performed

- Added `close_isolated_tree_actions` and `isolated_tree_actions` only;
  no duplicate local `setModel(None)`.
- Migrated all `build_isolated_tree_actions` owners to
  `self.addCleanup(close_isolated_tree_actions, harness)`.
- Extended `tests/test_qt_item_view_teardown.py` with two PYPOST-973 proofs
  (both have module `pytestmark = timeout(30)`).

## Quality Check

| Check | Result |
| --- | --- |
| Focused tests green | Yes (32) |
| Explicit timeouts | Yes (module pytestmark) |
| Unused imports | None in changed helpers |
| Production code touched | No |

## Remaining Notes

None blocking.
