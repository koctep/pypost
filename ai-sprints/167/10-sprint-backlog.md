# Sprint 167 — Backlog

> Date: 2026-03-26 (PM kickoff)
> Total issues: 3 (tech-debt, all PYPOST-402 children)
> Priority: High / High / Medium

## Issues

| # | Key | Summary | Type | Priority | Status |
|---|-----|---------|------|----------|--------|
| 1 | PYPOST-418 | [PYPOST-402] AlertManager never injected into RequestWorker | Debt | High | To Do |
| 2 | PYPOST-419 | [PYPOST-402] AppSettings.default_retry_policy is persisted but never applied | Debt | High | To Do |
| 3 | PYPOST-420 | [PYPOST-402] Logger accumulation in AlertManager | Debt | Medium | To Do |

---

## Execution Order & Rationale

### Group A — AlertManager / Retry Wiring (PYPOST-402)

All three issues share the same module surface (`alert_manager.py`, `request_worker.py`,
`app_settings.py`). Addressing them together in one sprint avoids repeated churn on the
same files.

#### 1 · PYPOST-420 — Logger accumulation in AlertManager

**Problem**: `AlertManager.__init__` unconditionally calls `logging.getLogger().addHandler()`
on every instantiation, so the root logger accumulates duplicate handlers over time, causing
log-line multiplication.

**Fix**: Guard handler registration (check `logger.handlers` before adding) or use
`logging.getLogger(__name__)` (module-level singleton) rather than the root logger.

**Effort**: Low — isolated to `AlertManager.__init__` / logging setup.

#### 2 · PYPOST-418 — AlertManager never injected into RequestWorker

**Problem**: `AlertManager` is created in the application bootstrap but never passed to
`RequestWorker`, so alert callbacks (e.g., request-failure notifications) are dead code.

**Fix**: Inject `AlertManager` into `RequestWorker.__init__` and call the appropriate
alert methods at failure / timeout boundaries.

**Effort**: Medium — touches `RequestWorker`, the DI wiring in the main application, and
requires unit-test updates.

**Dependency**: PYPOST-420 should land first to ensure the injected `AlertManager` has a
clean logger.

#### 3 · PYPOST-419 — default_retry_policy persisted but never applied

**Problem**: `AppSettings.default_retry_policy` is serialised to / deserialised from disk
but `RequestWorker` never reads it at runtime, leaving the retry feature inert.

**Fix**: Read `default_retry_policy` from `AppSettings` inside `RequestWorker` and apply
it before each request (or at worker initialisation).

**Effort**: Medium — touches `RequestWorker` retry logic, settings loading, and unit tests.

**Dependency**: Best landed after PYPOST-418 so both wiring changes land in the same area
in one coordinated pass.
