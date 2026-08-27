# PYPOST-1113: Technical Debt Analysis

**Verdict:** Minimal, intentional test-only sync fix. No production shortcuts.
Compound `wait_until` in `test_port_busy_emits_start_failed` matches the module’s
established multi-condition pattern (`test_status_true_when_port_is_listening`).
No BLOCKER (timeout markers present). No new Jira Debt issues required from this
task.

Scope reviewed: `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`
and prior `ai-tasks/PYPOST-1113/{10,20,40,50}-*.md`. Sibling WIP for
[PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178)
(`pypost/core/qt/mcp_server.py`, `tests/helpers/mcp_live_server.py`,
`tests/helpers/port_allocation.py`) was left untouched and is **not** claimed as
debt of this task.

---

## Shortcuts Taken

None for the in-scope fix. The incomplete wait (`bool(failures)` only) was replaced
with the full conjunction (`failures` ∧ `statuses` ∧ `statuses[-1] is False`) rather
than a fixed sleep, unbounded poll, or product emission-order change.

Step 3’s deferred `QTimer.singleShot` harness was intentionally temporary and
removed in Step 4; that is not residual debt.

## Code Quality Issues

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Post-wait `assert statuses[-1] is False` duplicates the wait predicate | Low | Kept deliberately as an explicit behavioral assertion after the wait (see `40-code-cleanup.md`). Harmless redundancy. |
| Pre-existing double blank line after stdlib imports in `tests/test_mcp_server_manager.py` | Low | Outside the PYPOST-1113 diff; not reformatted in Step 5. |
| `test_stop_emits_false` waits only for *initial* status, then asserts stopped without a post-`stop_server` compound wait | Low | Same file, related incomplete-sync *pattern*, but **not** observed as a flake in this task’s stress/history. Optional hardening only if it flakes later. |

No naming, decomposition, or architecture deviations from `20-architecture.md`.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Busy-port start emits one `start_failed` (port in message) and stopped status | Covered — compound wait + asserts |
| Module-level pytest timeout | Present — `pytestmark = pytest.mark.timeout(60)` (**NO BLOCKER**) |
| Permanent deferred-delivery regression (Step 3 `QTimer` harness kept as a test) | Not kept — by design; suite standardizes on compound `wait_until`, not synthetic deferral fixtures. Acceptable trade-off. |
| Broader MCP manager / live-port / restart coverage | Out of scope (PYPOST-1178 and existing suite) |

## Performance Concerns

None. Default bounded `wait_until` timeout (~10s via `ui_wait`) is unchanged; the
predicate may poll slightly longer under load when waiting for the second signal,
which is the intended reliability trade-off.

## Follow-up Tasks

| Priority | Item | Notes |
| -------- | ---- | ----- |
| — | PYPOST-1113 signal-ordering flake in `test_port_busy_emits_start_failed` | **Resolved** by this task (origin NON-BLOCKER in [PYPOST-1088](../PYPOST-1088/60-tech-debt.md)) |
| Out of scope | MCP restart EADDRINUSE / port allocation WIP | Owned by [PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178); do not ticket again from this analysis |
| NON-BLOCKER — optional | Harden `test_stop_emits_false` with a post-stop compound `wait_until` if it ever flakes under load | Same module pattern; no failure evidence in this run |

No new follow-up Jira issues required from PYPOST-1113.
