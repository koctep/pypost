# PYPOST-974: Code Cleanup

## Actions Performed

- Added `test_select_combo_index_out_of_range_raises` in
  `tests/test_ui_actions.py` (parametrized `[-1, 3]`), mirroring list/tree
  out-of-range contract tests from PYPOST-942.
- Confirmed new test inherits module `pytestmark` (`timeout(60)`, `agent_e2e`).
- No production code changes; no unused imports or dead code introduced.
- Line length kept within 100 characters; English docstrings.
- Ran focused tests and full `tests/test_ui_actions.py` via `make test`.
- Ran `make lint` on the Python package (no changes under `pypost/`).

## Static Analysis

- `make lint` — clean for this change (test-only; no `pypost/` edits).
- New test follows existing `try`/`finally` teardown and substring asserts.

## Formatting

- Matches surrounding select negative-path tests in `test_ui_actions.py`.

## Quality Check

- Explicit timeout: module `pytest.mark.timeout(60)` covers the new test.
- No merge conflicts.
- No debug prints or commented-out code.

## Residual Notes

None. Cleanup is complete for this test-debt ticket.
