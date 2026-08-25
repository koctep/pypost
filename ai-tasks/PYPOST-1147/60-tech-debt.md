# PYPOST-1147: Technical Debt Analysis

**Verdict:** PYPOST-1136 missing-test debt ("High-Concurrency Stress Benchmarks") closed. Dedicated `tests/test_session_slots_stress.py` delivers 64-worker burst benchmarks with ceiling contention and timing sanity checks. **SAFE TO CLOSE.**

## Shortcuts Taken

None. Stress tests use isolated `SessionSlots` instances and inline helpers — no separate helper module to avoid over-engineering for 2 SP scope.

## Code Quality Issues

None introduced. Production `SessionSlots` unchanged.

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| 50+ concurrent worker acquire/release burst | **Present** | `test_session_slots_high_concurrency_acquire_release_burst` |
| Sustained ceiling contention with refusals | **Present** | `test_session_slots_sustained_ceiling_contention` |
| Bounded completion sanity | **Present** | `test_session_slots_stress_completes_within_timeout` |
| Global singleton stress under `get_session_slots()` | Deferred | Isolated instances sufficient; singleton leakage risk low |
| Dynamic mid-session limit reduction under stress | Deferred | Separate PYPOST-1136 follow-up scenario |

### Timeout Marker Review

- **BLOCKER Check**: Module declares `pytestmark = pytest.mark.timeout(60)`.
- **Result**: **NO BLOCKER**

## Performance Concerns

- Stress module adds ~1–3 s to targeted runs (64 workers × 50 cycles). Kept in dedicated file so default fast suite selection can exclude `*_stress.py` if needed in future CI tiers.
- `SessionSlots` mutex contention under 64 threads remains sub-second for in-memory set operations — no production change warranted.

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Optional CI job tier running `tests/test_*_stress.py` | Low | Only if full suite runtime becomes a concern |
| Global singleton stress scenario | Low | If cross-thread presenter + probe integration regresses |
| `test_websocket_session_slots.py` doc reference | Low | `doc/dev/testing.md` lists aspirational filename; actual slots tests span repro + stress modules |

## Closed Debt

- [x] [PYPOST-1147](https://pypost.atlassian.net/browse/PYPOST-1147) — closes item from [`ai-tasks/PYPOST-1136/60-tech-debt.md`](../PYPOST-1136/60-tech-debt.md) "High-Concurrency Stress Benchmarks"
