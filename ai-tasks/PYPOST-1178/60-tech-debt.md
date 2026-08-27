# PYPOST-1178: Technical Debt Analysis

**Verdict:** Acceptable, intentional trade-offs for same-port restart readiness.
Primary flake path is covered by a permanent green regression. Known probe
caveat (`SO_REUSEADDR` false-positive) was deferred by architecture and remains
the main follow-up. No BLOCKER (timeout markers present). Sibling
[PYPOST-1113](https://pypost.atlassian.net/browse/PYPOST-1113) is Done and is a
different flake (signal-order wait) — not reopened here.

Scope reviewed: `pypost/core/qt/mcp_server.py` (`_wait_until_port_bindable` +
`update_tools` call site), `tests/helpers/port_allocation.py`,
`tests/helpers/mcp_live_server.py`,
`tests/test_mcp_server_manager.py::test_update_tools_restart_waits_until_port_bindable`,
and prior `ai-tasks/PYPOST-1178/{10,20,40,50}-*.md`.

---

## Shortcuts Taken

1. **Land WIP as-is (no rewrite)** — Requirements and architecture mandated
   retaining the existing restart-readiness and port-allocation shape rather
   than redesigning (port migration on restart, `SO_REUSEPORT`-only strategies,
   etc.). That keeps the surface small and matches validated in-scope progress.
2. **`SO_REUSEADDR` on probe-bind** — Both `_wait_until_port_bindable` and
   `allocate_tcp_port` / `_can_bind` set `SO_REUSEADDR` on the probe socket.
   Architecture explicitly noted that this can falsely report a port free on
   some platforms while another process holds a different bind tuple
   ([flare: drop SO_REUSEADDR from port probe](https://github.com/Tencent/flare/commit/81386ff6329335ca03e2c68ba938f732e548d822)).
   Primary flake is same-process restart after stop on Linux; WIP landed with
   the probe as-is. Treat platform false-positives/negatives as follow-up debt
   only if observed.
3. **Deadline then proceed** — On wait timeout, `_wait_until_port_bindable`
   logs `mcp_port_still_busy` and returns `None`; `update_tools` still calls
   `start_server`. Failure remains visible via existing `start_failed` / ERROR
   logs rather than a hard abort or return-value contract. Intentional and
   documented in architecture / observability.
4. **`stop_server` still clears thread refs after a 2.0s join** — Clearing the
   thread can make `is_running()` false before the OS has released the listener.
   The new bounded probe-bind gate is the compensating control; join timeout
   itself was not redesigned.

## Code Quality Issues

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Hardcoded wait defaults (`timeout=5.0`, sleep `0.05`) | Low | Bounded and documented; match suite “no unbounded wait” rules. Not worth config surface for this debt item. |
| Hardcoded allocator constants (`_PORT_BASE=35000`, `_PORT_SPAN=25000`, `_MAX_ATTEMPTS=200`, lock under `/tmp`) | Low | Test-only; override via `PYPOST_TEST_PORT_LOCK`. Adequate for CI isolation. |
| Duplicate probe-bind + `SO_REUSEADDR` pattern in production wait and test allocator | Low | Same readiness criterion intentionally; extracting a shared helper would couple production to test helpers — leave until a probe-policy change (follow-up 1) forces one place. |
| Pre-existing `make typecheck` baseline drift outside this change set | Low / NON-BLOCKER | Noted in Step 5 cleanup; files not introduced by PYPOST-1178. Do not expand this ticket to refresh mypy baseline. |

No naming, decomposition, or layering deviations from `20-architecture.md`.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Tool-set restart waits for port readiness then listens without `start_failed` | Covered — `test_update_tools_restart_waits_until_port_bindable` (permanent green; exercises real `_wait_until_port_bindable`) |
| Existing suite restart regression under load | Covered — `test_update_tools_restarts_when_exposed_set_changes` (original flake node) |
| Module-level pytest timeout | Present — `pytestmark = pytest.mark.timeout(60)` (**NO BLOCKER**) |
| Deadline path: held port + short timeout → `mcp_port_still_busy` in `caplog` | Not kept as a permanent test — Step 3 used held-socket / monkeypatch harness for red; Step 4 removed it in favor of the happy-path permanent regression. Acceptable for closing the flake; optional thin unit coverage if deadline WARNING regressions become a concern. |
| Dedicated unit coverage for `allocate_tcp_port` / lock-counter wrap / bind(0) fallback | Missing — optional; allocator is exercised indirectly via `free_port()` in manager/live tests. Architecture listed this as optional harden-only. |

## Performance Concerns

None material. Worst-case restart path adds up to ~5.0s of 50ms poll loops
before logging and continuing. Happy path returns on first successful
probe-bind. Cross-process `fcntl.flock` on test port allocation is held only
for counter advance + bind probe (test-only; not on the production restart
path).

## Follow-up Tasks

1. **NON-BLOCKER — deferred by architecture**
   - Drop or harden `SO_REUSEADDR` on readiness / allocator probe-bind if
     false-positive “port free” reports appear on non-Linux or under parallel
     bind-tuple contention (see architecture Research caveat / flare commit).
   - Touch points: `_wait_until_port_bindable` in
     `pypost/core/qt/mcp_server.py`; `_can_bind` /
     `allocate_tcp_port` in `tests/helpers/port_allocation.py`.
   - Do not expand PYPOST-1178; ticket only if observed in CI/prod.

2. **NON-BLOCKER — optional**
   - Thin unit tests: (a) `_wait_until_port_bindable` deadline emits
     `mcp_port_still_busy` under a held listener + short timeout; (b)
     `allocate_tcp_port` returns a bindable port / exercises fallback.
   - Nice-to-have coverage; not required to close the original flake.

3. **Resolved / out of scope**
   - Original flake node
     `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
     — addressed by this task (origin NON-BLOCKER in
     [PYPOST-1173](../PYPOST-1173/60-tech-debt.md)).
   - [PYPOST-1113](https://pypost.atlassian.net/browse/PYPOST-1113) — Done;
     different flake (signal-order wait in `test_port_busy_emits_start_failed`);
     do not reopen or ticket again from this analysis.

Phase D of the orchestrator creates Jira issues. Step 7 does not.
