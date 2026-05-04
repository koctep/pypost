# Sprint 167 — Execution Report

> Date: 2026-03-26
> Executor: junior_engineer
> Method: `./scripts/agent-do.sh <ISSUE_KEY>` per issue, in dependency order
> Scope refresh: 2026-03-27 against Jira sprint composition
> Final refresh: 2026-03-27 after PYPOST-421..424 closure

---

## Completed Issues

| # | Key | Summary | Commit | Tests |
| --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | Logger accumulation in AlertManager | `a397a18` | 17/17 pass |
| 2 | PYPOST-418 | AlertManager never injected into RequestWorker | `39eb591` | 274/274 pass |
| 3 | PYPOST-419 | AppSettings.default_retry_policy persisted but never applied | `24a7656` | 26/26 pass |
| 4 | PYPOST-421 | Bare assert in production retry path | `231a24c` | 49/49 pass |
| 5 | PYPOST-422 | email_notification_failures_total metric name is misleading | `0c19432` | 42/42 pass |
| 6 | PYPOST-423 | retryable_codes_edit silently drops invalid input | `b897782` | 49/49 pass |
| 7 | PYPOST-424 | request_timeout spin box created but never added to form layout | `d644190` | 292/292 pass |

---

## Failed Issues

None.

---

## Blockers

- None.

---

## Retries Performed

None. All three issues completed on first attempt.

---

## Retries Performed (Final Wave)

None. PYPOST-421/422/423/424 each completed on first attempt.

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

### PYPOST-421 — Bare assert in production retry path

- **Fix**: Replaced assertion-based exhaustion branch with explicit `ExecutionError` handling
  for retryable status exhaustion; aligned exhaustion flow with existing alert/metric path.
- **Files changed**: `pypost/core/request_service.py`, `tests/test_retry.py`
- **New tests**: `TestRetryableStatusExhaustion` and related exhaustion assertions.

### PYPOST-422 — Misleading metric name

- **Fix**: Renamed exhaustion metric and tracker from email-specific naming to request-retry
  semantics (`request_retry_exhaustions_total`, `track_request_retry_exhaustion`).
- **Files changed**: `pypost/core/metrics.py`, `pypost/core/request_service.py`,
  `tests/test_metrics_manager.py`, `tests/test_retry.py`
- **New tests**: Metric scrape assertion and updated retry exhaustion metric assertions.

### PYPOST-423 — Silent invalid input drop in `retryable_codes_edit`

- **Fix**: Added explicit parser/validator for retryable codes and blocked settings save with
  user feedback on invalid input; removed silent token drops.
- **Files changed**: `pypost/models/retry.py`, `pypost/ui/dialogs/settings_dialog.py`,
  `tests/test_retryable_status_codes_parse.py`
- **New tests**: Parser validation matrix (valid, empty segment, invalid token, range, separator).

### PYPOST-424 — `request_timeout` control not visible in settings

- **Fix**: Added request-timeout control to settings form layout and extended `settings_applied`
  log snapshot with `request_timeout` for post-save observability.
- **Files changed**: `pypost/ui/dialogs/settings_dialog.py`, `pypost/ui/main_window.py`,
  `tests/test_settings_dialog.py`, `tests/test_settings_persistence.py`
- **New tests**: Settings dialog layout/load/accept checks and persistence round-trip extension.
