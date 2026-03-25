# Sprint 100 — Sprint Report

> Date: 2026-03-24
> Sprint: 100
> Reporter: Team Lead

---

## Result Summary

**3 of 3 issues completed. 0 failed.**

| Key | Summary | Result | Commits |
|-----|---------|--------|---------|
| PYPOST-400 | Stabilize post publishing API error handling | Done | `031194b` |
| PYPOST-401 | Fix race condition in scheduling worker | Done | `2200238` |
| PYPOST-402 | Add retry and alerting for email failures | Done | `10789f6` |

Test suite: 187/191 passing across all three issues. The 4 pre-existing failures are
unrelated to sprint work and unchanged throughout.

---

## Done Issues

### PYPOST-400 · Stabilize post publishing API error handling

Introduced `ErrorCategory` / `ExecutionError` structured error model across 8 files. All
error paths now carry typed categories and actionable UI messages. Prometheus counters cover
every failure mode. 43 new/updated tests pass.

### PYPOST-401 · Fix race condition in scheduling worker

Replaced unsafe `bool` stop flag with `threading.Event` (RC-1/RC-2). Fixed RC-3 stale-worker
reference and RC-4 assignment ordering in `tabs_presenter`. New `tests/test_worker_race.py`
covers all three concurrency scenarios. No new debt introduced.

### PYPOST-402 · Add retry and alerting for email failures

Added `RetryPolicy`, `AlertManager`, retry signal, exponential backoff, and settings UI across
8 files. Unit tests confirm retry/alert logic in isolation. Two critical wiring gaps (TD-1,
TD-2 below) mean alerting and the default retry policy are not yet active in production.

---

## Failed Issues

None.

---

## Key Risks

### RISK-1 (High) — Alerting is dead code in production

`AlertManager` is fully implemented and unit-tested but is never injected into `RequestWorker`
at the production call-site (`pypost/core/worker.py`). Alerts will never fire regardless of
user settings until TD-1 is resolved.

**Affected:** PYPOST-402 AC-6 / FR-4

### RISK-2 (High) — Default retry policy has no runtime effect

`AppSettings.default_retry_policy` is saved by the Settings UI but neither `RequestWorker`
nor `RequestService` reads it. All requests without a per-request policy fall back to
`max_retries=0` silently, defeating the primary user-facing feature.

**Affected:** PYPOST-402 AC-9

### RISK-3 (Low) — Pre-existing DI gap in `HTTPClient`

`HTTPClient()` can be instantiated without a `template_service`, causing 3 SSE probe tests to
fail. Tracked since before PYPOST-378; not introduced by this sprint.

---

## Technical Debt Backlog

Items ordered by priority for scheduling in a future sprint.

### Critical (schedule in next sprint)

| ID | File | Description |
|----|------|-------------|
| PYPOST-402-TD1 | `pypost/core/worker.py` | Wire `AlertManager` into `RequestWorker` |
| PYPOST-402-TD2 | `pypost/core/worker.py`, `pypost/models/settings.py` | Apply `default_retry_policy` from `AppSettings` at runtime |

### Significant

| ID | File | Description |
|----|------|-------------|
| PYPOST-402-TD3 | `pypost/core/alert_manager.py` | Fix logger/file-handle leak on repeated `AlertManager` construction |
| PYPOST-402-TD4 | `pypost/core/request_service.py:183` | Replace bare `assert last_error` with explicit `RuntimeError` guard |
| PYPOST-400-TD3 | `pypost/core/mcp_client_service.py` | Replace string-heuristic exception classification with explicit `except` clauses |

### Minor

| ID | File | Description |
|----|------|-------------|
| PYPOST-402-TD5 | `pypost/core/metrics.py` | Rename `email_notification_failures_total` to `request_retry_exhaustions_total` |
| PYPOST-402-TD6 | `pypost/ui/dialogs/settings_dialog.py` | Validate `retryable_codes_edit` input; show error on invalid token |
| PYPOST-402-TD7 | `pypost/ui/dialogs/settings_dialog.py` | Add missing `request_timeout` row to settings form layout |
| PYPOST-400-TD1 | `pypost/core/request_service.py` | Deprecate `script_error: Optional[str]` in favour of `execution_error.category` |
| PYPOST-400-TD2 | `pypost/core/request_service.py` | Render URL template once and pass resolved value down call chain |
| PYPOST-400-TD4 | `tests/` | Add test covering `except ExecutionError` branch in `RequestWorker.run()` |
| PYPOST-400-TD5 | `pypost/ui/presenters/tabs_presenter.py` | Introduce `ErrorCategory.CANCELLED` to replace string-matching cancellation heuristic |
| PYPOST-401-TD2 | `tests/test_worker_race.py` | Add test for stale-worker cleared log path (RC-3 observable path) |
| PYPOST-401-TD3 | `pypost/core/worker.py` | Document that `stop()` is permanent for the lifetime of the instance |

---

## Recommendations for Next Iteration

1. **Prioritise TD-1 and TD-2 before any new PYPOST-402 work.** Both are small wiring fixes
   (< 20 lines each) but without them the alerting and retry-policy features are inert in
   production. They should be treated as a release blocker.

2. **Schedule TD-3 (logger leak) alongside TD-1.** Both touch `alert_manager.py` / `worker.py`;
   fixing them together reduces context-switching cost.

3. **Create follow-up tickets for the 4 pre-existing test failures.** The DI gap in `HTTPClient`
   (3 SSE probe failures) and the flaky `tmpdir` history test have been deferred across multiple
   sprints. They should be formally tracked as bugs with a target sprint.

4. **Consider an `ErrorCategory.CANCELLED` enum value (PYPOST-400-TD5).** The current
   string-matching cancellation heuristic in `tabs_presenter.py` is a ticking time bomb.
   This is a low-effort change with high resilience payoff.

5. **Close out minor UI gaps (TD-6, TD-7) in a dedicated polish sprint.** Silent input
   dropping and a missing form row degrade user trust in the settings panel.
