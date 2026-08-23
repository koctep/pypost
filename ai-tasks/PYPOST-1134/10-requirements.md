# PYPOST-1134: WS-6 Composer, saved presets and sequence runner

## Programming Language

Python is the implementation language for the application runtime, data models, user interface presenters/views, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost supports interactive WebSocket communication through Epic PYPOST-1123. Previous foundational stories established the transport engine (WS-1), persistent data models (WS-2), bounded stream buffers (WS-3), the interactive session tab (WS-4), and the stream inspector (WS-5).

In real-world API development and testing, WebSocket interactions are rarely limited to typing one-off plain-text messages:
1. **Diverse Data Formats:** Modern real-time endpoints communicate using diverse data formats beyond plain text, including structured JSON, raw hexadecimal bytes (e.g. binary protocols, IoT feeds, custom framing), and Base64-encoded binary payloads.
2. **Repetitive Payloads & Tedious Retyping:** Developers frequently send standard commands (authentication handshakes, channel subscriptions, heartbeat pings, query probes) multiple times during testing. Retyping complex JSON or hex payloads is error-prone, tedious, and time-consuming.
3. **Multi-Step Protocol Workflows:** Reproducing specific bugs or exercising complex real-time exchanges requires sending a precise multi-step sequence of messages with defined timing delays between steps (for example: *Connect -> 0 ms: Send Auth -> 250 ms: Subscribe to Channel -> 1,000 ms: Request Snapshot*). Manually coordinating these multi-step exchanges is impossible to reproduce identically across different test runs or environments.

The goal of this task (WS-6) is to deliver a **versatile multi-format message composer, a reusable message preset library, and an automated sequence runner**:
- **Multi-Format Composition & Syntax Validation:** Enable users to author and transmit payloads in Text, JSON, Hexadecimal, and Base64 formats with real-time format validation to prevent sending malformed data over the wire.
- **Persistent Message Presets:** Allow users to save frequently used messages directly onto the connection profile, ensuring presets persist through workspace export/import and can be re-sent in a single click or loaded into the composer for rapid modification.
- **Automated Sequence Execution:** Empower users to define and run multi-step message sequences combining saved presets or inline payloads with configurable pre-step delays, ensuring reproducible, deterministic protocol exchanges.
- **Graceful Failure & Control Flow:** Ensure running sequences can be stopped at any moment without dropping the active session, report clear diagnostics when a step fails, and block execution when a sequence references a missing preset.
- **Dedicated Messages Management Workspace:** Provide a clean, master/detail `Messages` sub-tab for managing presets and sequences alongside intuitive quick-access shortcuts directly within the composer strip.

## User Stories

- As an **API developer testing binary or structured protocols**, I want to compose and transmit messages in JSON, Hexadecimal, and Base64 formats in addition to plain text, so that I can interact with endpoints regardless of their wire format.
- As a **developer authoring JSON or Hex payloads**, I want the composer to validate my input format before transmission and report formatting errors, so that I don't accidentally send invalid syntax over an active connection.
- As a **tester running repetitive commands**, I want to save frequently used messages as named presets directly on my WebSocket profile, so that I can reuse them without retyping.
- As an **API engineer**, I want to save a message preset with one click directly from the composer (`Save...`), so that I can quickly capture payloads I have just authored and verified.
- As a **developer testing multi-step workflows**, I want to assemble an ordered sequence of message steps with custom timing delays (e.g. 0 ms, 250 ms, 1,000 ms), so that I can reproduce complex protocol exchanges identically.
- As an **API tester**, I want to run a multi-step sequence against different workspace environments (e.g. staging vs production) without modifying the sequence definition, so that I can verify identical behavior across environments.
- As an **engineer executing a sequence**, I want each executed step to appear clearly in the stream view, so that I can verify outbound message delivery and observe subsequent server responses.
- As a **developer debugging a sequence failure**, I want execution to stop immediately if a step fails and display the exact failing step index and reason, so that I can quickly diagnose what went wrong.
- As an **operator running a long sequence**, I want an explicit **Stop** button that halts execution before the next step while leaving the connection open, so that I can inspect the intermediate state without disconnecting.
- As an **API developer organizing test fixtures**, I want to use both saved preset references and custom inline payloads within sequence steps, so that I have complete flexibility when designing test scripts.
- As a **tester editing presets and sequences**, I want a dedicated `Messages` management tab with clear master/detail views and empty states, so that I can easily create, duplicate, edit, reorder, and delete test assets.
- As an **API tester**, I want the application to prevent sending or running sequences when the connection is not Open and provide clear feedback, so that outbound messages are not silently queued or lost.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Multi-Format Composition & Per-Format Validation:**
   - The message composer supports authoring in four distinct formats: `Text`, `JSON`, `Hexadecimal`, and `Base64`.
   - The composer performs format-specific validation prior to transmission.
   - Attempting to send invalid JSON syntax, non-hexadecimal characters / odd-length hex strings, or invalid Base64 data is refused with an immediate inline validation error.
2. **Preset Persistence and CRUD Management:**
   - Message presets are saved directly on the WebSocket connection profile and persist across workspace export/import and application restarts.
   - The user can create, duplicate, edit (name, format, payload), and delete presets via the `Messages` sub-tab.
   - The composer strip provides a `Save...` action that captures the current composer format and payload as a new preset on the profile.
3. **One-Action Preset Dispatch & Loading:**
   - A preset can be dispatched immediately across an open connection via `Send now` in one action without modifying the active composer text.
   - A preset can be loaded into the active composer via `Load into composer` for further editing in any session state.
4. **Ordered Sequence Execution with Pacing Delays:**
   - The user can define multi-step sequences containing an ordered list of steps.
   - Each step supports either referencing a saved preset (`preset_id`) or defining an inline payload with its own format.
   - Each step specifies a configurable pre-step delay (`delay_ms`) waited before that step is sent.
   - Running a sequence executes steps in strict chronological order with the specified pacing delays, and each transmitted step lands in the stream view as an outbound message.
5. **Sequence Failure Handling & Safe Mid-Run Cancellation:**
   - If a step fails during execution (e.g. malformed payload or connection drop), the sequence immediately stops, and an event is logged stating which step failed and the specific failure reason.
   - A running sequence can be stopped at any time via `Stop`; halting stops before the next scheduled step and leaves the WebSocket session open and undisturbed.
6. **Missing Preset Safety Guard:**
   - If a sequence contains a step referencing a deleted or non-existent preset, the step is visibly flagged (e.g. `<missing preset>`), and attempting to `Run` the sequence is blocked with a clear, named reason.
7. **Connection State Guard:**
   - Attempting to send a composer message, trigger `Send now`, or `Run` a sequence while the session is not in the `Open` state is refused with a clear user notification rather than silently queued.
8. **Messages Sub-Tab & Composer Strip UI Integration:**
   - The `Messages` sub-tab provides master/detail editing for both saved messages and sequences, step reordering (`Up`/`Down`), and clear empty states for both sections when no items exist.
   - The composer strip includes `Format:`, `Preset:`, and `Sequence:` quick-selection controls alongside `Save...`, `Run`, and `Stop` buttons.
9. **UI Identity Spot-Check Integration:**
   - Stable automation identifiers (`WS_*`) are declared for all composer controls, preset widgets, sequence tables, and action buttons.
   - `tests/test_ui_identity_spotcheck.py` is extended to verify that all new widget identifiers resolve correctly on live tabs.
10. **Comprehensive Automated Test Coverage:**
    - Automated unit, GUI, and end-to-end tests verify multi-format encoding/validation, preset CRUD and export/import round-trips, sequence step execution order and delays, cancellation, error stops, missing preset guards, and state refusal checks.

## Task Description

### Problem Statement

In WS-4 and WS-5, PyPost established the fundamental WebSocket workspace tab and the stream inspector. However, message transmission remains limited to typing raw plain-text payloads one at a time:
- Users cannot author binary payloads (Hexadecimal or Base64) or structured JSON with syntax validation.
- Users have no way to store commonly used messages, forcing them to repeatedly re-enter authentication tokens, subscription queries, or testing commands.
- Users cannot automate multi-step protocol flows, making regression testing of complex state machines (e.g. handshake -> authenticate -> subscribe -> query) manual, tedious, and prone to human timing variations.
- Attempting to reproduce a sequence across different environments requires manual copy-pasting rather than executing a reusable sequence plan.

WS-6 resolves these limitations by delivering a rich, format-aware composer, profile-level message presets, and a QTimer-paced sequence runner.

### Scope

**In Scope:**
- **Multi-Format CodeEditor Composer:** Integration with `BodyFormat` selectors supporting Text, JSON, Hexadecimal, and Base64 payloads with pre-send validation and error indicators.
- **Composer Quick-Strip Controls:** `Format:`, `Preset:` dropdown with `Save...`, and `Sequence:` dropdown with `Run` and `Stop` buttons situated directly above/below the payload editor.
- **Messages Sub-Tab Workspace:** Dedicated sub-tab inside `pypost_ws_detail_tabs` featuring split master/detail lists for Saved Messages (Presets) and Sequences.
- **Preset CRUD & Actions:** Creating, editing, duplicating, deleting, loading into composer, and sending presets immediately (`Send now`).
- **Sequence Step Management:** Creating, duplicating, deleting sequences; adding, removing, and reordering steps (`Up`/`Down`); configuring preset references vs inline payloads; setting per-step pre-delays.
- **Sequence Runner Engine:** Pure plan step expansion (`websocket_sequence.py`) and asynchronous timer-paced execution (`websocket_sequence_runner.py`).
- **Control & Safety Invariants:** Blocking runs on missing presets, halting sequences mid-run without closing the session, refusing dispatches when not connected, and logging step failure diagnostics.
- **Automation Identities & Tests:** Declaring `pypost_ws_*` widget IDs, updating `tests/test_ui_identity_spotcheck.py`, and implementing comprehensive unit and GUI test suites.

**Out of Scope:**
- Connect-time handshake secret resolution and deep egress heuristic masking (covered in WS-7).
- TLS certificate overrides and warning dialogs (covered in WS-8).
- Model Context Protocol (MCP) bounded probe tool execution (covered in WS-9).
- Global concurrency ceilings and Prometheus telemetry counters (covered in WS-10).

### Constraints and Assumptions

- **Layering Compliance:** Pure sequence expansion and step validation must reside in Qt-free core modules (`pypost/core/websocket_sequence.py`), while UI-thread pacing and timers reside in Qt glue (`pypost/core/qt/websocket_sequence_runner.py`).
- **Non-Blocking Execution:** Step delays must be managed asynchronously using Qt timers, never blocking the main UI event loop or freezing UI responsiveness.
- **Session Decoupling:** Sequence execution must operate over an existing `Open` session without managing or interrupting the session lifecycle. Halting a sequence must leave the underlying socket connected.
- **Persistence Integrity:** Presets and sequences are stored within the `WebSocketConnection` domain model and must seamlessly round-trip through collection storage and export/import without data loss.
- **Offline Testability:** All sequence runner and composer tests must execute deterministically in offline test environments using local mock servers without external network access.

## Functional Requirements

- **FR-1: Multi-Format Message Composer**:
  - The composer must provide a format selector supporting four formats: `Text`, `JSON`, `Hexadecimal`, and `Base64`.
  - Switching formats updates syntax highlighting and validation rules appropriately.
  - The editor must support multi-line text input with standard editing shortcuts.
  - An explicit **Send Message** button (and shortcut `Ctrl+Enter` / `F5`) triggers validation and transmission.

- **FR-2: Pre-Send Payload Validation**:
  - `JSON`: Validates that the payload is well-formed JSON (objects, arrays, strings, numbers, booleans, null).
  - `Hexadecimal`: Validates that the payload consists of valid hexadecimal digit pairs (ignoring optional whitespace separators) with an even character count.
  - `Base64`: Validates that the payload conforms to valid standard Base64 encoding.
  - `Text`: Accepts any valid UTF-8 string.
  - If validation fails, transmission is blocked, and an inline error message highlights the syntax defect.

- **FR-3: Message Preset Management (CRUD)**:
  - Presets are saved on the parent `WebSocketConnection` profile and persist across collection saves, exports, and imports.
  - Each preset contains: unique ID, descriptive name, payload format, and payload template string.
  - The `Messages` sub-tab provides a master list of presets and a detail editing pane (Name, Format, Payload).
  - The user can perform full CRUD: `New`, `Duplicate`, `Delete`, and `Save`.

- **FR-4: Composer Strip Quick-Preset Integration**:
  - The composer strip contains a `Preset:` dropdown listing all saved presets for the active profile.
  - Selecting a preset loads its format and payload into the composer editor.
  - A `Save...` button next to the preset dropdown prompts the user for a preset name (or updates the current preset) and immediately saves the composer's current format and payload to the profile.

- **FR-5: Single-Action Preset Dispatching**:
  - In the `Messages` sub-tab preset detail pane:
    - **`Load into composer`**: Copies the preset format and payload into the main composer for editing. Works across all session states.
    - **`Send now`**: Validates and immediately transmits the preset payload over the active socket without overwriting the current composer content. Only enabled when the session is `Open`.

- **FR-6: Sequence Creation and Step Configuration**:
  - Sequences are saved on the `WebSocketConnection` profile and persist through storage and export/import.
  - Each sequence contains: unique ID, descriptive name, and an ordered list of steps.
  - Each sequence step contains:
    - **Step Type**: Preset Reference (`preset_id`) or Inline Payload.
    - **Format**: `Text`, `JSON`, `Hex`, or `Base64` (for inline payloads).
    - **Payload**: Payload template string (for inline payloads).
    - **Pre-Step Delay**: Delay in milliseconds (`delay_ms`, 0 to 600,000 ms) waited before transmitting the step.
  - The step table supports adding new steps, removing steps, and reordering steps via **Move Up** and **Move Down** actions.

- **FR-7: Sequence Runner Execution & Pacing**:
  - The user can trigger sequence execution via **Run** (in the `Messages` sub-tab or via `pypost_ws_sequence_combo` in the composer strip).
  - Sequence execution is allowed only when the session is in the `Open` state.
  - Steps are executed strictly sequentially:
    1. Wait the step's specified `delay_ms` using an asynchronous timer.
    2. Resolve the step payload (preset payload or inline payload).
    3. Validate and transmit the payload over the active WebSocket connection.
    4. The sent message immediately appears as an outbound entry in the stream view.
    5. Proceed to the next step until all steps complete.

- **FR-8: Sequence Control, Stopping & Error Handling**:
  - While a sequence is executing, a **Stop** button is enabled in both the composer strip and the sequence detail pane.
  - Clicking **Stop** halts sequence execution immediately before the next step begins. The active WebSocket session remains open and undisturbed.
  - If any step fails (e.g. invalid format syntax or underlying socket error), the runner halts execution immediately.
  - When a sequence finishes, stops, or fails, an informational lifecycle event or status notification records the outcome (e.g. *"Sequence 'login+sub' completed (3/3 steps)"*, *"Sequence stopped at step 2"*, or *"Sequence failed at step 2: invalid hex payload"*).

- **FR-9: Missing Preset Reference Protection**:
  - If a sequence step references a preset ID that has been deleted or cannot be resolved, the step is displayed as `<missing preset>` in the step table.
  - Attempting to `Run` a sequence containing a missing preset reference is blocked, and the user receives a named error message identifying the missing dependency.

- **FR-10: Empty State Guidance**:
  - When a profile has no saved message presets, the preset pane displays an informative empty state: *"No saved messages yet. Compose one and choose Save... in the composer, or [New]."*
  - When a profile has no saved sequences, the sequence pane displays an informative empty state: *"No sequences yet. [New sequence] builds one from saved messages or inline payloads."*

- **FR-11: UI Automation Identities & Spot-Check Extension**:
  - Stable automation identifiers are assigned to all composer, preset, and sequence controls (`pypost_ws_messages_tab`, `pypost_ws_presets_list`, `pypost_ws_preset_name_input`, `pypost_ws_preset_format_combo`, `pypost_ws_preset_payload_edit`, `pypost_ws_preset_new_button`, `pypost_ws_preset_duplicate_button`, `pypost_ws_preset_delete_button`, `pypost_ws_preset_load_button`, `pypost_ws_preset_send_button`, `pypost_ws_preset_save_button`, `pypost_ws_sequences_list`, `pypost_ws_sequence_new_button`, `pypost_ws_sequence_duplicate_button`, `pypost_ws_sequence_delete_button`, `pypost_ws_sequence_steps_table`, `pypost_ws_sequence_step_add_button`, `pypost_ws_sequence_step_remove_button`, `pypost_ws_sequence_step_up_button`, `pypost_ws_sequence_step_down_button`, `pypost_ws_composer_format_combo`, `pypost_ws_preset_combo`, `pypost_ws_sequence_combo`, `pypost_ws_sequence_run_button`, `pypost_ws_sequence_stop_button`, `pypost_ws_composer_edit`, `pypost_ws_send_message_button`).
  - `tests/test_ui_identity_spotcheck.py` is extended to assert all composer, preset, and sequence identifiers.

## Non-Functional Requirements

- **NFR-1: UI Responsiveness & Non-Blocking Pacing**:
  - Pacing delays between sequence steps must use asynchronous timers (`QTimer`), ensuring the UI remains completely responsive and interactive during long delays (e.g. 5,000 ms delays).
- **NFR-2: Deterministic Reproducibility**:
  - Executing the same sequence multiple times against an endpoint must produce identical message ordering and step pacing.
  - Sequences must execute identically regardless of active workspace environment switching.
- **NFR-3: Graceful Error Isolation**:
  - Sequence failures or validation errors must never crash the application or unexpectedly sever active WebSocket connections.
- **NFR-4: Data Persistence & Backward Compatibility**:
  - Presets and sequences must serialize cleanly to JSON within collection files and survive round-trip export and import without field degradation.
- **NFR-5: Modularity & Code Quality**:
  - Sequence planning, step expansion, and format codec validation must be implemented in pure, Qt-free core modules to allow headless testing.
  - Per-file line-of-code caps and project architectural constraints must be strictly adhered to.
- **NFR-6: Usability & Ergonomics**:
  - Master/detail forms must update seamlessly without requiring manual page refreshes.
  - Empty states must provide actionable guidance directing users to primary creation pathways.
- **NFR-7: Automated Testability**:
  - All test suites must execute deterministically in offline environments with explicit test timeouts.

## Main Entities and Attributes

- **Message Preset (`WebSocketMessagePreset`)**:
  - `id`: Unique string identifier (UUID).
  - `name`: User-facing name of the preset (e.g. "Subscribe Orders", "Auth Handshake").
  - `format`: Payload format (`text`, `json`, `hex`, `base64`).
  - `payload`: Template payload string.

- **Sequence Step (`WebSocketSequenceStep`)**:
  - `preset_id`: Optional string reference to a `WebSocketMessagePreset`.
  - `inline_payload`: String payload used when not referencing a preset.
  - `format`: Payload format used for inline payloads.
  - `delay_ms`: Pacing delay in milliseconds waited before executing this step (default: 0 ms).

- **Sequence (`WebSocketSequence`)**:
  - `id`: Unique string identifier (UUID).
  - `name`: User-facing name of the sequence (e.g. "Login and Subscribe", "Reproduce Issue 412").
  - `steps`: Ordered list of `WebSocketSequenceStep` objects.

- **WebSocket Connection Profile (`WebSocketConnection`)**:
  - `presets`: List of `WebSocketMessagePreset` objects associated with the connection.
  - `sequences`: List of `WebSocketSequence` objects associated with the connection.
  - `default_format`: Default `WsMessageFormat` selected when creating new messages.

- **Sequence Runner State**:
  - `active_sequence_id`: Identifier of the currently executing sequence (or `None`).
  - `current_step_index`: 0-based index of the step currently being delayed or transmitted.
  - `total_steps`: Total number of steps in the active sequence.
  - `is_running`: Boolean flag indicating whether sequence execution is in progress.
  - `is_stopped`: Boolean flag indicating if execution was halted by the user.

- **Composer State**:
  - `current_format`: Currently selected `WsMessageFormat` in the composer dropdown.
  - `payload_text`: Content string currently in the code editor.
  - `selected_preset_id`: Currently selected preset in the composer strip dropdown (or `None`).
  - `selected_sequence_id`: Currently selected sequence in the composer strip dropdown (or `None`).
  - `is_valid`: Boolean indicating if the current payload satisfies format syntax rules.
  - `validation_error`: Error message describing syntax defect when invalid.

## User Scenarios

### Scenario 1: Composing and Validating Multi-Format Payloads
1. The user connects to an active WebSocket session (`Open` state).
2. In the composer strip, the user selects **JSON** from the `Format:` dropdown.
3. The user types an invalid JSON string: `{"action": "subscribe", "channel": }`.
4. The user clicks **Send Message** (or presses `Ctrl+Enter`).
5. PyPost blocks transmission and displays an inline validation error: *"Invalid JSON syntax"*.
6. The user corrects the payload to `{"action": "subscribe", "channel": "orders"}` and presses `Ctrl+Enter`.
7. The message is validated, transmitted, and appears in the stream with an outbound indicator (`->`).

### Scenario 2: Composing and Sending Binary Hexadecimal Frames
1. The user selects **Hex** from the `Format:` dropdown.
2. The user types `48 65 6c 6c 6f` (ASCII "Hello" in hex).
3. The user clicks **Send Message**.
4. PyPost decodes the hex string into raw binary bytes and transmits the binary frame over the WebSocket.
5. The sent entry appears in the stream marked with format `hex`, wire size `5 B`, and content `48 65 6c 6c 6f`.

### Scenario 3: Saving a Message Preset from the Composer
1. In the composer, the user authors an authentication message in JSON format: `{"type": "auth", "token": "{{API_KEY}}"}`.
2. The user clicks the **Save...** button next to the `Preset:` dropdown.
3. PyPost prompts for a preset name; the user enters *"Authenticate"*.
4. PyPost creates a new `WebSocketMessagePreset` on the connection profile and selects *"Authenticate"* in the preset dropdown.
5. The user switches to the `Messages` sub-tab; *"Authenticate"* is listed in the Saved Messages master list with format `json` and the saved payload.

### Scenario 4: Managing Presets in the Messages Sub-Tab
1. The user opens the `Messages` sub-tab of the active WebSocket profile.
2. In the Saved Messages section, the user clicks **[New]**.
3. A new preset entry is added to the list. In the detail pane, the user sets:
   - Name: *"Ping Heartbeat"*
   - Format: `Text`
   - Payload: `ping`
4. The user clicks **[Save]**.
5. With the connection in the `Open` state, the user clicks **[Send now]**.
6. The ping message is immediately sent over the wire and logged to the stream without altering whatever text was previously in the composer.
7. The user clicks **[Load into composer]**; the composer is populated with `ping` and format `Text`.

### Scenario 5: Defining and Executing a Multi-Step Sequence
1. In the `Messages` sub-tab, the user clicks **[New sequence]** under the Sequences section.
2. The user sets the sequence name to *"Login and Subscribe"*.
3. The user clicks **[Add step]** and configures Step 1:
   - Message: References preset *"Authenticate"*
   - Delay before: `0 ms`
4. The user clicks **[Add step]** and configures Step 2:
   - Message: References preset *"Subscribe Orders"*
   - Delay before: `250 ms`
5. The user clicks **[Add step]** and configures Step 3:
   - Message: Inline payload `{"op": "query", "limit": 50}` (Format: `JSON`)
   - Delay before: `1,000 ms`
6. With the connection open, the user clicks **[Run]** (or uses the composer strip `Sequence: [Login and Subscribe] [Run]`).
7. Step 1 sends immediately (`0 ms`).
8. After 250 ms, Step 2 sends automatically.
9. After another 1,000 ms, Step 3 sends automatically.
10. All three outgoing messages appear chronologically in the stream, and a notification reports that the sequence completed successfully.

### Scenario 6: Stopping a Running Sequence Mid-Run
1. The user starts a sequence containing 5 steps with 2,000 ms delays between steps.
2. Step 1 executes and lands in the stream.
3. During the 2,000 ms delay before Step 2, the user notices an unexpected server response and clicks **[Stop]**.
4. The sequence runner cancels pending timers and halts immediately.
5. A lifecycle notice logs: *"Sequence stopped by user before step 2"*.
6. The WebSocket connection remains `Open` and fully active, allowing the user to inspect the stream and send ad-hoc commands.

### Scenario 7: Handling Missing Presets and Step Failures
1. A user previously configured a sequence referencing a preset named *"Legacy Token"*. Later, the user deletes *"Legacy Token"* from the presets list.
2. The user views the sequence; Step 1 displays `<missing preset>` in the message column.
3. The user clicks **[Run]**.
4. Execution is blocked immediately, and an error dialog or notification explains: *"Cannot run sequence: Step 1 references missing preset 'Legacy Token'"*.
5. No network frames are sent.

### Scenario 8: Guarding Against Dispatches While Disconnected
1. The session is in the `Idle` state (not connected).
2. The user clicks **Send Message** in the composer.
3. PyPost displays a clear message: *"Cannot send message: WebSocket session is not connected. Connect first."*
4. The user attempts to click **[Run]** on a sequence; the action is disabled or reports the same connection requirement.
5. Outbound messages are never silently queued or buffered while disconnected.

## Q&A

| Question | Answer |
| --- | --- |
| Why is per-format validation enforced before message transmission? | Sending malformed JSON or invalid hexadecimal sequences over a real-time socket often results in immediate server disconnects or unhelpful protocol errors. Validating syntax locally before transmission protects developers from avoidable errors and provides immediate, actionable feedback. |
| What binary formats are supported and how are they handled? | `Hexadecimal` and `Base64` formats are supported. In both cases, the composer accepts user-entered text (hex digit pairs or base64 strings), validates the encoding, and converts the text into raw binary bytes (`bytes`) before dispatching as a WebSocket binary frame (`send_binary`). In the stream, they are displayed with their respective format markers. |
| How do presets interact with workspace exports and imports? | Presets are stored directly within the `presets` field of the `WebSocketConnection` domain model. When a collection is exported to JSON or imported into another workspace, all presets and their associated formats and payloads travel seamlessly with the collection. |
| What is the difference between `Load into composer` and `Send now`? | `Load into composer` copies the preset's payload and format into the main composer editor so the user can inspect or modify it before sending; it can be used in any session state. `Send now` transmits the preset immediately over the open socket without altering the current text in the composer, enabling quick one-click dispatching. |
| How are pre-step delays handled without blocking the UI? | Sequence pacing is handled asynchronously using Qt timers (`QTimer`) in `pypost/core/qt/websocket_sequence_runner.py`. When a sequence step specifies a `delay_ms`, a non-blocking timer schedules the execution of that step, leaving the main UI thread free to render incoming messages, handle user interactions, and process the Stop button. |
| What happens when a running sequence is stopped? | Clicking **Stop** halts the runner before the next scheduled step executes. The underlying WebSocket connection remains in the `Open` state without interruption, allowing the user to inspect intermediate responses or continue manual interactions. |
| What happens if a step in a sequence fails? | If a step fails (e.g. invalid payload syntax or connection drops mid-sequence), the runner terminates immediately and reports the specific step index and failure reason in the stream/status bar, preventing subsequent steps from executing in an invalid state. |
| Why are messages refused when the session is not Open rather than queued? | WebSockets are stateful, real-time protocols. Silently queuing messages while disconnected can lead to unintended bursts of traffic upon reconnection or sending stale data. Refusing dispatches with clear feedback ensures all transmissions are deliberate and predictable. |
| How do sequences work across different environments? | Step payloads and presets store template strings. When executed, variable placeholders (e.g. `{{API_KEY}}`, `{{BASE_URL}}`) resolve dynamically using the active environment variables at send time, allowing the exact same sequence to run unmodified against local, staging, or production environments. |
