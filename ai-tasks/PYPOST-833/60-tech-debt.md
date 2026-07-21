# PYPOST-833: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

All acceptance criteria for launch → ready → shutdown are met. Items below are
non-blocking follow-ups (no blockers relative to DoD).

## Shortcuts Taken

- **Local `_wait_until` in `pypost.agent.lifecycle`.** Intentionally duplicates
  `tests.helpers.qt_wait.wait_until` so `pypost.agent` never imports from `tests/`.
  Behavior matches (processEvents + wall-clock deadline); drift risk if one side
  gains features (message formatting, posted quit, etc.).
- **Mid-start failure cleanup is best-effort.** On ready timeout, `start()` calls
  `shutdown()` before re-raising. `shutdown()` swallows per-step errors
  (MCP stop, `handle_exit`, window close, metrics stop, temp cleanup) and logs
  `*_failed` events. Failures before the ready wait (e.g. `compose_app` after
  temp dirs / metrics bind) rely on that same path or GC of
  `TemporaryDirectory` — not a guaranteed transactional rollback.
- **Soft FR6 metrics-port assert in smoke.**
  `test_agent_app_session_relaunch_after_shutdown` proves a second session can
  launch after shutdown (locks/dirs released). It does **not** hard-assert that
  the first session’s ephemeral metrics port is free via a socket bind/connect
  check.
- **Full `make check` not run during cleanup.** Step 4 validated
  `make lint` plus scoped
  `make test PYTEST_ARGS="tests/test_agent_lifecycle_smoke.py -v"` (2 passed).
  Full gate (lint + entire suite + verify-ai-tasks) was deferred as non-blocking
  for this story’s scoped change set.

## Code Quality Issues

- Duplicate wait helper (see Shortcuts) — prefer a shared production-safe helper
  under `pypost/` (or re-export) if siblings need the same pump elsewhere.
- `AgentAppSession.start` is not wrapped in a single try/finally for all
  pre-ready failures; only the timeout path explicitly shuts down before raise.
  Context-manager `__enter__` that raises does not run `__exit__`.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Launch → ready → shutdown | Covered (`test_agent_app_session_launch_ready_shutdown`) |
| Relaunch after shutdown (FR6 soft) | Covered (`test_agent_app_session_relaunch_after_shutdown`) |
| Ready timeout → `TimeoutError` + shutdown attempted | Not covered |
| Hard assert: metrics port free after shutdown | Not covered (soft FR6 only) |
| Mid-start failure leaves no listeners / temp dirs | Not covered |
| Full `make check` green after this story | Not re-run for PYPOST-833 |

Smoke tests have `pytestmark = pytest.mark.timeout(60)` — no timeout-marker
blockers.

## Performance Concerns

None introduced. Ready wait defaults to 30s; smoke uses the same bound. Ephemeral
metrics ports avoid fixed-port contention for parallel agent sessions.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| TD-1 | Low | Deduplicate `_wait_until` with a production-safe shared helper | Keep `pypost.agent` free of `tests/` imports; optional extract under `pypost/` | [PYPOST-840](https://pypost.atlassian.net/browse/PYPOST-840) |
| TD-2 | Low | Harden mid-start failure cleanup (try/finally transactional shutdown) | Best-effort today; ensure temp dirs + metrics always stop if `start()` fails | [PYPOST-841](https://pypost.atlassian.net/browse/PYPOST-841) |
| TD-3 | Low | Strengthen FR6 smoke: assert previous metrics port is free | Soft relaunch coverage exists; optional socket-level assert | [PYPOST-842](https://pypost.atlassian.net/browse/PYPOST-842) |
| TD-4 | Low | Run full `make check` after sibling noise is clear | Deferred in Step 4 cleanup; not a DoD blocker for lifecycle smoke | [PYPOST-843](https://pypost.atlassian.net/browse/PYPOST-843) |

Deferred by design (not debt for this ticket):

- Optional `ui_ready` signal — architecture; siblings may add if needed.
- Epic `make agent-*` packaging — PYPOST-839.
- Logging catalog entries in `doc/dev/logging.md` — Step 7 (Dev Docs).
- Scrapeable Prometheus counters for ephemeral agent sessions — N/A per
  observability notes.

## Blocker Review

**SAFE TO CLOSE** — FR1–FR7 satisfied by `AgentAppSession`, `is_ui_ready`, smoke
tests, and `doc/dev/agent_lifecycle.md`. Listed gaps are non-blocking; Jira Debt
issues are intentionally deferred to sprint-task-runner Phase D.
