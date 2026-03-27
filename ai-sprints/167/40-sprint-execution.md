# Sprint 167 — Execution Report

> Date: 2026-03-26
> Executor: junior_engineer
> Method: `./scripts/agent-do.sh <ISSUE_KEY>` per issue, in dependency order
> Scope refresh: 2026-03-27 against Jira sprint composition

---

## Completed Issues

| # | Key | Summary | Commit | Tests |
| --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | Logger accumulation in AlertManager | `a397a18` | 17/17 pass |
| 2 | PYPOST-418 | AlertManager never injected into RequestWorker | `39eb591` | 274/274 pass |
| 3 | PYPOST-419 | AppSettings.default_retry_policy persisted but never applied | `24a7656` | 26/26 pass |

---

## Remaining Issues In Sprint 167

| # | Key | Summary | Priority | Jira Status |
| --- | --- | --- | --- | --- |
| 1 | PYPOST-421 | [PYPOST-402] Bare assert in production retry path | Low | To Do |
| 2 | PYPOST-422 | [PYPOST-402] email_notification_failures_total metric name is misleading | Low | To Do |
| 3 | PYPOST-423 | [PYPOST-402] retryable_codes_edit silently drops invalid input | Low | To Do |
| 4 | PYPOST-424 | [PYPOST-402] request_timeout spin box created but never added to form layout | Low | To Do |

---

## Failed Issues

None.

---

## Blockers

- No technical blockers for completed items.
- Sprint-level completion is pending because 4 scope items remain in Jira (`To Do`).

---

## Retries Performed

None. All three issues completed on first attempt.

---

## Execution Notes

### PYPOST-420 — Logger accumulation in AlertManager

- **Fix**: Handler guard in `AlertManager.__init__` closes and removes stale handlers left by
  GC'd instances at the same CPython memory address; `close()` and `__enter__`/`__exit__`
  added for lifecycle management.
- **Files changed**: `pypost/core/alert_manager.py`, `tests/test_alert_manager.py`
- **New tests**: `TestAlertManagerAccumulation` (normal close path + CPython id() reuse path)

### PYPOST-418 — AlertManager never injected into RequestWorker

- **Fix**: `AlertManager` bootstrapped in `main.py` from `AppSettings` and propagated through
  the full DI chain: `main.py` → `MainWindow` → `TabsPresenter` → `RequestWorker` →
  `RequestService`. All params default to `None` (backward-compatible).
- **Files changed**: `pypost/models/settings.py`, `pypost/main.py`, `pypost/ui/main_window.py`,
  `pypost/ui/presenters/tabs_presenter.py`, `pypost/core/worker.py`,
  `tests/test_worker.py`, `tests/test_tabs_presenter.py`
- **New tests**: `TestRequestWorkerAlertManagerInjection` (2), `TestTabsPresenterAlertManagerPropagation` (2)
- **Dependency**: Required PYPOST-420 (clean logger) to land first — satisfied.

### PYPOST-419 — default_retry_policy persisted but never applied

- **Fix**: `default_retry_policy: RetryPolicy | None = None` injected into `RequestService`
  and `RequestWorker`; `tabs_presenter` passes `self._settings.default_retry_policy` at
  worker construction. Two-line fallback in `_execute_http_with_retry` implements the
  3-tier resolution: per-request → app default → hardcoded fallback.
- **Files changed**: `pypost/core/request_service.py`, `pypost/core/worker.py`,
  `pypost/ui/presenters/tabs_presenter.py`, `tests/test_request_service.py`
- **New tests**: `TestRequestServiceRetryPolicyResolution` (3 — all 3 resolution branches)
- **Dependency**: Required PYPOST-418 (shared wiring surface) to land first — satisfied.
