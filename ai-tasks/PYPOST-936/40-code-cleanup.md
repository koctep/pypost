# PYPOST-936: Code Cleanup

## Changes

- Extracted duplicated timer/rewrap/dismiss blocks from
  `tests/test_agent_dialog_settle_e2e.py` into
  `tests/helpers/agent_e2e_dialog_settle.py`.
- Removed unused imports (`QTimer`, `QApplication`) from the test module;
  Settings predicate keeps a local `QApplication` import inside the function.
- Added `tests/test_agent_dialog_settle_convention.py` to lock helper adoption
  (mirrors PYPOST-948 Send settle convention).

## Intentional local code

| Item | Location | Reason |
| --- | --- | --- |
| `_settings_dialog_present()` | test module | Settings-specific predicate |
| `SETTLE_STEP`, timeout constants | test module | Scenario contract |
| Test assertions | test module | Proof-specific |

## No further cleanup required

Helper is ~80 lines, single responsibility, matches `agent_e2e_send_settle`
precedent. No dead code or unused exports.
