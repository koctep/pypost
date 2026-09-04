# PYPOST-1256: Developer Documentation

## Step 8 artifact

Created [`doc/dev/presenter_teardown.md`](../../doc/dev/presenter_teardown.md), a maintainer guide
for the uniform asynchronous teardown contract. It documents the public owner APIs,
`TeardownResult` fields and outcomes, bounded deadline semantics, the bounded
`flush(timeout_ms=...)` form and the unbounded `flush(timeout_ms=None)` caveat,
composition-root ordering and environment-update cutoff, lifecycle-owned late-signal fencing, the
HistoryPanel UI-local callback caveat (TD-1256-04), owner responsibilities, compatibility seams,
observability, secret-safe telemetry, and deterministic test patterns.

The guide is aligned with the final implementation in `pypost/core/lifecycle.py`, the lifecycle
helpers for tabs, history, environment storage, and `MainWindow`, plus the focused regression and
observability suites. It records current behavior, including cached incomplete results, the
optional/live environment disposition diagnostic, the bounded-versus-unbounded history flush
behavior, and the TD-1256-04 HistoryPanel caveat, rather than promising a retry or immutable
snapshot API that does not yet exist.

## Validation

- `make test WORKERS=1 WORKER_TIMEOUT=60 PYTEST_ARGS='tests/test_presenter_teardown_contract_repro.py tests/test_lifecycle_observability.py'` passed: 2 files passed, 0 failed, 0 skipped.
- `make lint` passed, including Markdown and relative-link checks.
- `make verify-ai-tasks` passed: 358 completed-task artifacts and 2 grandfathered legacy gaps verified.
- Protected files `AGENTS.md`, `ai-tasks/sprint-1984/00-sprint-state.md`, and
  `ai-tasks/PYPOST-376/baseline-metrics.md` were not modified by Step 8.

Step 8 passed the independent acceptance review and is accepted (`[x]`).
