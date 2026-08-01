# PYPOST-988: Code Cleanup

## Lint / format

- Ran `make lint` on touched files — clean.
- No lambda-assignment issues in new tests.

## Tests

- `tests/test_environment_export.py` — 10 pure-logic tests including import round-trip.
- `tests/test_environment_export_ui.py` — 7 Qt-level export orchestration tests.
- `pytestmark = pytest.mark.timeout(60)` on both modules.

## Worklog

tokens_used: 3000
role: execution
step: 5
step_name: Code Cleanup
