# PYPOST-1140: WS test harness — optional max_history buffer cap

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) relies on the in-process WebSocket test harness from [PYPOST-1129](https://pypost.atlassian.net/browse/PYPOST-1129) (WS-11) for offline, deterministic client and integration testing.

Follow-up technical debt **TD-2** in [`ai-tasks/PYPOST-1129/60-tech-debt.md`](../PYPOST-1129/60-tech-debt.md) identified that the harness stores every received and sent message in unbounded in-memory lists. During large-scale benchmark or flood stress scenarios (tens of thousands of frames), those buffers can grow without limit and increase memory consumption across long CI suites or repeated benchmark runs.

This task closes TD-2 by adding an optional cap on message history retention so benchmark authors can bound memory while still inspecting recent frames for assertions.

**Implementation language:** Python (test infrastructure in the existing PyPost / PySide6 codebase; no production code changes).

## User Stories

- As a **test engineer** running high-throughput WebSocket flood or benchmark tests, I want to limit how many recent messages the test server retains in memory, so that long benchmark runs do not accumulate unbounded message history and inflate CI memory usage.
- As a **developer** writing observability assertions on the harness, I want the most recent N received and sent messages to remain available when a cap is configured, so that I can still verify recent traffic without storing the full stream.
- As a **maintainer** of the WS-11 harness, I want the default behavior (no cap) to remain unchanged for existing tests, so that the current test suite and downstream consumers do not regress.

## Definition of Done

The task is considered done when:

1. **Optional history cap**
   - The scripted WebSocket test server accepts an optional maximum history size at construction.
   - When unset, message buffers behave as today (unbounded retention until `reset()`).
   - When set, received and sent message buffers retain only the most recent N entries (ring-buffer truncation); older entries are dropped.

2. **Buffer consistency**
   - Truncation applies to aggregate buffers (`received_messages`, `sent_messages`) and their text/binary filtered views so counts and contents stay aligned.

3. **Backward compatibility**
   - Default construction without the cap preserves existing behavior.
   - All existing harness tests pass without behavioral changes.

4. **Test coverage**
   - A dedicated test asserts truncation of received and sent buffers when the cap is exceeded.

5. **Quality gates**
   - New test declares explicit `pytest.mark.timeout(...)`.
   - `make lint` and targeted harness tests pass.

## Task Description

### Problem

`ScriptedWebSocketServer` records every received and sent frame in Python lists for test assertions. `reset()` clears buffers between tests, but within a single long-running benchmark or extreme flood scenario, lists can grow to hundreds of thousands of entries and increase memory pressure.

### Scope

**In scope:**

- Optional `max_history` parameter on `ScriptedWebSocketServer` in `tests/websocket_echo_server.py`.
- Ring-buffer truncation on received and sent message lists when the cap is set.
- Test validating truncation behavior.
- Developer documentation update for the new parameter.
- Closing TD-2 in PYPOST-1129 tech-debt follow-ups.

**Out of scope:**

- Production code under `pypost/`.
- Changes to `ServerBehaviorConfig` or scripted behavior semantics beyond buffer retention.
- Per-client send API (PYPOST-1139 / TD-1).
- TLS / `wss://` mode (PYPOST-1134).

### Constraints and assumptions

- Work stays within `tests/websocket_echo_server.py` for implementation; tests live in `tests/test_websocket_echo_server.py`.
- Cap applies to in-memory diagnostic buffers only; WebSocket protocol behavior (echo, flood, close codes) is unchanged.
- Benchmark authors who need full history continue to use default (no cap) or call `reset()` between phases.

## Q&A

**Q: Should truncation affect connection counters or close-on-message-count behavior?**
A: Connection and disconnection counters remain cumulative. Close-on-message-count must still count every received frame even when buffers are truncated — addressed in architecture (separate total counter).

**Q: Where is the parameter configured?**
A: Constructor argument on `ScriptedWebSocketServer`, not the behavior config dataclass — keeps benchmark tuning separate from scripted behavior mode.
