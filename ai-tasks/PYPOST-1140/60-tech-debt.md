# PYPOST-1140: Technical Debt Analysis

**Verdict:** Optional `max_history` ring-buffer cap closes TD-2 from PYPOST-1129. Default unbounded behavior preserved. All 20 harness tests pass.

Scope reviewed:
- `tests/websocket_echo_server.py` — `max_history` parameter, `_append_to_buffer`, `_total_received_count`
- `tests/test_websocket_echo_server.py` — `test_max_history_truncates_received_and_sent_buffers`
- `doc/dev/websocket_test_harness.md` — parameter documentation

---

## Shortcuts Taken

1. **Per-list independent caps with shared N**:
   - Each of the six message lists is capped independently to the same `max_history` value rather than a single shared deque backing all views.
   - *Rationale:* Minimal diff; aggregate and typed lists stay aligned without a larger refactor.

2. **No `max_history` on `ServerBehaviorConfig`**:
   - Cap is a server construction parameter only, not part of behavior configuration.
   - *Rationale:* Benchmark tuning is orthogonal to scripted behavior mode; avoids `configure()` accidentally clearing the cap.

---

## Code Quality Issues

None blocking. `_append_to_buffer` centralizes truncation; `_total_received_count` preserves close-on-count semantics.

---

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| Received buffer truncation | **Present** | `test_max_history_truncates_received_and_sent_buffers` |
| Sent buffer truncation | **Present** | Same test |
| Binary truncation | Optional | Text-only coverage sufficient for ring-buffer helper |
| `max_history < 1` ValueError | Optional | Documented; low risk |
| `close_on_message_count` with truncation | Optional | `_total_received_count` logic; no dedicated test in 1 SP scope |

### Timeout Marker Review

- **BLOCKER Check**: New test declares `@pytest.mark.timeout(10)`; module `pytestmark` remains `timeout(15)`.
- **Result**: **NO BLOCKER**

---

## Performance Concerns

1. **List front deletion**: `del buffer[:len - max_history]` is O(k) per append when over cap. Acceptable for test harness with modest N (typical benchmark caps 100–1000).
2. **Unbounded default unchanged**: Existing tests without `max_history` retain prior memory characteristics.

---

## Follow-up Tasks

### Resolved
- **TD-2 (PYPOST-1140)**: Optional `max_history` buffer truncation — **closed by this task**.

### Remaining from PYPOST-1129 (unchanged)
- TLS / `wss://` (PYPOST-1134)
- `oversize_on_connect` symmetry (optional improvement)
- TCP-level frame chunking (out of scope)

---

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** |
| Deviations from architecture | **None** |
| Acceptance gaps vs DoD | **None** |

**SAFE TO CLOSE** for PYPOST-1140.
