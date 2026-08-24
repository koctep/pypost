# PYPOST-1139: WS test harness — per-client messaging and disconnection cleanup

## Goals

Epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123) (WebSocket Protocol Support) depends on the in-process WebSocket test harness delivered in [PYPOST-1129](https://pypost.atlassian.net/browse/PYPOST-1129) (WS-11). That harness already supports broadcast messaging to all connected peers and leak-free startup/teardown across repeated test cycles.

Follow-up technical debt **TD-1** in [`ai-tasks/PYPOST-1129/60-tech-debt.md`](../PYPOST-1129/60-tech-debt.md) identified two non-blocking gaps that limit upcoming multi-session WebSocket stories and stress scenarios:

1. **Selective per-client messaging**: Downstream tests (multi-client routing, per-session scripted responses, MCP probe scenarios with several simultaneous peers) need to deliver a message to one connected peer without broadcasting to every other peer on the same test server. Today the harness only exposes broadcast-style delivery to all connected clients.
2. **Prompt reclamation after disconnection under churn**: When many clients connect and disconnect rapidly during a single test or across repeated cycles, disconnected peer handles must be reclaimed promptly so CI runs stay deterministic, memory-stable, and free of orphaned native objects. Current disconnection handling removes peers from the active client list but relies on deferred garbage collection for final reclamation.

This task closes TD-1 so the test harness remains a reliable foundation for Wave 1+ WebSocket client and integration stories without expanding scope into unrelated harness enhancements (buffer truncation, TLS, or new scripted behaviors).

**Implementation language:** Python (test infrastructure in the existing PyPost / PySide6 codebase; no new language or framework).

## User Stories

- As a **test engineer** writing multi-client WebSocket integration tests, I want the offline test server to send a text or binary message to one specific connected peer without affecting other peers on the same server, so that I can verify per-session routing, selective server responses, and concurrent session behavior deterministically.
- As a **developer** implementing WebSocket client features (transport, session controller, MCP probe, E2E flows), I want a documented, harness-level way to target individual connected peers during tests, so that I do not duplicate ad-hoc socket wiring in every test module.
- As a **CI/CD maintainer**, I want disconnected test-server peers to be reclaimed promptly during high connection churn and repeated startup/teardown cycles, so that long test suites do not accumulate native object leaks, memory growth, or flaky port/socket exhaustion.
- As a **maintainer** of the WS-11 test harness, I want broadcast messaging and existing scripted behaviors (echo, flood, drop, close codes, etc.) to continue working unchanged after this enhancement, so that the existing 17 harness tests and downstream consumers (`ws_test_server` fixture, E2E and MCP probe tests) do not regress.

## Definition of Done

The task is considered done when the following acceptance criteria are met:

1. **Per-client message delivery**
   - The scripted WebSocket test server exposes a capability to send a text or binary message to a single designated connected peer.
   - When multiple peers are connected, a message sent to one peer is received only by that peer; other connected peers do not receive it.
   - Sent messages are recorded in the server's existing sent-message diagnostic buffers consistently with broadcast delivery (so observability counters and assertions remain trustworthy).

2. **Disconnection cleanup under churn**
   - When a peer disconnects (normal close, server-initiated close, or abrupt drop), the harness reclaims resources associated with that peer promptly and does not retain it as an active or lingering connection handle.
   - Repeated connect/disconnect cycles and the existing leak-free startup/teardown test continue to pass without socket, port, or resource leaks.

3. **Backward compatibility**
   - Existing broadcast-to-all messaging behavior is unchanged.
   - All existing harness unit and integration tests in `tests/test_websocket_echo_server.py` pass without modification to their behavioral expectations (unless a test is added specifically for the new capability).
   - The `ws_test_server` pytest fixture and downstream tests that depend on the harness (E2E WebSocket tests, MCP probe repro tests) continue to pass.

4. **Test coverage (recommended, not blocking release of the helper alone)**
   - A dedicated test asserting selective multi-client message targeting is added or explicitly deferred with rationale in the tech-debt artifact if scope is limited to harness API only in this 1 SP story.

5. **Quality gates**
   - New or updated tests declare explicit `pytest.mark.timeout(...)` markers per project testing standards.
   - `make check` (lint, test, verify-ai-tasks) passes.

## Task Description

### Problem

The WS-11 scripted WebSocket test server (`tests/websocket_echo_server.py`) is the offline loopback peer for Epic PYPOST-1123. PYPOST-1129 delivered broadcast messaging (`send_to_all`), scripted behaviors, observability buffers, and verified leak-free lifecycle across 17 tests.

Two harness limitations remain (TD-1 in PYPOST-1129 tech debt):

| Gap | Impact |
| --- | --- |
| No per-client send API | Multi-session tests must broadcast or open separate server instances, blocking realistic concurrent-peer scenarios planned for downstream stories. |
| Deferred peer reclamation on disconnect | Under connection churn, reliance on garbage collection for native peer objects increases risk of resource retention and nondeterministic CI behavior. |

### Scope

**In scope:**

- Enhancements to the scripted WebSocket test server in `tests/websocket_echo_server.py` for (a) targeted single-peer message delivery and (b) prompt reclamation when a peer disconnects.
- Tests validating the new per-client delivery behavior and confirming no regression to leak-free lifecycle guarantees.
- Closing TD-1 in PYPOST-1129 tech-debt follow-ups.

**Out of scope:**

- Changes to production code under `pypost/`.
- Optional `max_history` buffer truncation (PYPOST-1140 / TD-2).
- TLS / `wss://` server mode (PYPOST-1134).
- New scripted behaviors (e.g. `oversize_on_connect` symmetry) or signal-adapter refactors noted as separate improvements in PYPOST-1129 tech debt.
- User-facing documentation (owned by PYPOST-1138 / WS-12 unless dev docs are updated in Step 8 if API surface changes).

### Constraints and assumptions

- Work stays within the existing in-process test harness boundary established by WS-11 (no production changes, no external network, no new transport modes such as TLS).
- Per-client delivery applies only to peers currently in the server's connected-client set; behavior for invalid or already-disconnected peer handles is defined in architecture (Step 2), not here.
- Story estimate is 1 SP — scope is narrowly limited to TD-1; comprehensive multi-session test suites may land in follow-on stories.

### Non-functional requirements

- **Determinism**: Behavior must be reproducible under headless CI (`QT_QPA_PLATFORM=offscreen`) with bounded `wait_until` synchronization, not arbitrary sleeps.
- **Performance**: Per-client send and disconnect cleanup must not materially degrade existing flood and responsiveness tests for standard burst sizes (50–100 messages).
- **Isolation**: No external network dependencies; all verification remains on loopback.
- **Maintainability**: Changes follow existing harness conventions (type hints, structured debug logging, sent/received buffer accounting).

### Main entities (business perspective)

- **Scripted WebSocket Test Server**: The in-process offline peer that accepts connections, applies scripted behaviors, and exposes diagnostic buffers and counters for test assertions.
- **Connected Peer**: A single client session attached to the test server during a test; may receive and send frames independently of other peers.
- **Broadcast Delivery**: Sending the same message to every currently connected peer (existing capability).
- **Targeted Delivery**: Sending a message to one designated connected peer without affecting others (new capability).
- **Connection Churn**: Repeated connect/disconnect activity within or across tests that stresses peer lifecycle and resource reclamation.
- **Harness Diagnostic Buffers**: Ordered sent/received message histories and connection/disconnection counters used by tests to verify behavior.

## Q&A

**Q: Why is per-client messaging needed when `send_to_all` and separate server instances exist?**
A: Real WebSocket products routinely hold multiple simultaneous sessions to one endpoint. Broadcasting cannot distinguish peers; spawning separate server instances per peer does not exercise shared-server routing, concurrent peer lists, or selective server responses that downstream transport, session, and MCP stories must test against one loopback peer.

**Q: Why is explicit disconnection reclamation a harness requirement rather than relying on garbage collection?**
A: PYPOST-1129 verified leak-free lifecycle for standard cycles, but TD-1 notes that disconnected peers were only removed from the active list. Under high churn, delayed cleanup can leave resources accounted for longer than tests expect, risking flaky leak checks and CI instability. Prompt reclamation aligns with the harness's zero-leak guarantee for repeated startup/teardown.

**Q: Does this task change production WebSocket behavior?**
A: No. All work is confined to test infrastructure (`tests/websocket_echo_server.py` and related tests). Production transport and session code are out of scope.

**Q: Where did this requirement originate?**
A: Follow-up TD-1 (Low) in [`ai-tasks/PYPOST-1129/60-tech-debt.md`](../PYPOST-1129/60-tech-debt.md), ticketed as [PYPOST-1139](https://pypost.atlassian.net/browse/PYPOST-1139) under epic [PYPOST-1123](https://pypost.atlassian.net/browse/PYPOST-1123).

**Q: Is a new multi-client test mandatory in this 1 SP story?**
A: TD-1 listed multi-client selective targeting as an optional enhancement. Delivering the harness API and disconnect cleanup is the core obligation; a focused selective-delivery test is recommended in Definition of Done but may be deferred with explicit rationale if timeboxed to API-only delivery in architecture Step 2.
