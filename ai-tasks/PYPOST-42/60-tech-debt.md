# PYPOST-42: Technical Debt Analysis

## Code Review Summary

**Reviewed:** `pypost/ui/widgets/request_editor.py`, `pypost/core/metrics.py`,
`tests/test_request_editor_method_tab_switch.py`

### request_editor.py

- **Correctness:** `_loading` guard correctly prevents auto-switch during `load_data`.
  `try/finally` ensures flag is always reset.
- **Signal safety:** Explicit `_on_method_changed` call in `load_data` is necessary:
  Qt's `currentTextChanged` does not fire when the value is unchanged, so the explicit
  call covers the case where the method stays the same across loads.
- **Lint:** `flake8 --max-line-length=100` passes. No violations introduced.

### metrics.py

- **Pre-existing E501 violations** (lines 6, 90, 138, 163, 177, 206, 261, 264, 280)
  when running `flake8` without config. These are pre-existing and exceed 79 chars but
  comply with the project's 100-char limit. No flake8 config file exists to enforce
  project limit. **Low priority — add a `.flake8` config.**
- **New counter** `gui_method_body_autoswitches_total` is consistent with existing
  counter naming conventions (`gui_*_total`).

### tests

- 8 tests added covering POST/PUT switch, non-switching methods, and load_data guard.
- Tests use `unittest` + bare `QApplication` — consistent with rest of test suite.
- `QT_QPA_PLATFORM=offscreen` required for headless environments. Not encoded in
  Makefile `test` target. **Low priority — add env var to Makefile.**

## Shortcuts Taken

None. All requirements implemented as designed.

## Code Quality Issues

| Issue | Severity | File | Notes |
|-------|----------|------|-------|
| No `.flake8` config | Low | project root | E501 pre-existing; affects whole codebase |
| `QT_QPA_PLATFORM` not in Makefile `test` | Low | `Makefile` | UI tests fail in CI without it |
| HTTP method strings not constants | Low | multiple | Pre-existing pattern; tracked since PYPOST-40 audit |

## Missing Tests

- No test verifying that the Prometheus counter increments on auto-switch. Would require
  resetting `MetricsManager` singleton between tests — non-trivial. Low priority.

## Performance Concerns

None. The auto-switch is a single `setCurrentWidget` call on a UI event; negligible cost.

## Follow-up Tasks

1. ~~Add `.flake8` config with `max-line-length = 100` to project root.~~ **Done.**
2. ~~Add `QT_QPA_PLATFORM=offscreen` to the `test` target in `Makefile`.~~ **Done.**
3. Consider defining HTTP method constants/enum in `pypost/models/models.py` (surfaced
   during PYPOST-40 audit and reconfirmed here).
4. Fix pre-existing `flake8` violations across `pypost/` (W293, E302, F401, E501 etc.)
   — widespread, recommend a dedicated cleanup task.
