# Sprint 167 — Backlog

> Date: 2026-03-26 (PM kickoff), refreshed: 2026-03-27 from Jira
> Total issues: 7 (tech-debt, all PYPOST-402 children)
> Priority mix: High / High / Medium / Low / Low / Low / Low

## Issues

| # | Key | Summary | Type | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | PYPOST-418 | [PYPOST-402] AlertManager never injected into RequestWorker | Debt | High | Done |
| 2 | PYPOST-419 | [PYPOST-402] AppSettings.default_retry_policy is persisted but never applied | Debt | High | Done |
| 3 | PYPOST-420 | [PYPOST-402] Logger accumulation in AlertManager | Debt | Medium | Done |
| 4 | PYPOST-421 | [PYPOST-402] Bare assert in production retry path | Debt | Low | To Do |
| 5 | PYPOST-422 | [PYPOST-402] email_notification_failures_total metric name is misleading | Debt | Low | To Do |
| 6 | PYPOST-423 | [PYPOST-402] retryable_codes_edit silently drops invalid input | Debt | Low | To Do |
| 7 | PYPOST-424 | [PYPOST-402] request_timeout spin box created but never added to form layout | Debt | Low | To Do |

---

## Execution Order & Rationale

### Group A — AlertManager / Retry Wiring (PYPOST-402)

All three issues share the same module surface (`alert_manager.py`, `request_worker.py`,
`app_settings.py`). Addressing them together in one sprint avoids repeated churn on the
same files.

#### 1 · PYPOST-420 — Logger accumulation in AlertManager (Done)

**Problem**: `AlertManager.__init__` unconditionally calls `logging.getLogger().addHandler()`
on every instantiation, so the root logger accumulates duplicate handlers over time, causing
log-line multiplication.

**Fix**: Guard handler registration (check `logger.handlers` before adding) or use
`logging.getLogger(__name__)` (module-level singleton) rather than the root logger.

**Effort**: Low — isolated to `AlertManager.__init__` / logging setup.

#### 2 · PYPOST-418 — AlertManager never injected into RequestWorker (Done)

**Problem**: `AlertManager` is created in the application bootstrap but never passed to
`RequestWorker`, so alert callbacks (e.g., request-failure notifications) are dead code.

**Fix**: Inject `AlertManager` into `RequestWorker.__init__` and call the appropriate
alert methods at failure / timeout boundaries.

**Effort**: Medium — touches `RequestWorker`, the DI wiring in the main application, and
requires unit-test updates.

**Dependency**: PYPOST-420 should land first to ensure the injected `AlertManager` has a
clean logger.

#### 3 · PYPOST-419 — default_retry_policy persisted but never applied (Done)

**Problem**: `AppSettings.default_retry_policy` is serialised to / deserialised from disk
but `RequestWorker` never reads it at runtime, leaving the retry feature inert.

**Fix**: Read `default_retry_policy` from `AppSettings` inside `RequestWorker` and apply
it before each request (or at worker initialisation).

**Effort**: Medium — touches `RequestWorker` retry logic, settings loading, and unit tests.

**Dependency**: Best landed after PYPOST-418 so both wiring changes land in the same area
in one coordinated pass.

### Group B — Remaining PYPOST-402 debt (open)

#### 4 · PYPOST-421 — Bare assert in production retry path

Replace production `assert` usage in retry flow with explicit runtime checks and
controlled error handling.

#### 5 · PYPOST-422 — Misleading metric name

Align metric naming with actual semantics to avoid observability confusion and false
interpretation in dashboards.

#### 6 · PYPOST-423 — Silent invalid input drop in `retryable_codes_edit`

Surface validation errors to users instead of silently dropping invalid values.

#### 7 · PYPOST-424 — `request_timeout` spin box not added to layout

Ensure timeout control is visible and connected in the settings form layout.
