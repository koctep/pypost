# PYPOST-1213: Technical Debt Analysis

## Shortcuts Taken

None. The task intentionally records diagnosis without changing runtime behavior.

## Code Quality Issues

None introduced. The underlying Qt allocation/lifecycle internals remain outside the
application’s proven control boundary.

## Missing Tests

No tests are missing for this scope. PYPOST-1212 owns the reproduction and bounded-pass
guard. Adding a second crash test here would duplicate the baseline and increase native
test risk.

## Performance Concerns

The full single-process GUI workload remains unsafe and can terminate with SIGSEGV. This
is an accepted known condition pending PYPOST-1214 mitigation.

## Follow-up Tasks

- NON-BLOCKER — PYPOST-1214 must implement and own bounded/process-isolated GUI execution
  and verify the chosen threshold against the PYPOST-1212 harness.
- NON-BLOCKER — upstream PySide6/Qt investigation may be needed if a future release
  provides a style-engine fix; this task does not claim a precise leaking allocation.

## Pre-Existing Test Failures

- NON-BLOCKER — pre-existing: `tests/test_main_window_alert_reload.py::test_open_settings_reloads_alert_manager_when_webhook_changes`
  reproduced during `make check` as SIGSEGV at `pypost/ui/styles/style_manager.py:102`.
  This is the behavior diagnosed by PYPOST-1213 and tracked under
  [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117); it is not caused by
  this documentation-only change.
