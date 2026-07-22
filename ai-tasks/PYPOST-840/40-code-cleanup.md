# PYPOST-840: Code Cleanup

## Actions

- Confirmed no local `_wait_until` remains in `pypost.agent.lifecycle`.
- Confirmed `tests.helpers.qt_wait` is a thin re-export (no second loop body).
- Added focused lock module; no drive-by refactors in unrelated agent modules.
- Artifacts kept under `ai-tasks/PYPOST-840/` only for this debt close-out.

## Checklist

- [x] No unused duplicate wait helper in agent lifecycle
- [x] Line length / typing consistent with existing agent modules
- [x] Tests follow `.cursor/lsr/do-testing.md` timeout rules
