# PYPOST-1136: WS-10 Settings, session ceiling, metrics and logging

## Programming Language

Python is the implementation language for the application runtime, data models, configuration schemas, metrics registry, logging policies, user interface settings widgets, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost supports interactive WebSocket communication through Epic PYPOST-1123. Foundational stories have implemented the transport engine (WS-1), persistent models (WS-2), bounded stream buffers (WS-3), interactive session tabs (WS-4), and stream inspection tools (WS-5).

In enterprise, team, and server-hosted deployments, operators and system administrators require strict controls to bound resource utilization, prevent memory bloat or file-descriptor exhaustion, monitor system health, and diagnose network and protocol issues without leaking sensitive user credentials or payloads into observability pipelines.

The goal of this task (WS-10) is to deliver a comprehensive **Settings, Session Ceiling, Metrics, and Logging Framework** for WebSocket connections:
- **Configurable Global Bounds:** Provide operator-configurable global settings in `AppSettings` (and the Settings dialog) covering stream buffer capacities, per-session memory budgets, incoming frame/message limits, display truncation caps, default heartbeat/reconnect policies, MCP probe bounds, and concurrent connection ceilings.
- **Process-Wide Concurrent Session Ceiling (D-14):** Enforce an atomic, process-wide concurrency ceiling (`ws_max_concurrent_sessions`) across both interactive GUI session tabs and background/MCP probe workers. At the ceiling, new connection attempts are cleanly and deterministically refused with an informative message and refusal counter increment without stalling, queueing, or corrupting state.
- **Zero-Session Lockdown Mode:** Support `ws_max_concurrent_sessions = 0` as a deliberate lockdown mode for restricted deployments, immediately blocking all connection attempts with an explicit operator-policy explanation.
- **Immediate Runtime Reconfiguration:** Ensure all global bounds and defaults are dynamically editable at runtime and take effect for subsequent sessions without requiring an application restart.
- **Standardized Prometheus Observability:** Expose low-cardinality, well-structured Prometheus metrics for session lifecycles, active connections (gauge), frame/byte throughput, buffer drops, reconnect attempts, refusal counts, and probe timings under `/metrics`.
- **Zero-Leak Structured Logging:** Provide structured, security-audited key-value logging for all WebSocket lifecycle and anomaly events, guaranteeing that no message payloads, header values, or unmasked URLs are ever emitted at any log level.
- **System Documentation & Audit Integrity:** Document all Prometheus metrics in `doc/prometheus_monitoring.md` and log events in `doc/dev/logging.md`, while maintaining baseline architectural and LOC constraints verified by `scripts/audit_baseline_metrics.py --check`.

## User Stories

- As a **system administrator / operator**, I want to configure a process-wide ceiling on concurrent WebSocket connections (`ws_max_concurrent_sessions`), so that multiple active tabs or automated agents cannot exhaust machine memory or network socket limits.
- As an **operator in a restricted environment**, I want to set the concurrency ceiling to `0`, so that WebSocket connections are completely locked down and disabled across the entire application with an explicit explanatory message.
- As an **operator monitoring PyPost via Prometheus**, I want standardized metrics for active sessions, message/byte volume, reconnects, dropped entries, and refusals, so that I can monitor connection health and track system utilization in Grafana dashboards.
- As a **user attempting to connect when the ceiling is reached**, I want an immediate and clear notification explaining that the session limit is reached (e.g. `8 of 8 WebSocket sessions are already open — disconnect one to start another`), so that I know exactly why the connection did not start and how to proceed.
- As an **automated agent (MCP tool caller)**, I want connection attempts at the concurrency limit to return a clean, non-crashing refusal response, so that I can back off or retry later without breaking the agent loop.
- As a **developer tweaking application preferences**, I want to adjust stream memory budgets, message size limits, and default heartbeat/reconnect intervals in the Settings dialog without restarting PyPost, so that new settings take effect immediately on subsequent connections.
- As a **site reliability engineer (SRE) reviewing application logs**, I want structured key-value log entries for connection attempts, handshakes, terminations, and errors, so that I can troubleshoot network failures quickly.
- As a **security officer**, I want guarantees that sensitive authentication tokens, authorization headers, raw query parameters, and message payloads are never written to application log files at any level, so that system logs remain safe and compliant.
- As a **developer maintaining code quality**, I want slot management and limit counters to be purely unit-testable without spinning up Qt GUI applications, so that slot acquisition and release edge cases (failures, timeouts, peer closes) are robustly tested and cannot leak.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Configurable Settings in `AppSettings` & Settings UI:**
   - All `ws_*` configuration fields are declared with default values in `pypost/models/settings.py`:
     - `ws_max_stream_entries` (default: 5,000)
     - `ws_session_memory_budget_bytes` (default: 67,108,864 = 64 MiB)
     - `ws_max_incoming_message_bytes` (default: 8,388,608 = 8 MiB)
     - `ws_display_truncate_bytes` (default: 262,144 = 256 KiB)
     - `ws_default_heartbeat` (default: enabled, 30s interval, 10s timeout)
     - `ws_default_reconnect` (default: enabled, 5 attempts, 1.0s initial delay, 2.0x backoff, 30.0s max delay)
     - `ws_mcp_probe_max_messages` (default: 10)
     - `ws_mcp_probe_max_duration_ms` (default: 10,000)
     - `ws_max_concurrent_sessions` (default: 8)
   - A dedicated WebSocket configuration section/group is added to the Settings dialog (`pypost/ui/widgets/settings_dialog.py`).
   - Every setting is editable and takes effect immediately for the next connection attempt without requiring an application restart.
2. **Process-Wide Concurrent Session Ceiling (`SessionSlots`):**
   - Thread-safe slot manager `SessionSlots` is implemented in `pypost/core/websocket_session_policy.py` using `threading.Lock` to coordinate GUI-thread connections and MCP threadpool probe runners.
   - Slot acquisition occurs upon connection initiation; slot release occurs upon any terminal state transition (`Idle`, `Failed`, closed) or probe completion.
   - When active sessions reach `ws_max_concurrent_sessions = N`, the `N+1`-th connect attempt is refused:
     - The connection badge remains `Idle`.
     - No network socket or thread is opened.
     - An inline message and stream lifecycle entry state: `N of N WebSocket sessions are already open — disconnect one to start another`.
     - The Connect button remains active to allow subsequent retries.
     - Metric `websocket_session_start_refused_total{reason="max_concurrent"}` is incremented.
     - Log event `websocket_session_refused` is emitted.
   - Freeing any slot (disconnecting or closing another session) immediately allows subsequent connection attempts to succeed.
3. **Lockdown Mode (`ws_max_concurrent_sessions = 0`):**
   - Setting `ws_max_concurrent_sessions = 0` blocks all connection attempts immediately.
   - The UI and lifecycle log explicitly state that WebSocket connections are disabled by operator policy.
   - Metric `websocket_session_start_refused_total{reason="disabled"}` is incremented.
4. **Leak-Free Slot Release Verification:**
   - Unit tests verify `SessionSlots` in pure Python without Qt dependencies.
   - Tests assert that slots are released under all terminal conditions: clean user disconnect, server-initiated close, connection handshake rejection, TLS verification failure, heartbeat timeout, and probe deadline expiry.
5. **Prometheus Metrics Registry:**
   - All new WebSocket metrics are registered in `pypost/core/metrics_registry.py` and scrape cleanly under the Prometheus `/metrics` endpoint:
     - `websocket_sessions_opened_total{outcome}` (outcomes: `success`, `failure`, `timeout`, `tls_rejected`)
     - `websocket_sessions_closed_total{reason}` (reasons: `clean`, `peer_close`, `heartbeat_timeout`, `transport_error`, `reconnect_exhausted`, `forced`)
     - `websocket_messages_total{direction,kind}` (direction: `inbound`, `outbound`; kind: `text`, `binary`, `ping`, `pong`)
     - `websocket_message_bytes_total{direction}` (direction: `inbound`, `outbound`)
     - `websocket_stream_entries_dropped_total{reason}` (reason: `capacity`, `memory_budget`)
     - `websocket_reconnect_attempts_total{outcome}` (outcome: `scheduled`, `succeeded`, `exhausted`)
     - `websocket_active_sessions` (gauge)
     - `websocket_session_start_refused_total{reason}` (reason: `max_concurrent`, `disabled`)
     - `websocket_probe_duration_seconds{outcome}` (histogram; outcome: `success`, `timeout`, `limit_reached`, `error`)
   - All metric labels are strictly bounded to documented, fixed low-cardinality string values.
6. **Zero-Leak Logging & Secret Redaction:**
   - Structured key=value log events are emitted for all lifecycle events per `doc/dev/logging.md`.
   - Invariant: Message payloads, handshake header values, unmasked query parameters, and plain secret strings never appear in logs at any level (DEBUG, INFO, WARNING, ERROR).
   - An automated test injects a known sensitive token and verifies with pytest `caplog` that the token never appears in emitted logs.
7. **Documentation Updates:**
   - `doc/prometheus_monitoring.md` is updated with full metric names, types, label sets, and descriptions.
   - `doc/dev/logging.md` is updated with all WebSocket log event names, key=value field schemas, and redaction rules.
8. **Quality Gate & Baseline Audit:**
   - `scripts/audit_baseline_metrics.py --check` passes and regression snapshots are updated.
   - All unit, integration, and GUI tests pass under `QT_QPA_PLATFORM=offscreen`.

## Task Description

### Problem Statement

In previous stories (WS-1 through WS-5), PyPost established the mechanisms for creating WebSocket connections, handling streaming frames, buffering messages, and inspecting live streams. However, without centralized settings management, concurrency controls, and comprehensive observability, the application has critical operational vulnerabilities:
1. **Unbounded Concurrency:** Opening dozens of simultaneous tabs or triggering parallel MCP probe calls can overload system resources, leak file descriptors, and exhaust available memory.
2. **Lack of Global Operational Limits:** Operators cannot tune default buffer sizes, message size ceilings, or heartbeat/reconnect intervals globally across all profiles from a central settings pane.
3. **Black-Box Operations:** System administrators and SREs have no visibility into active WebSocket sessions, message volume, byte counts, buffer drop rates, or connection failures via standard Prometheus monitoring tools.
4. **Troubleshooting & Security Risks:** Debugging connection and protocol issues requires structured logging, but logging raw frames or connection URLs poses severe security risks of leaking API keys, bearer tokens, or sensitive payload data.

WS-10 solves these challenges by providing a robust, production-grade settings, concurrency governance, metrics collection, and secure logging foundation.

### Scope

**In Scope:**
- Declaration of all `ws_*` settings fields on `AppSettings` with default values and validation rules.
- Implementation of a dedicated WebSocket settings section in the PyPost Settings dialog.
- Implementation of the `SessionSlots` process-wide concurrency coordinator with atomic check-and-acquire mechanics and fail-safe release logic.
- UI handling for connection refusal at the ceiling (informative message, lifecycle entry, `Idle` badge preservation, retry readiness).
- Implementation of lockdown mode (`ws_max_concurrent_sessions = 0`).
- Registration and tracking of all WebSocket Prometheus metrics (counters, gauge, histogram) with low-cardinality labels.
- Emission of structured key-value log events for connection lifecycle, reconnects, drops, and refusals.
- Secret sanitization in all logging pathways and automated `caplog` verification.
- Documentation updates to `doc/prometheus_monitoring.md` and `doc/dev/logging.md`.
- Baseline metrics audit check verification (`scripts/audit_baseline_metrics.py --check`).

**Out of Scope:**
- Prometheus alerting rules and external alertmanager configurations.
- Dynamic runtime rate limiting per individual message/frame (handled via stream buffer eviction policies in WS-3).
- Custom TLS certificate management and SSL error override dialogs (handled in WS-8).
- Implementation of MCP probe tools themselves (handled in WS-9; WS-10 provides the shared concurrency slot integration and probe metrics).

### Constraints and Assumptions

- **Immediate Reconfiguration:** Modifying any WebSocket setting in the Settings dialog must apply immediately to subsequent connection attempts without restarting the application.
- **Thread Safety:** `SessionSlots` must safely coordinate slot acquisition and release across GUI main thread operations and background worker threads (such as MCP probe threads) using thread-safe synchronization primitives (`threading.Lock`).
- **No Ambience / Pure Testability:** Concurrency slot management and metrics recording must be testable in headless Python environments without requiring Qt GUI instantiation.
- **Zero Sensitive Data in Observability Pipelines:** URLs in logs must always be sanitized via `sanitize_text`, header values must be excluded, and message payload text must never be logged.
- **Fixed Metric Cardinality:** Metric label values must only use predefined, closed enums/string sets (e.g. `direction="inbound"|"outbound"`) to prevent Prometheus time-series explosion.

## Functional Requirements

- **FR-1: Global WebSocket Settings in AppSettings**:
  - `AppSettings` must include configurable fields for:
    - `ws_max_stream_entries`: Maximum retained stream entries per session (default: 5,000).
    - `ws_session_memory_budget_bytes`: Memory budget in bytes per session buffer (default: 64 MiB).
    - `ws_max_incoming_message_bytes`: Maximum allowed incoming message size passed to transport (default: 8 MiB).
    - `ws_display_truncate_bytes`: Per-entry display truncation threshold (default: 256 KiB).
    - `ws_default_heartbeat`: Default `HeartbeatPolicy` for newly created profiles (enabled: True, interval: 30s, timeout: 10s).
    - `ws_default_reconnect`: Default `ReconnectPolicy` for newly created profiles (enabled: True, max_attempts: 5, initial_delay: 1.0s, multiplier: 2.0, max_delay: 30.0s).
    - `ws_mcp_probe_max_messages`: Hard ceiling for MCP probe messages (default: 10).
    - `ws_mcp_probe_max_duration_ms`: Hard ceiling for MCP probe execution time (default: 10,000 ms).
    - `ws_max_concurrent_sessions`: Process-wide concurrent session ceiling (default: 8).
  - All settings must be deserialized with safe defaults if omitted from `settings.json`.

- **FR-2: Settings Dialog UI Integration**:
  - The PyPost Settings dialog must provide a dedicated section or group for WebSocket configuration.
  - Users can adjust stream caps, memory limits, message size limits, concurrency ceilings, and default heartbeat/reconnect parameters.
  - Saving settings updates `AppSettings` dynamically and applies immediately to subsequent connections.

- **FR-3: Process-Wide Concurrency Limiting (`SessionSlots`)**:
  - A thread-safe `SessionSlots` class manages slot acquisition and release.
  - `acquire(session_id)` checks if `active_count < ws_max_concurrent_sessions`. If slots are available, it increments the count and returns success.
  - If the ceiling is reached, `acquire()` returns a refusal result (`reason="max_concurrent"`).
  - `release(session_id)` decrements the active count and ensures idempotent release (calling release multiple times for the same session does not decrement below zero).

- **FR-4: Connection Refusal User Experience**:
  - When connection initiation is refused due to the concurrency ceiling:
    - The connection state remains `Idle` (the state badge does not transition to `Connecting` or `Failed`).
    - No network socket is opened.
    - An inline notification/status and a stream lifecycle entry report: `N of N WebSocket sessions are already open — disconnect one to start another`.
    - The Connect button remains enabled, allowing immediate retry once a slot is freed.
    - `websocket_session_start_refused_total{reason="max_concurrent"}` is incremented.
    - Log event `websocket_session_refused` is recorded.

- **FR-5: Concurrency Lockdown Mode (`ws_max_concurrent_sessions = 0`)**:
  - When `ws_max_concurrent_sessions` is set to `0`:
    - All connection attempts are immediately blocked.
    - The UI displays an explicit message indicating WebSocket connections are disabled by operator policy.
    - `websocket_session_start_refused_total{reason="disabled"}` is incremented.

- **FR-6: Prometheus Metrics Collection & Scraping**:
  - The metrics registry must track and expose the following metrics on `/metrics`:
    - `websocket_sessions_opened_total{outcome}`: Counter tracking total opened sessions (outcomes: `success`, `failure`, `timeout`, `tls_rejected`).
    - `websocket_sessions_closed_total{reason}`: Counter tracking session closures (reasons: `clean`, `peer_close`, `heartbeat_timeout`, `transport_error`, `reconnect_exhausted`, `forced`).
    - `websocket_messages_total{direction,kind}`: Counter tracking messages sent/received (direction: `inbound`, `outbound`; kind: `text`, `binary`, `ping`, `pong`).
    - `websocket_message_bytes_total{direction}`: Counter tracking message payload byte volumes (direction: `inbound`, `outbound`).
    - `websocket_stream_entries_dropped_total{reason}`: Counter tracking evicted stream entries (reasons: `capacity`, `memory_budget`).
    - `websocket_reconnect_attempts_total{outcome}`: Counter tracking reconnect attempts (outcomes: `scheduled`, `succeeded`, `exhausted`).
    - `websocket_active_sessions`: Gauge tracking the instantaneous number of active sessions.
    - `websocket_session_start_refused_total{reason}`: Counter tracking refused session starts (reasons: `max_concurrent`, `disabled`).
    - `websocket_probe_duration_seconds{outcome}`: Histogram tracking MCP probe durations (outcomes: `success`, `timeout`, `limit_reached`, `error`).

- **FR-7: Structured Lifecycle & Security Logging**:
  - The application must emit structured log events using `snake_case key=value` format for:
    - `websocket_connect_initiated`: `session_id`, `profile_id`, `url_masked`, `subprotocols`
    - `websocket_connected`: `session_id`, `subprotocol`, `handshake_ms`
    - `websocket_handshake_failed`: `session_id`, `category`, `detail_len`
    - `websocket_closed`: `session_id`, `close_code`, `peer_initiated`, `duration_s`
    - `websocket_reconnect_scheduled`: `session_id`, `attempt`, `max_attempts`, `delay_ms`
    - `websocket_reconnect_exhausted`: `session_id`, `attempts`
    - `websocket_heartbeat_timeout`: `session_id`, `timeout_s`
    - `websocket_stream_overflow`: `session_id`, `dropped`, `reason`
    - `websocket_session_refused`: `profile_id`, `reason`, `active`, `limit`
    - `websocket_probe_completed`: `tool`, `outcome`, `messages`, `duration_ms`
  - URL values in log events must always be masked using `sanitize_text` to redact query parameter secrets.
  - Frame payload bodies and request header values must never be logged.

- **FR-8: Operational & Developer Documentation**:
  - `doc/prometheus_monitoring.md` must document all WebSocket Prometheus metrics and label specifications.
  - `doc/dev/logging.md` must document all WebSocket structured log events, key=value formats, and secret-handling constraints.

## Non-Functional Requirements

- **NFR-1: Concurrency & Thread Safety**:
  - `SessionSlots` must be strictly thread-safe across GUI threads and background worker/threadpool threads using `threading.Lock`.
  - Atomic check-and-increment operations prevent race conditions when multiple sessions or probes start simultaneously.
- **NFR-2: Fail-Safe Resource Release**:
  - Slot release must be guaranteed under all normal and exceptional termination conditions, including unhandled network exceptions, process aborts, and test teardowns.
- **NFR-3: Strict Secret Isolation**:
  - Sensitive environment variable values, bearer tokens, passwords, and message payloads must never appear in cleartext in standard logging channels at any log level.
- **NFR-4: Low Metric Cardinality**:
  - Metric labels must use closed sets of discrete enumeration values, avoiding dynamic user strings or URLs in label sets to prevent metric cardinality explosion.
- **NFR-5: Architectural Modularity & Headless Testability**:
  - `SessionSlots` and metric tracking policies must remain completely Qt-free and fully testable in pure Python unit test environments without creating a GUI application.
- **NFR-6: Performance & Low Overhead**:
  - Slot acquisition, metrics incrementing, and structured logging must add negligible execution overhead (<0.1 ms per event).

## Main Entities and Attributes

- **AppSettings WebSocket Bounds**:
  - `ws_max_stream_entries: int` (Default: 5000)
  - `ws_session_memory_budget_bytes: int` (Default: 67108864)
  - `ws_max_incoming_message_bytes: int` (Default: 8388608)
  - `ws_display_truncate_bytes: int` (Default: 262144)
  - `ws_default_heartbeat: HeartbeatPolicy`
  - `ws_default_reconnect: ReconnectPolicy`
  - `ws_mcp_probe_max_messages: int` (Default: 10)
  - `ws_mcp_probe_max_duration_ms: int` (Default: 10000)
  - `ws_max_concurrent_sessions: int` (Default: 8)

- **SessionSlots**:
  - `max_slots: int`: Configured process-wide limit.
  - `active_slots: Set[str]`: Set of active session IDs currently holding slots.
  - `lock: threading.Lock`: Mutex synchronizing state mutations.
  - Methods: `acquire(session_id: str) -> SlotAcquireResult`, `release(session_id: str) -> None`, `active_count() -> int`, `set_max_slots(limit: int) -> None`.

- **SlotAcquireResult**:
  - `allowed: bool`: True if the slot was granted; False if refused.
  - `reason: Optional[str]`: `"max_concurrent"` or `"disabled"` when refused.
  - `active_count: int`: Number of active sessions at time of check.
  - `limit: int`: Configured concurrency limit.

- **MetricsRegistry WebSocket Metrics**:
  - `websocket_sessions_opened_total`: Counter `[outcome]`
  - `websocket_sessions_closed_total`: Counter `[reason]`
  - `websocket_messages_total`: Counter `[direction, kind]`
  - `websocket_message_bytes_total`: Counter `[direction]`
  - `websocket_stream_entries_dropped_total`: Counter `[reason]`
  - `websocket_reconnect_attempts_total`: Counter `[outcome]`
  - `websocket_active_sessions`: Gauge
  - `websocket_session_start_refused_total`: Counter `[reason]`
  - `websocket_probe_duration_seconds`: Histogram `[outcome]`

- **Log Events**:
  - Structured events for `websocket_connect_initiated`, `websocket_connected`, `websocket_handshake_failed`, `websocket_closed`, `websocket_reconnect_scheduled`, `websocket_reconnect_exhausted`, `websocket_heartbeat_timeout`, `websocket_stream_overflow`, `websocket_session_refused`, `websocket_probe_completed`.

## User Scenarios

### Scenario 1: Reaching the Concurrency Ceiling
1. An operator sets `ws_max_concurrent_sessions = 3` in `settings.json`.
2. A developer opens 3 WebSocket tabs and connects each to a different backend service.
3. All 3 tabs successfully connect; `websocket_active_sessions` gauge reads `3`.
4. The developer opens a 4th tab and clicks **Connect**.
5. `SessionSlots.acquire()` determines that 3 of 3 slots are occupied and refuses the connection.
6. The 4th tab remains in `Idle` state without opening a socket.
7. An inline notice and stream lifecycle entry state: `3 of 3 WebSocket sessions are already open — disconnect one to start another`.
8. `websocket_session_start_refused_total{reason="max_concurrent"}` increments by 1, and `websocket_session_refused` log event is recorded.
9. The developer disconnects tab 1. Tab 1 transitions to `Idle` and calls `SessionSlots.release()`. `websocket_active_sessions` decreases to `2`.
10. The developer clicks **Connect** on tab 4. The connection is granted and connects successfully.

### Scenario 2: Zero-Session Lockdown Mode
1. In a secure sandbox deployment, the system administrator configures `ws_max_concurrent_sessions = 0`.
2. A user opens PyPost, loads a WebSocket profile, and clicks **Connect**.
3. The connection is immediately rejected before any network initialization.
4. The UI displays an operator policy notice: `WebSocket connections are disabled by operator policy (ws_max_concurrent_sessions=0)`.
5. `websocket_session_start_refused_total{reason="disabled"}` increments by 1.

### Scenario 3: Modifying Global Settings at Runtime
1. A developer testing high-bandwidth video metadata streams notices that 8 MiB messages are being rejected.
2. The developer opens the **Settings** dialog and navigates to the **WebSocket** section.
3. The developer increases **Max Incoming Message Size** from 8 MiB to 16 MiB and **Session Memory Budget** from 64 MiB to 128 MiB.
4. The developer clicks **Save**.
5. The next connection attempt uses the updated 16 MiB incoming message size limit without requiring an application restart.

### Scenario 4: Prometheus Metrics Scraping during Active Session
1. A Prometheus server scrapes PyPost's `/metrics` endpoint.
2. A client connects to `ws://example.com/feed` and receives 500 JSON messages (totaling 120 KB).
3. The Prometheus scrape returns:
   - `websocket_sessions_opened_total{outcome="success"} 1`
   - `websocket_active_sessions 1`
   - `websocket_messages_total{direction="inbound",kind="json"} 500`
   - `websocket_message_bytes_total{direction="inbound"} 122880`
4. When the session closes cleanly, the scrape returns:
   - `websocket_sessions_closed_total{reason="clean"} 1`
   - `websocket_active_sessions 0`

### Scenario 5: Secret Redaction in Structured Logs
1. A user connects to `wss://api.example.com/v1/stream?api_key=secret_token_12345` with a custom `Authorization: Bearer my_secret_token` header.
2. PyPost emits `websocket_connect_initiated`:
   `websocket_connect_initiated session_id=sess_1 profile_id=prof_1 url_masked=wss://api.example.com/v1/stream?api_key=*** subprotocols=0`
3. The log entry contains the masked URL and omits header values.
4. An automated test asserts that `secret_token_12345` and `my_secret_token` are absent from `caplog` records.

## Q&A

| Question | Answer |
| --- | --- |
| Why is a global session ceiling necessary if per-session stream buffers are already bounded? | While WS-3 bounds memory and entry counts per session (e.g. 64 MiB / 5,000 entries), having unconstrained concurrent sessions means ten open tabs consume 640 MiB and hold multiple socket descriptors. A global ceiling guarantees overall process resource bounds. |
| Why is slot acquisition handled atomically with `threading.Lock`? | PyPost supports both GUI interactive tabs (on the main Qt thread) and MCP automated probe tools (executed in background thread pools). A mutex ensures that concurrent connect requests from UI and MCP agents cannot exceed the ceiling due to race conditions. |
| Why is connection refusal non-fatal and non-queueing? | Queueing connection attempts can lead to unexpected background connection bursts when older tabs close. Refusing immediately with a clear message lets the user or agent decide when to disconnect an unused session and retry. |
| What is the purpose of the lockdown mode (`ws_max_concurrent_sessions = 0`)? | Enterprise administrators often need to disable WebSocket functionality completely in specific environments without removing or modifying the application binaries. Setting the ceiling to 0 provides an explicit, documented policy lockdown. |
| Why are Prometheus metric labels restricted to fixed low-cardinality values? | Prometheus time-series storage degrades severely if high-cardinality values (such as URLs, session IDs, or timestamps) are included in labels. Restricting labels to fixed enums (e.g. `direction`, `outcome`, `reason`) maintains high scraping performance. |
| Why are message bodies and header values excluded from logs even at DEBUG level? | WebSocket messages and headers frequently transmit authentication tokens, personal identifying information, and sensitive business data. Preventing sensitive data from entering logs protects against accidental credential leakage into central log aggregators. |
| Do settings changes require an application restart? | No. Global bounds and default policies are read dynamically from `AppSettings` upon each connection initiation, taking effect immediately for all subsequent sessions. |
