# PYPOST-1137: WS-9 Bounded MCP WebSocket probe tool

## Programming Language

Python is the implementation language for the application runtime, MCP tool registration and schema generators, probe runners, event loop threading coordinators, daemon storage loaders, UI configuration widgets, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost supports interactive WebSocket communication and Model Context Protocol (MCP) server capabilities. AI agents and automated clients interacting with PyPost via MCP require a safe, deterministic, and bounded way to sample real-time WebSocket endpoints (e.g. streaming market data, live notifications, device telemetry, IoT feeds).

Unlike traditional request/response HTTP endpoints, WebSocket connections are long-lived and continuous. Permitting automated agents to open and hold persistent WebSocket connections indefinitely introduces severe operational risks: abandoned socket handles, runaway memory consumption, thread exhaustion, and lack of operator visibility in headless server deployments (`pypost-daemon`).

The goal of this task (WS-9) is to deliver a **Bounded MCP WebSocket Probe Tool**:
- **Bounded Sampling Pattern (D-5):** Replicate PyPost's proven Server-Sent Events (SSE) bounded probe pattern for WebSockets. The probe tool opens a connection, optionally sends an initial preset payload, collects incoming messages until the first of three deterministic stopping conditions (max messages, max duration, or a `stop_when` substring match), cleanly closes the socket (RFC 6455 code 1000), and returns a single structured, masked transcript.
- **Strict Hard Ceilings:** Enforce global operational ceilings (`ws_mcp_probe_max_messages`, `ws_mcp_probe_max_duration_ms`) that cannot be bypassed or exceeded by per-profile overrides or agent arguments.
- **Strict MCP Secret Isolation:** Ensure `list_tools` exposes only user-configured `mcp.request.*` variables as parameters; hidden environment keys and credentials remain strictly stripped from tool schemas and are merged only during tool execution.
- **Sanitized Transcripts:** Sanitize output transcripts using the existing HTTP MCP masking policy (`sanitize_text` with environment variables and hidden keys) before returning results to agents.
- **Guaranteed Thread Termination:** Execute probe sessions in a short-lived `QThread` (`WebSocketProbeRunner`) with its own event loop and hard deadline timer, guaranteeing that the runner thread always terminates and never outlives the MCP tool call under any condition (including errors, disconnections, and timeouts).
- **Headless Daemon Support:** Ensure the probe tool functions seamlessly under `pypost-daemon` without requiring a display server (X11/Wayland), with `daemon_storage` snapshot loaders extended to load WebSocket connection profiles.
- **Concurrency Governance:** Integrate probe executions into the process-wide `SessionSlots` coordinator (`ws_max_concurrent_sessions`), releasing slots on every exit path and returning an informative refusal message when limits are reached.
- **Audit & Metrics Observability:** Record all MCP probe tool calls in `McpActivityLog` and track execution timings and outcomes in Prometheus metrics (`websocket_probe_duration_seconds{outcome}`).

## User Stories

- As an **AI agent / MCP client**, I want to call an exposed WebSocket tool to sample a live real-time stream and receive a structured, sanitized transcript of the exchange, so that I can inspect real-time service status or verify live streaming outputs.
- As an **AI agent / MCP client**, I want the probe to terminate immediately when a specific expected pattern or keyword is received via the `stop_when` parameter, so that I do not have to wait for duration timeouts when the target event has already arrived.
- As an **AI agent / MCP client**, I want connection attempts at the concurrency limit to return a clean, non-crashing refusal response, so that I can handle capacity limits gracefully without failing my workflow.
- As a **developer / operator**, I want to expose selected WebSocket connection profiles as MCP tools with custom descriptions, parameter bindings, and default probe message presets in PyPost, so that my AI tools have access to necessary real-time capabilities.
- As a **developer**, I want to preview the generated MCP tool schema and parameter contract in the WebSocket editor UI, so that I can verify exactly what tools and parameters agents will see.
- As a **security officer**, I want tool schemas published in `list_tools` to expose only designated `mcp.request.*` parameters and strictly exclude hidden keys or environment secrets, so that sensitive credentials are never leaked to external agents.
- As a **security officer**, I want transcripts returned to agents to have sensitive keys and tokens redacted using PyPost's standard masking policy, so that confidential payloads are not exposed in LLM context windows.
- As a **system administrator**, I want WebSocket MCP probe tools to run reliably under `pypost-daemon` in headless server environments, so that automated agent workflows can execute without GUI overhead or virtual display servers.
- As a **site reliability engineer (SRE)**, I want all MCP probe calls, durations, and outcomes to be logged in the MCP activity log and measured with Prometheus histogram metrics, so that I can monitor probe latency and success rates.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Tool Schema & Parameter Isolation in `list_tools`:**
   - Exposed WebSocket profiles (`expose_as_mcp=True`) are published as tools in `list_tools`.
   - Tool schemas expose only `mcp.request.*` placeholders as parameters (along with optional probe arguments such as `stop_when`).
   - Hidden variables and environment-only keys are strictly excluded from tool schemas.
2. **Deterministic Bounded Execution in `call_tool`:**
   - `call_tool` resolves template variables, connects to the WebSocket endpoint using handshake headers and subprotocols from the profile, and sends the designated initial message preset (if `mcp_probe_preset_id` is set).
   - Inbound messages are collected until the FIRST of:
     - Message count reaches the effective limit (`mcp_probe_max_messages` override or global `ws_mcp_probe_max_messages`).
     - Execution duration reaches the effective limit (`mcp_probe_max_duration_ms` override or global `ws_mcp_probe_max_duration_ms`).
     - An incoming message body contains the `stop_when` substring (if provided as a tool argument).
   - The connection is cleanly closed with WebSocket close code 1000 ("probe complete").
   - The probe result is returned as a single masked transcript formatted as `List[TextContent]`.
3. **Strict Global Ceiling Enforcement:**
   - Per-profile overrides (`mcp_probe_max_messages`, `mcp_probe_max_duration_ms`) and tool arguments cannot exceed the global bounds configured in `AppSettings` (`ws_mcp_probe_max_messages`, `ws_mcp_probe_max_duration_ms`).
4. **Output Sanitization:**
   - Transcripts are sanitized using `sanitize_text` with active environment variables and hidden keys, matching the security policy applied to HTTP MCP tool results.
5. **Guaranteed Runner Thread Lifetime & Termination:**
   - `WebSocketProbeRunner` executes the probe on a short-lived `QThread` with its own event loop and a hard-deadline timer.
   - The runner thread terminates cleanly and never outlives the `call_tool` invocation under any exit condition (success, network error, TLS failure, or deadline timeout), as asserted by automated lifecycle tests.
6. **Headless Daemon Support:**
   - MCP WebSocket probe tools function correctly under `pypost-daemon` in headless mode without a display server (operating on a `QCoreApplication` event loop).
   - `pypost.core.daemon_storage` snapshot loaders are extended to load and snapshot `Collection.websockets` profiles.
7. **Audit Logging & Prometheus Metrics:**
   - Every probe execution is recorded in `McpActivityLog`.
   - Probe duration and execution outcomes are recorded in Prometheus histogram `websocket_probe_duration_seconds{outcome}` (outcomes: `success`, `timeout`, `limit_reached`, `error`).
8. **Concurrency Slot Governance (`SessionSlots`):**
   - Probe executions acquire a slot from `SessionSlots` before opening a socket and release the slot on every exit path.
   - When the process-wide ceiling `ws_max_concurrent_sessions` is reached, `call_tool` returns an informative refusal result without opening a socket or spawning worker threads.
9. **UI MCP Sub-Tab Preview:**
   - The WebSocket editor includes an MCP sub-tab providing tool preview (`format_mcp_tool_contract_preview`) and configuration options consistent with the HTTP request editor.
10. **Architecture & LOC Compliance:**
    - `pypost/models/websocket.py` remains unchanged (reusing model fields defined in WS-2).
    - `MCPServerImpl.register_tools` delegates tool registration and dispatch to `pypost/core/websocket_mcp_tools.py` without violating module LOC caps (`scripts/audit_baseline_metrics.py --check` passes).

## Task Description

### Problem Statement

In automated environments and LLM agent workflows via MCP, agents need the ability to inspect and interact with real-time systems. However, standard WebSocket connections are inherently bidirectional and persistent. If an agent initiates an unconstrained WebSocket connection, the socket may remain open indefinitely if the agent does not explicitly close it. This results in socket descriptor leaks, unbounded memory consumption, and zombie connections on the host machine.

Furthermore, in headless server environments managed by `pypost-daemon`, there is no GUI operator to monitor or terminate errant connections.

WS-9 addresses this by implementing a bounded probe mechanism: transforming WebSocket connections into deterministic, single-call MCP tools that sample the endpoint, collect bounded responses, close cleanly, and return a sanitized transcript.

### Scope

**In Scope:**
- Core probe logic and stopping condition evaluation in `pypost/core/websocket_probe.py`.
- Threaded execution runner in `pypost/core/qt/websocket_probe_runner.py` using a short-lived `QThread`, dedicated event loop, and hard deadline timer.
- MCP tool schema generation, registration, and dispatch in `pypost/core/websocket_mcp_tools.py` with delegating hook in `pypost/core/mcp_server_impl.py`.
- Extension of `pypost/core/daemon_storage.py` snapshot loaders to include `Collection.websockets`.
- MCP configuration and preview sub-tab in the WebSocket connection editor UI.
- Integration with `SessionSlots` for concurrency ceiling enforcement and refusal responses.
- Integration with `McpActivityLog` and `MetricsRegistry` (`websocket_probe_duration_seconds`).
- Transcript sanitization via `sanitize_text`.

**Out of Scope:**
- Persistent agent-held WebSocket sessions across multiple tool invocations (deferred as FU-3).
- Changes to persisted WebSocket models in `pypost/models/websocket.py` (fields were established in WS-2).
- Interactive GUI session stream presentation or filtering (handled in WS-4 and WS-5).

### Constraints and Assumptions

- **Bounded Execution:** Every probe execution must have a finite upper bound on both duration and message count.
- **No Thread Leaks:** The `QThread` running the probe must be joined and terminated before `call_tool` returns.
- **Zero Display Dependency:** The probe must run cleanly on `QCoreApplication` in headless environments without X11, Wayland, or `DISPLAY` environment variables.
- **Secret Redaction:** No sensitive tokens or secrets may be exposed in schemas or unmasked transcripts.
- **Non-Crashing Refusal:** Concurrency ceiling exhaustion must return a structured refusal result to the agent, not an unhandled exception or crash.

## Functional Requirements

- **FR-1: Tool Discovery & Schema Generation (`list_tools`)**:
  - Profiles with `expose_as_mcp=True` are published as MCP tools with naming convention `ws_{profile_name_sanitized}` or profile ID.
  - The tool schema description is populated from `mcp_description` or a default description.
  - Parameter definitions are extracted from `mcp_params` for placeholders matching `mcp.request.*`.
  - Hidden variables and environment-only keys are strictly excluded from tool schemas.
  - An optional tool argument `stop_when` (string) is supported for early match-based probe termination.

- **FR-2: Probe Execution Flow (`call_tool`)**:
  - Resolves template variables in URL, headers, query parameters, and initial message payloads using supplied tool arguments and environment context.
  - Checks and acquires a concurrency slot from `SessionSlots`.
  - Instantiates `WebSocketProbeRunner` and starts connection to the resolved endpoint.
  - Sends the initial message preset designated by `mcp_probe_preset_id` upon reaching `Open` state.
  - Buffers received text and binary frames up to the configured limits.

- **FR-3: Stopping Conditions & Close Handling**:
  - The probe terminates immediately upon the earliest occurrence of:
    1. Reaching message limit (`effective_max_messages = min(profile_override or global_default, global_ceiling)`).
    2. Reaching duration limit (`effective_max_duration_ms = min(profile_override or global_default, global_ceiling)`).
    3. Detecting a match for `stop_when` substring in any received message body.
    4. Receiving a server-initiated close or transport error.
  - Upon termination condition, the runner sends a WebSocket close frame (code 1000, reason "probe complete") and exits its event loop.

- **FR-4: Transcript Formatting & Sanitization**:
  - Formats probe events into a readable structured text transcript (including connect event, sent message, received messages with timestamps, and close event).
  - Sanitizes the entire transcript text using `sanitize_text(transcript, env_vars, hidden_keys)`.
  - Returns the sanitized transcript as a `List[TextContent]` response.

- **FR-5: Concurrency Ceiling & Refusal Handling**:
  - If `SessionSlots.acquire()` returns refusal (`allowed=False`), `call_tool` aborts before network initialization and returns a descriptive refusal message (e.g. `WebSocket probe refused: session limit reached`).
  - Slots are released reliably in a `finally` block on all exit paths.

- **FR-6: Daemon Storage Integration**:
  - `pypost/core/daemon_storage.py` snapshot loading functions are updated to load `websockets` from collection files so that exposed WebSocket tools are available under `pypost-daemon`.

- **FR-7: UI MCP Sub-Tab Preview**:
  - The WebSocket connection editor UI includes an MCP sub-tab displaying the formatted contract preview (`format_mcp_tool_contract_preview`), exposed parameter table, and probe limit settings.

## Non-Functional Requirements

- **NFR-1: Deterministic Termination**:
  - A hard deadline timer ensures the runner thread never hangs, even if the remote server fails to respond to close handshakes.
- **NFR-2: Thread Safety & Isolation**:
  - The `QThread` event loop runs independently of uvicorn's asyncio loop and the Qt main GUI thread.
- **NFR-3: Security & Masking**:
  - All secret values defined in active environments or marked as hidden are masked in both schemas and output transcripts.
- **NFR-4: Headless Execution**:
  - The probe runner requires only `QtCore` and `QtNetwork` / `QtWebSockets` and executes without GUI dependencies under `QT_QPA_PLATFORM=offscreen`.
- **NFR-5: Observability & Auditability**:
  - Probe executions are logged in `McpActivityLog` and tracked in `MetricsRegistry` with low-cardinality labels.

## Main Entities and Attributes

- **WebSocketConnection (MCP Attributes from WS-2)**:
  - `expose_as_mcp: bool`: Flag indicating if profile is published to MCP.
  - `mcp_description: str`: Custom description for the generated MCP tool.
  - `mcp_params: Dict[str, McpToolParam]`: Schema parameter configurations.
  - `mcp_probe_preset_id: Optional[str]`: ID of the message preset sent immediately after connection.
  - `mcp_probe_max_messages: Optional[int]`: Per-profile message limit override.
  - `mcp_probe_max_duration_ms: Optional[int]`: Per-profile duration limit override in milliseconds.

- **WebSocketProbeConfig**:
  - `target: HandshakeTarget`: Resolved URL, headers, subprotocols.
  - `initial_payload: Optional[str]`: Resolved initial message to send.
  - `max_messages: int`: Effective message limit.
  - `max_duration_ms: int`: Effective duration limit.
  - `stop_when: Optional[str]`: Substring stopping condition.

- **WebSocketProbeResult**:
  - `outcome: str`: `"success"`, `"timeout"`, `"limit_reached"`, `"error"`, `"refused"`.
  - `messages_received: int`: Count of received messages.
  - `duration_ms: float`: Total execution duration in milliseconds.
  - `transcript: str`: Formatted probe transcript.
  - `close_code: Optional[int]`: WebSocket close code.
  - `error_message: Optional[str]`: Error description if failed.

## User Scenarios

### Scenario 1: Sampling Live Market Ticker Stream
1. An operator configures a WebSocket profile for `wss://stream.binance.com/ws/btcusdt@trade` with `expose_as_mcp=True`, `mcp_probe_max_messages=5`, and `mcp_probe_max_duration_ms=5000`.
2. An AI agent calls `list_tools` and sees tool `ws_binance_trade_stream`.
3. The agent calls `ws_binance_trade_stream()`.
4. `WebSocketProbeRunner` starts, acquires a concurrency slot, connects, receives 5 trade event messages in 120 ms, sends close code 1000, and terminates the runner thread.
5. The agent receives a structured transcript containing the 5 received JSON messages.
6. The concurrency slot is released, and `websocket_probe_duration_seconds{outcome="limit_reached"}` is recorded.

### Scenario 2: Early Termination via `stop_when`
1. A developer exposes a deployment status notification stream `wss://ci.example.com/builds/stream`.
2. An agent calls the probe tool with argument `stop_when="BUILD_FINISHED"`.
3. The probe connects and receives 2 intermediate status messages (`"BUILD_START"`, `"BUILD_PROGRESS"`).
4. The 3rd message contains `"BUILD_FINISHED: SUCCESS"`.
5. The runner detects the substring match, immediately closes the socket, and returns the 3-message transcript without waiting for the full 10-second timeout.

### Scenario 3: Concurrency Ceiling Reached
1. All `ws_max_concurrent_sessions` slots are occupied by active interactive tabs.
2. An agent calls `ws_market_feed()`.
3. `SessionSlots.acquire()` returns `allowed=False, reason="max_concurrent"`.
4. `call_tool` aborts without opening a network connection and returns: `WebSocket probe refused: session limit reached (8 of 8 active sessions). Disconnect an existing session to proceed.`
5. `websocket_session_start_refused_total{reason="max_concurrent"}` is incremented.

### Scenario 4: Secret Redaction in Probe Transcript
1. A WebSocket profile uses `wss://api.example.com/stream?token={{SECRET_API_TOKEN}}` and sends an authentication preset containing `{"auth": "{{SECRET_KEY}}"}`.
2. The agent calls the probe tool.
3. The probe runs, authenticates, and collects messages.
4. Before returning to the agent, the transcript passes through `sanitize_text()`.
5. `SECRET_API_TOKEN` and `SECRET_KEY` are replaced with `***` in the returned transcript.

## Q&A

| Question | Answer |
| --- | --- |
| Why is MCP WebSocket support implemented as a bounded probe rather than a persistent agent-held session? | Persistent sessions held by remote LLM agents introduce critical risks of unclosed zombie connections, socket leaks, and unbounded buffer memory growth. Bounded probes guarantee deterministic termination while satisfying agent needs for real-time sampling and verification. |
| How is thread synchronization handled between MCP uvicorn asyncio loop and Qt? | MCP tool execution happens on uvicorn's worker thread pool. `WebSocketProbeRunner` starts a dedicated short-lived `QThread` with its own `QEventLoop`, runs the probe to completion or hard deadline, and rejoins cleanly before returning the result. |
| How are secrets protected from exposure in `list_tools`? | PyPost's `McpSecretsPolicy` inspects template placeholders and includes only `mcp.request.*` variables in published schemas. Environment variables and hidden keys are excluded from `list_tools` and resolved only at execution time. |
| Can a profile override exceed global probe duration or message caps? | No. Effective limits are computed as `min(profile_override or global_default, global_ceiling)`. Global ceilings configured in `AppSettings` take precedence and cannot be bypassed. |
| How does the probe work in headless mode under `pypost-daemon`? | QtWebSockets depends only on QtCore and QtNetwork. Under `pypost-daemon`, the probe operates on a `QCoreApplication` loop with no requirement for a display server (X11/Wayland). |
| What happens if a target server does not respond to the close handshake? | A hard deadline timer on the runner `QThread` forces socket abort and loop termination, ensuring the worker thread never hangs indefinitely. |
