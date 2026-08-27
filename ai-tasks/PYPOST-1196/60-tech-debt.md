# PYPOST-1196: Technical Debt Analysis

**Verdict:** Acceptable. Residual port-busy flake after PYPOST-1178 is addressed
by truthful `is_running()` after join timeout plus a 10s bindable wait and
stronger listening asserts. No BLOCKER relative to acceptance criteria.
Sibling FILE_CAPS ([PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194))
remains out of scope.

Scope reviewed: `pypost/core/qt/mcp_server.py` (`stop_server`, `update_tools`,
`_wait_until_port_bindable`), `tests/test_mcp_server_manager.py` (join-timeout
repro + hardened exposed-set restart), and prior
`ai-tasks/PYPOST-1196/{10,20,40,50}-*.md`.

---

## Shortcuts Taken

1. **Retain thread ref on join timeout (no redesign of stop)** — Did not change
   the 2.0s join budget or introduce a hard abort when the port never frees;
   deadline still logs `mcp_port_still_busy` and proceeds (PYPOST-1178 contract).
2. **Default wait 10.0s** — Hardcoded bump from 5.0s to cover slow teardown under
   parallel suite load; not configurable. Matches suite “bounded wait” rules.
3. **SO_REUSEADDR probe unchanged** — Deferred by PYPOST-1178; filed failure was
   genuine busy (`mcp_port_still_busy`), not false-free. Left alone.
4. **Test-only delayed `should_exit` proxy** — Deterministic red harness; not a
   production API.

## Code Quality Issues

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Hardcoded wait default `timeout=10.0` | Low | Documented; optional config later if ops need tuning |
| `_server_instance = None` while orphaned thread may still reference the server | Low | Pre-existing on join timeout; keep-thread fix does not expand that surface |
| Delay proxy in join-timeout test | Low | Clear and local; acceptable for regression |

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| Join timeout + slow exit → restart listens without `start_failed` | Covered — `test_update_tools_restarts_when_stop_join_times_out` |
| Exposed-set restart asserts listening (not mere thread spawn) | Covered — hardened `test_update_tools_restarts_when_exposed_set_changes` |
| Happy-path bindable wait | Covered — `test_update_tools_restart_waits_until_port_bindable` (PYPOST-1178) |
| Module pytest timeout | Present — `pytestmark = pytest.mark.timeout(60)` (**NO BLOCKER**) |
| Deadline WARNING under held port (permanent unit) | Still optional from PYPOST-1178 — NON-BLOCKER |

## Performance Concerns

Worst-case tool-set restart wait is now ~10s of 50ms polls (plus up to 2s join)
before WARNING and continue. Happy path returns on first successful probe-bind
after the worker exits. Acceptable for CI / local suite; not on a hot request
path.

## Follow-up Tasks

| Item | Priority / class | Notes |
| ---- | ---------------- | ----- |
| SO_REUSEADDR probe hardening if false-free appears | Low / NON-BLOCKER — already deferred in PYPOST-1178 | Do not re-ticket unless observed |
| Configurable bindable-wait timeout | Low / NON-BLOCKER — accept residual, no ticket | Only if ops need knobs |
| Sibling FILE_CAPS | Out of scope | [PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194) |

No blockers relative to PYPOST-1196 acceptance criteria. Phase D: no new Jira
follow-ups required (no unticketed actionable debt rows).
