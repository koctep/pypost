# PYPOST-569: Audit tests that consume full timeout budget but still pass

## Goals

Some tests may run close to their `pytest.mark.timeout` boundary and still report PASSED,
which can hide flakiness or unbounded waits that finish just in time. This task audits the
full suite to find high-utilization passes and document risk.

Part of epic [PYPOST-566](https://pypost.atlassian.net/browse/PYPOST-566) (test-suite
health), following [PYPOST-567](https://pypost.atlassian.net/browse/PYPOST-567) log
inventory.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want slow tests cross-referenced with their timeout markers so I
  can see which passes consume most of the declared budget.
- As a **maintainer**, I want a reproducible durations capture and parser so the audit can
  be re-run after suite changes.
- As a **team lead**, I want a clear verdict on whether any test passes only because the
  outer timeout kills a hang.

## Definition of Done

- [x] Full-suite durations captured with `--durations=30 --durations-min=10`.
- [x] Each slow test mapped to its effective `pytest.mark.timeout` (module/class/function).
- [x] Tests with duration >80% of marker flagged in `timeout-audit.md` / `.csv`.
- [x] Risk notes and recommendations documented.
- [x] Artifacts stored under `ai-tasks/PYPOST-569/`.

## Acceptance (from Jira)

- List: test name, duration, timeout marker, risk note — **0 offenders** at >80%
  threshold; top-20 slowest table included for context.
- No follow-up fix tasks required (no worst offenders).
