# PYPOST-1135: WS-7 Environments, templating and secret masking

## Programming Language

Python is the implementation language for the application runtime, data models, user interface presenters/views, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost's core value proposition is its unified workspace environment system and defense-in-depth secret protection. In HTTP workflows, users seamlessly parameterize requests using `{{ VAR }}` syntax across URLs, headers, and bodies, while sensitive tokens and credentials stored in hidden environment variables are protected from accidental exposure across the UI, clipboard, exports, logs, and telemetry.

With the addition of real-time WebSocket communication (Epic PYPOST-1123), real-time sessions must inherit PyPost's environment variables, dynamic templating, and secret masking guarantees without compromise.

The goal of this task (WS-7) is to make this differentiator real for WebSocket sessions:
- **Consistent Environment Parameterization:** Allow users to use `{{ VARIABLE }}` placeholders in WebSocket URLs, query parameters, handshake headers, requested subprotocols, and message payloads (composer text, saved presets, sequence steps), enabling connection profiles to effortlessly adapt across development, staging, and production environments.
- **Deterministic Resolution Timing:** Enforce clear, unambiguous lifecycle resolution rules:
  - **Handshake parameters** (URL, query parameters, headers, subprotocols) resolve *once at connection time*, ensuring the stream log accurately represents what was actually transmitted across the wire during the handshake without silent mid-session drift.
  - **Message payloads** (composer, presets, sequence steps) resolve *dynamically per send*, allowing environment variables captured mid-session (e.g. session tokens or order IDs) to be utilized immediately in subsequent outgoing messages.
- **Template Injection Defense (Security Invariant):** Guarantee that incoming server payloads are *never* rendered through the template engine. Server-controlled text containing `{{ ... }}` must be treated strictly as literal data, preventing unintentional variable expansion or malicious injection.
- **Interactive Variable Inspection:** Provide variable-aware hover tooltips across all WebSocket input fields (URL, headers, query params, subprotocols, composer, presets, sequences), displaying the active variable value, or `********` if marked hidden, matching HTTP editor behavior.
- **Seamless Environment Switching:** Switching the active workspace environment immediately applies new variable sets to subsequent connection attempts and outgoing messages without requiring manual edits to connection profiles.
- **Two-Tier Defense-in-Depth Secret Masking:**
  - **Tier 1 (Stream Ingestion / Live Display):** Exact replacement of hidden environment variable values with standard placeholders (`HIDDEN_PLACEHOLDER` / `***`) before entries enter the stream buffer. Incoming server payloads undergo exact hidden-value replacement only (avoiding destructive heuristic mangling of server payloads under inspection).
  - **Tier 2 (Egress / Outside Process):** Full heuristic sanitization (`sanitize_text`) on all data leaving the process via clipboard copy, file export (JSON and plain-text transcripts), and agent/MCP transcripts.
- **Strict Observability and Logging Hygiene:** Prohibit logging message payloads, handshake header values, or resolved URLs containing sensitive query parameters. Increment the Prometheus/OpenTelemetry counter `hidden_value_masks_applied_total{surface="websocket"}` whenever a hidden value is masked.
- **Seam and Architecture Invariant Preservation:** Extend the existing ingestion pipeline built in WS-4 without rewiring architectural boundaries: `WebSocketPresenter` remains the single point of masking coordination, and `StreamListModel.append_batch` remains the sole writer to `MessageStream`.

## User Stories

- As an **API developer**, I want to use `{{ BASE_WS_URL }}` and `{{ AUTH_TOKEN }}` in my WebSocket endpoint URL and handshake headers, so that I can reuse the same connection profile across development, staging, and production environments simply by switching the active environment.
- As a **security-conscious developer**, I want sensitive tokens marked as hidden variables to be automatically masked in the stream log, so that confidential credentials are never exposed on my screen or during screen sharing.
- As an **API tester**, I want handshake parameters (URL, headers, query params, subprotocols) to resolve once when I click Connect, so that the stream displays the exact handshake sent and does not retroactively change if an environment variable is modified later during the session.
- As a **developer executing interactive workflows**, I want outgoing message payloads to resolve template variables at the exact moment they are sent, so that variables captured from server responses earlier in the session are immediately available in my next message.
- As a **security engineer**, I want received server payloads containing `{{ ... }}` syntax to be displayed as literal text without template evaluation, so that malicious or accidental server strings cannot trigger template injection or corrupt displayed data.
- As an **API developer composing messages**, I want to hover over a `{{ VARIABLE }}` placeholder in any WebSocket field (URL, headers, subprotocols, composer) to see its current resolved value or `********` if hidden, so that I can verify my variable bindings before sending.
- As a **tester switching environments**, I want to select a different environment from the workspace environment selector and reconnect, having the session automatically pick up the new environment's variables without editing profile fields.
- As an **engineer copying payloads or exporting transcripts**, I want all clipboard copies and exported files to undergo deep heuristic secret sanitization, so that credentials never leak into defect reports, tickets, or external files.
- As a **system administrator or SRE**, I want PyPost to increment the `hidden_value_masks_applied_total{surface="websocket"}` metric whenever secrets are masked, and ensure raw payloads and secret header values never appear in application logs or metric labels.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Connect-Time Handshake Resolution:**
   - When initiating a connection, the target URL, query parameters, handshake headers, and requested subprotocols are resolved using active environment variables via `TemplateService`.
   - Modifying environment variables while a session is active does *not* alter the resolved handshake configuration or stream handshake event recorded for that session.
   - Reconnecting after modifying environment variables or switching active environments resolves the connection target using the updated environment variables.

2. **Per-Send Outgoing Payload Resolution:**
   - Outgoing message payloads authored in the composer, loaded from presets, or executed in sequences resolve `{{ VARIABLE }}` placeholders dynamically at the exact moment of transmission.
   - Variables captured mid-session (e.g. via "Set as variable...") are immediately resolved and transmitted in subsequent outgoing messages without requiring a reconnect.

3. **Template Injection Defense for Inbound Payloads:**
   - Inbound messages received from the WebSocket server are *never* processed by the template engine.
   - Payloads containing `{{ VAR }}`, Jinja syntax, or placeholder tokens are displayed and retained strictly as literal text.

4. **Interactive Variable-Aware Hover Tooltips:**
   - Hovering over a `{{ VARIABLE }}` placeholder in any WebSocket configuration field (URL input, query parameter table, header table, subprotocol list) or message authoring area displays a tooltip with the variable's resolved value.
   - If the variable is marked as hidden/secret, the tooltip displays `********` (or masked placeholder) instead of the plaintext value.
   - If the variable is undefined, the tooltip indicates that the variable is missing/unresolved.

5. **Two-Tier Secret Masking:**
   - **Tier 1 (Live Stream Ingestion):**
     - Outgoing frames and handshake lifecycle events replace exact hidden-variable values with standard masking placeholders (`HIDDEN_PLACEHOLDER`) prior to insertion into the `MessageStream` ring.
     - Incoming server frames replace exact hidden-variable values with standard masking placeholders without applying heuristic alterations.
   - **Tier 2 (Egress Surfaces):**
     - Copying stream entries or payload text to the clipboard applies heuristic sensitive text sanitization (`sanitize_text`).
     - Exporting session transcripts (JSON or plain-text files) applies full heuristic sensitive text sanitization across all output lines and payloads.
     - Agent and MCP inspection tools receive fully sanitized transcripts.

6. **Zero Secret Leakage Invariant:**
   - A hidden environment variable referenced in a header, URL parameter, or message payload never appears in plaintext in:
     - The live stream view.
     - System clipboard.
     - Exported transcript files.
     - Application log records.
     - Prometheus/OpenTelemetry metric labels.

7. **Observability and Metrics Accounting:**
   - Each time a hidden secret value is masked on the WebSocket stream ingestion or egress path, the metric counter `hidden_value_masks_applied_total{surface="websocket"}` is incremented.
   - Log statements generated by WebSocket components strictly omit message payloads, resolved URLs with query strings, and handshake header values, logging only `url_masked` and structured low-cardinality metadata.

8. **Architectural Seam Preservation:**
   - Ring ownership and ingestion boundaries remain strictly preserved: `WebSocketPresenter` manages secret masking and template resolution, while `StreamListModel.append_batch` is the sole writer to `MessageStream`.
   - `MessageStream` never holds unmasked secret values.

9. **Automated Test Coverage:**
   - Comprehensive unit, integration, and GUI tests verify:
     - Connect-time handshake resolution and mid-session variable modification isolation.
     - Per-send payload resolution with mid-session variable updates.
     - Literal preservation of `{{ ... }}` in inbound server payloads.
     - Variable hover tooltips for visible and hidden variables.
     - Egress masking on clipboard copy, JSON export, and plain-text export.
     - Metric increments for `hidden_value_masks_applied_total{surface="websocket"}`.
     - Absence of secret leaks in logs and metric labels.

## Task Description

### Problem Statement

In real-world API development, WebSocket endpoints frequently require environment-specific configurations (such as distinct gateway URLs for local, staging, and production clusters) and authentication credentials (such as bearer tokens, API keys, or session tokens passed via handshake headers, query parameters, or initial connection payloads).

PyPost has established robust environment templating and secret masking mechanisms for HTTP requests. However, prior to WS-7, WebSocket tabs either used hardcoded strings or lacked complete two-tier secret masking and live environment variable hover support:
1. **Lack of Dynamic Templating:** Without connect-time and per-send templating, users must manually edit URLs and headers whenever they switch environments.
2. **Timing Ambiguities:** Unlike HTTP requests which are short-lived, WebSocket sessions are persistent. Handshake parameters must resolve once at connection time so the stream reflects what was sent on the wire, whereas message payloads must resolve at send time so captured variables can be used interactively.
3. **Template Injection Risk:** If inbound server data were inadvertently passed through the template renderer, server payloads containing `{{ ... }}` could lead to unexpected behavior or security vulnerabilities.
4. **Secret Exposure Risks:** If secrets are not sanitized at both ingestion (Tier 1) and egress (Tier 2), sensitive tokens could be copied to the clipboard, written to export files, printed to debug logs, or exposed in metric labels.

WS-7 resolves these challenges by integrating PyPost's environment and secret masking framework directly into WebSocket sessions.

### Scope

**In Scope:**
- **Connect-Time Template Resolution:** Resolving URL, query parameters, handshake headers, and requested subprotocols via `TemplateService` at connection initiation.
- **Per-Send Payload Resolution:** Resolving outgoing message payloads (composer, presets, sequence steps) at transmission time.
- **Inbound Literal Safety:** Ensuring received server frames are never evaluated as templates.
- **Variable Hover Integration:** Enabling `VariableHoverMixin` / variable inspection tooltips across WebSocket UI inputs (URL, headers, query params, subprotocols, composer, presets, sequences).
- **Environment Propagation:** Propagating active environment variables and hidden keys from `EnvPresenter` to `WebSocketPresenter` and UI components.
- **Tier 1 Ingestion Masking:** Exact hidden-value replacement in `build_stream_entry` for live stream display.
- **Tier 2 Egress Masking:** Heuristic sensitive text sanitization on clipboard copy, JSON file export, plain-text file export, and MCP transcripts.
- **Telemetry Accounting:** Incrementing `hidden_value_masks_applied_total{surface="websocket"}` on masking events.
- **Log Hygiene:** Enforcing strict log redaction (sanitizing URLs to `url_masked`, excluding payloads and secret header values).
- **Automated Verification:** Comprehensive test suites validating templating, masking, hover tooltips, exports, and metric emissions.

**Out of Scope:**
- TLS certificate error overrides and `wss://` security policies (covered in WS-8).
- Model Context Protocol (MCP) probe runner tools (covered in WS-9).
- Process-wide session concurrency ceilings and settings persistence (covered in WS-10).

### Constraints and Assumptions

- **Non-Destructive Ingestion:** Exact secret replacement is applied to live streams; heuristic regex masking is reserved for egress (Tier 2) so that technical payloads under inspection are not corrupted during live debugging.
- **No Inbound Templating:** Received payloads are treated as immutable raw data; no template engine invocation is permitted on incoming frames.
- **Single Source of Truth for Variables:** `EnvPresenter` remains the single source of active variables and hidden keys, propagating snapshots to `WebSocketPresenter`.
- **Architectural Boundary:** `WebSocketSessionController` remains Qt/stream-free and unaware of environments; `WebSocketPresenter` handles template resolution and masking.

### Main Business Entities and Attributes

- **Environment Snapshot (`env_vars`, `hidden_keys`):**
  - `env_vars`: Mapping of variable names to current values (e.g. `{"BASE_URL": "wss://api.example.com", "TOKEN": "secret123"}`).
  - `hidden_keys`: Set of variable names flagged as sensitive/hidden whose values must be masked.
- **Handshake Configuration (Connect-Time Resolved):**
  - `url`: Fully resolved target WebSocket URL.
  - `headers`: Fully resolved key-value pairs for initial HTTP handshake headers.
  - `subprotocols`: Fully resolved tuple of requested subprotocol identifiers.
- **Outgoing Message (Per-Send Resolved):**
  - `raw_template`: Original payload text containing potential `{{ VAR }}` placeholders.
  - `resolved_payload`: Evaluated string with placeholders replaced by active environment values.
  - `masked_stream_entry`: Stream entry with sensitive hidden values replaced by `HIDDEN_PLACEHOLDER`.
- **Egress Artifact (Sanitized):**
  - `clipboard_text`: Payload string sanitized via heuristic sanitizer before copying.
  - `export_transcript`: JSON or plain-text transcript sanitized via heuristic sanitizer before writing to disk.

### User Scenarios / Workflows

#### Scenario 1: Multi-Environment Handshake Parameterization
1. The user defines a connection profile with URL `{{ WS_HOST }}/v1/stream` and header `Authorization: Bearer {{ API_KEY }}`.
2. The user selects the `Staging` environment (`WS_HOST=wss://staging.api.com`, `API_KEY=stg_secret_999` with `API_KEY` hidden).
3. The user hovers over `{{ WS_HOST }}` to see `wss://staging.api.com` in a tooltip, and hovers over `{{ API_KEY }}` to see `********`.
4. The user clicks **Connect**:
   - The handshake connects to `wss://staging.api.com/v1/stream` with `Authorization: Bearer stg_secret_999`.
   - The stream log displays `Connected to wss://staging.api.com/v1/stream` and the handshake entry shows `Authorization: Bearer ***`.
5. While connected, the user switches the active environment to `Production`.
   - The live session continues uninterrupted without altering its existing connection target.
6. The user clicks **Disconnect** and **Connect**:
   - The new session connects using the `Production` variables.

#### Scenario 2: Interactive Chained Workflow with Per-Send Payload Resolution
1. The user connects to an authenticated session.
2. The server sends an authentication challenge response: `{"session_id": "sess_abc123"}`.
3. The user selects `sess_abc123` in the stream detail pane and chooses **Set as variable...** -> `ACTIVE_SESSION`.
4. In the composer, the user writes: `{"action": "subscribe", "session": "{{ ACTIVE_SESSION }}"}`.
5. The user clicks **Send Message**:
   - The message resolves to `{"action": "subscribe", "session": "sess_abc123"}` at send time and transmits to the server.
   - If `ACTIVE_SESSION` was marked hidden, the stream displays `{"action": "subscribe", "session": "***"}`.

#### Scenario 3: Secure Transcript Export & Clipboard Copy
1. A session stream contains sent messages and received frames with sensitive credentials.
2. The user selects a message and clicks **Copy**:
   - The copied text on the clipboard has all hidden secrets and sensitive patterns sanitized (`sanitize_text`).
3. The user clicks **Export** -> **JSON Transcript**:
   - The generated export file replaces all hidden variables with placeholders and sanitizes any sensitive text, ensuring safe sharing in issue trackers.

## Q&A

**Q: Why are handshake parameters resolved at connect time while message payloads resolve per send?**
**A:** The WebSocket handshake occurs once when the TCP/TLS connection is established. Re-resolving handshake parameters mid-session would misrepresent what was actually sent over the wire. Conversely, message payloads are transmitted individually throughout an open session; resolving them per send allows users to use dynamic variables captured earlier in the session.

**Q: Why are received server payloads never evaluated by the template engine?**
**A:** Inbound data originates from external and potentially untrusted servers. Passing incoming payloads through a template engine would create a template injection vector where server strings containing `{{ ... }}` could evaluate arbitrary expressions or corrupt client state.

**Q: What is the difference between Tier 1 and Tier 2 masking?**
**A:** Tier 1 (live stream ingestion) uses exact value replacement for known hidden environment variables. This prevents secrets from entering the UI while preserving the exact technical structure of server responses during live debugging. Tier 2 (egress) applies full heuristic sanitization (`sanitize_text`) to everything leaving the process (clipboard, files, MCP transcripts) to guard against any residual sensitive patterns.

**Q: Where does secret masking occur in the architecture?**
**A:** Masking occurs in `WebSocketPresenter` before entries are added to `MessageStream`. `StreamListModel` remains the sole writer to `MessageStream`. No unmasked secret is ever stored in the ring buffer.
