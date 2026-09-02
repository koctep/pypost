# PYPOST-1251: Technical Debt Analysis

## Scope Reviewed

This analysis covers the complete task-scoped artifact set, the bounded crash repro, and the
existing alert-reload behavior. Step 4 made no production change because the available
environment did not reproduce the reported native crash.

## Shortcuts Taken

- **Low severity — limited runtime coverage.** The repro exercises isolated child processes with
  `QT_QPA_PLATFORM=offscreen` and `PYTHONFAULTHANDLER=1` in the current CI-like environment only.
  It classifies the reported boundary but cannot establish behavior on operating systems,
  display backends, or Qt/PySide versions that are unavailable here.
  **Jira follow-up: not required.** The limitation is explicit in the requirements, observability
  artifact, and developer guidance; opening a ticket for an unavailable environment would be
  speculative.

## Code Quality Issues

- **Low severity — unused diagnostic helper.**
  `tests/test_main_window_alert_reload_crash_repro.py` defines
  `_returncode_description()`, but `_ChildOutcome.report()` does not call it. The current
  contract deliberately reports normalized classifications and bounded output rather than raw
  return-code or signal details, so this is dead code rather than a correctness defect.
  Remove the helper or incorporate its output if the diagnostic contract is expanded.
  **Jira follow-up: not required.** This is a small, local cleanup suitable for the next edit to
  the repro and does not justify a separate issue.

## Missing Tests

No task-scoped behavioral gap was identified. The existing alert-reload tests cover changed and
unchanged settings, manager propagation, and records before and after a destination change. The
new repro covers a clean control plus three repeated isolated child runs and treats non-zero,
signal, and timeout outcomes as failures.

The reported native crash remains unreproduced, so there is no evidence-based failure fixture to
add without manufacturing an environment-specific condition.

## Performance Concerns

The repro intentionally launches four bounded child pytest processes and took 5.56 seconds in
the focused run. This is acceptable for targeted reliability coverage. It is not a production
performance concern, and reducing the repetitions would weaken repeatability evidence.

## Deviations and Follow-up Tasks

Step 4 did not alter production behavior because the reviewed alert-reload boundary completed
normally in all bounded attempts. This is an evidence-backed classification, not a claim that an
unavailable runtime-specific crash has been fixed.

No Jira follow-up is genuinely required from this analysis. The two low-severity items above are
documented limitations or local cleanup opportunities, not unresolved defects or actionable
cross-team work. No speculative or resolved item was ticketed.

## Verification

- `make lint` — passed
- `make test PYTEST_ARGS="tests/test_main_window_alert_reload_crash_repro.py -q -m 'slow or not slow'" WORKERS=1 WORKER_TIMEOUT=30` — passed; 2 tests, 4 child runs
- `make verify-ai-tasks` — passed
