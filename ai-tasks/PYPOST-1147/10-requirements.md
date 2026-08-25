# PYPOST-1147: WS — High-concurrency stress benchmark tests for SessionSlots

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) introduced process-wide concurrent session governance via `SessionSlots` in [PYPOST-1136](https://pypost.atlassian.net/browse/PYPOST-1136) (WS-10). Standard unit tests verify thread safety with 20 workers and an 8-thread pool, but **extreme contention** under simulated high-throughput workloads was explicitly deferred to avoid slowing the default test suite.

This 2 SP tech-debt task closes the follow-up from [`ai-tasks/PYPOST-1136/60-tech-debt.md`](../PYPOST-1136/60-tech-debt.md): add dedicated stress benchmark tests that hammer `SessionSlots` slot acquisition, contention, and release under **50+ concurrent worker threads** with rapid burst cycles.

**Implementation language:** Python (pytest stress tests in the existing PyPost codebase; no production code changes).

## User Stories

- As a **maintainer** of WebSocket concurrency policy, I want automated stress benchmarks that exercise `SessionSlots` under 50+ concurrent threads, so that mutex invariants and slot accounting remain trustworthy under extreme contention without waiting for production incidents.
- As a **CI/CD maintainer**, I want stress tests isolated in a dedicated module with explicit timeouts, so that the default fast suite stays fast while high-concurrency coverage can be run deliberately.
- As a **developer** extending MCP probe or presenter slot lifecycle, I want benchmark tests documenting expected behavior under burst acquire/release churn, so that regressions in slot release or ceiling enforcement are caught early.

## Definition of Done

1. **Dedicated stress test module**
   - New test file under `tests/` (e.g. `test_session_slots_stress.py`) dedicated to high-concurrency `SessionSlots` benchmarks.
   - Module declares explicit `pytest.mark.timeout(...)` per project testing standards.

2. **50+ concurrent worker coverage**
   - At least one test drives **≥ 50 concurrent worker threads** (via `ThreadPoolExecutor` or equivalent) against an isolated `SessionSlots` instance.
   - Tests verify slot acquisition, contention at the ceiling, and idempotent release under rapid burst cycles.

3. **Correctness invariants**
   - `active_count` never exceeds `max_slots` during concurrent operations.
   - All slots are released after workers complete (`active_count == 0` at end).
   - No deadlocks or counter corruption under sustained contention.

4. **Performance sanity (non-flaky)**
   - Optional bounded timing assertion or cycle-count benchmark that completes within a generous CI timeout (no hard millisecond SLA that flakes on slow runners).

5. **Quality gates**
   - `make test` and `make lint` pass for the new module.
   - No production code changes required unless a genuine defect is discovered (out of scope for this debt story).

## Task Description

### Problem

`tests/test_websocket_settings_and_limits_repro.py::TestSessionSlotsConcurrencyCoordinator::test_session_slots_thread_safety_under_contention` uses 20 workers with an 8-thread pool. PYPOST-1136 tech debt noted that **50+ thread** extreme contention scenarios were omitted to keep the standard suite fast.

### Scope

**In scope:**

- Dedicated stress benchmark tests for `SessionSlots` acquire/contention/release under ≥ 50 concurrent workers.
- Roadmap and dev-docs updates referencing the new stress module.

**Out of scope:**

- Production changes to `SessionSlots` implementation (unless a red stress test exposes a real bug — file a separate bug story).
- Prometheus metrics or logging changes.
- Live WebSocket integration or GUI tests.

### Constraints and assumptions

- Tests use isolated `SessionSlots(max_slots=N)` instances — not the global singleton — to avoid cross-test leakage.
- All verification is Qt-free; pure threading only.
- Stress tests may run longer than unit tests but must stay within declared per-module timeout (recommended 60–120 s tier).

### Non-functional requirements

- **Determinism**: Use thread-safe counters and join/executor completion — no arbitrary sleeps for synchronization.
- **Isolation**: No dependency on network, Qt event loop, or global `get_session_slots()` state.
- **Maintainability**: Constants (`STRESS_WORKER_COUNT`, burst cycle counts) documented at module top for tuning.

## Q&A

**Q: Why a separate file instead of extending `test_websocket_settings_and_limits_repro.py`?**
A: The existing repro module is large and tied to WS-10 settings/metrics integration. A dedicated stress module keeps slow high-thread benchmarks discoverable and avoids inflating the default repro suite runtime.

**Q: Does this task change production behavior?**
A: No. Deliverable is test coverage only, closing PYPOST-1136 missing-test debt.

**Q: Where did this requirement originate?**
A: Follow-up in [`ai-tasks/PYPOST-1136/60-tech-debt.md`](../PYPOST-1136/60-tech-debt.md), ticketed as [PYPOST-1147](https://pypost.atlassian.net/browse/PYPOST-1147).
