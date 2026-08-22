# PYPOST-1132: WS-4 WebSocket session tab and minimal client

## Programming Language

Python is the implementation language for the application runtime, user interface presenters, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost is introducing interactive real-time protocol support through Epic PYPOST-1123. Previous foundational stories established the transport engine (WS-1), persistent data models and collection storage (WS-2), and bounded message streaming buffers and codecs (WS-3). However, these capabilities remain purely internal without a user interface.

The goal of this task (WS-4) is to deliver the **first user-visible WebSocket client** within PyPost:
- **Intuitive session management:** Enable users to open saved WebSocket connection profiles from the collection tree into dedicated workspace tabs, inspect configuration parameters, and control connection lifecycles (Connect/Disconnect) independently from message dispatch.
- **Accessible and unambiguous status feedback:** Clearly present real-time session states across tab strips and header badges using both descriptive text and symbolic markers (never relying on color alone), ensuring immediate situational awareness.
- **Connection parameter freezing during active sessions:** Enforce that endpoint configuration fields (URL, query parameters, handshake headers, subprotocols) are locked to read-only during active or in-flight connections with clear explanatory notices, eliminating ambiguous or ineffective mid-session configuration edits.
- **Chronological stream visualization:** Provide a unified, timestamped, chronological log displaying sent messages, incoming server replies, and connection lifecycle events with distinct directional indicators.
- **Minimal interactive message authoring:** Provide a plain-text composer allowing users to author and transmit messages across an open connection.
- **Deterministic lifecycle and state safety:** Guarantee that closing a session tab or quitting the application deterministically releases network sockets without resource leaks, and that restored session tabs open in an idle state without initiating unintended network traffic.
- **End-to-end secret protection:** Guarantee that sensitive environment variables used in handshake headers or sent payloads are masked in the stream buffer from initial ingestion.

## User Stories

- As an **API developer or tester**, I want to double-click a saved WebSocket connection profile in my collection tree to open it in a tab, so that I can easily access and interact with my real-time endpoints.
- As a **developer testing real-time APIs**, I want explicit, independent controls for Connect/Disconnect and Send Message, so that I can establish a persistent session before deciding when and what payloads to transmit.
- As a **user with visual impairments or color vision deficiency**, I want session status indicated by distinct textual labels and symbolic glyphs/icons rather than color alone, so that I can always accurately discern whether my session is Idle, Connecting, Open, Reconnecting, or Failed.
- As an **API tester**, I want connection parameters (URL, query parameters, headers, subprotocols) locked to read-only while connected with a clear notice explaining why, so that I don't mistakenly assume that editing a field changes an existing live connection.
- As an **API developer debugging message exchanges**, I want to see sent frames, received replies, and lifecycle notifications in a single, chronological, timestamped list with clear directional indicators, so that I can trace the exact order of events in my WebSocket conversation.
- As an **operator sending ad-hoc commands**, I want a simple text composer to write and transmit plain-text payloads over the open connection, so that I can test real-time server responses interactively.
- As a **system administrator or developer running multiple tabs**, I want closing a tab or exiting PyPost to immediately and cleanly terminate the underlying socket, so that background connections do not linger or leak system resources.
- As a **developer relaunching PyPost**, I want previously open WebSocket tabs to restore in an Idle state without auto-connecting, so that network traffic is never initiated unexpectedly upon application startup.
- As a **security-conscious developer**, I want sensitive environment variables used in headers or sent messages to be masked in the stream log, so that confidential tokens or keys are not exposed during live inspection.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Collection Tree Integration:**
   - Double-clicking a saved WebSocket connection profile in the collection tree opens the profile in a dedicated tab in the main tab strip.
   - Re-opening an already open profile activates and focuses the existing tab instead of creating duplicates.
2. **Explicit Connection Lifecycle Control:**
   - Connect and Disconnect controls are separate and distinct from the message Send action.
   - Initiating connection transitions the session to Connecting; user-initiated disconnection cleanly closes the session and returns it to Idle.
3. **Multi-Modal State Indicators (Accessibility):**
   - Session state (Idle, Connecting, Open, Closing, Reconnecting, Failed) is prominently displayed in the tab header badge and on the tab strip.
   - State representation always includes both symbolic markers/glyphs and explicit textual status names (e.g. `Idle`, `Connecting...`, `Open`, `Failed`), never relying on color alone.
4. **Connection Parameter Locking:**
   - Connection parameters (URL input, query parameters, handshake headers, subprotocols) become strictly read-only whenever the session is active or in-flight (in Connecting, Open, Closing, or Reconnecting states).
   - A visible notice or tooltip explains that the user must disconnect before modifying connection parameters.
   - When the session returns to Idle or Failed, connection fields become editable again.
5. **Unified Chronological Stream Display:**
   - Sent messages, received replies, and lifecycle events (such as connection opened, handshake accepted, peer closed, disconnection) appear in a single chronological list.
   - Each entry displays a timestamp, directional indicator (e.g. outbound, inbound, or informational lifecycle), payload size, and formatted content.
6. **Plain-Text Composer & Message Sending:**
   - A multi-line message composer allows entering and sending plain-text payloads.
   - Attempting to send a message when the session is not in the Open state is prevented with clear user feedback.
7. **Deterministic Teardown & Safe Restoration:**
   - Closing a session tab terminates the active connection cleanly and releases associated resources.
   - Exiting the application cleanly shuts down all active WebSocket connections.
   - Restoring open tabs upon application restart restores WebSocket tabs in the Idle state without initiating automatic network connections.
8. **Secret Masking at Ingestion:**
   - Hidden environment variables referenced in handshake headers or outgoing messages are masked with standard placeholders in the stream display from the moment of ingestion.
9. **Automation and Test Verification:**
   - Stable automation identities (`WS_*`) are assigned to all key tab components and controls.
   - Automated end-to-end and GUI tests verify profile opening, connecting, message transmission, stream row population, state badge transitions, parameter locking, and tab teardown.

## Task Description

### Problem Statement

Prior to WS-4, PyPost possessed low-level transport mechanisms and data models for WebSocket connections, but users had no way to interact with these features through the graphical user interface. Users require a dedicated workspace tab where they can configure endpoints, manage persistent connection lifecycles, send payloads, and observe bidirectional message streams.

Furthermore, real-time protocols differ fundamentally from stateless request/response HTTP interactions:
- Connections are long-lived and stateful; establishing a connection and sending messages are distinct operations.
- Modifying connection parameters (such as query parameters or headers) while connected has no effect on an established socket; allowing edits during active sessions leads to user confusion and false assumptions.
- Connection status must be unambiguous at all times, including for users relying on high-contrast themes or screen readers, requiring multi-modal visual indicators (text and symbols, not color alone).
- High message volumes require smooth, non-blocking stream ingestion and clean resource cleanup upon tab closure or application exit.

### Scope

**In Scope:**
- **WebSocket Tab Workspace:** Dedicated tab layout integrating endpoint configuration, connection status header, chronological stream view, and message composer.
- **Collection Tree Row Interaction:** Opening saved WebSocket profiles into workspace tabs via tree double-click or context menu actions.
- **Tab Header & Badge Indicators:** Visual presentation of session state using text labels and symbolic glyphs across tab strips and header badges.
- **Connection Parameter Editor:** Input controls for target URL, query parameters, handshake headers, and requested subprotocols, with dynamic read-only locking during active states.
- **Chronological Message Stream:** List display of incoming, outgoing, and lifecycle entries with timestamps, directional indicators, and payload sizes.
- **Stream Ingestion Integration:** Connecting raw transport frame feeds to masked stream entries using active environment variables and hidden keys.
- **Plain-Text Message Composer:** Authoring area and send action for plain-text payloads over open connections.
- **Lifecycle & Teardown Management:** Deterministic connection closure on tab close, application exit, and safe Idle state on tab restoration at startup.
- **Automation Identities:** Declaration and assignment of stable widget identities (`WS_*`) for testing and automation.
- **Automated Verification:** Comprehensive GUI and agent end-to-end tests validating user interactions, state transitions, stream updates, and UI identity resolution.

**Out of Scope:**
- Advanced stream filtering, text search, pause/resume auto-scroll, entry detail inspection pane, and transcript file export (covered in WS-5).
- Advanced multi-format composer (JSON, Hex, Base64), format syntax validation, message presets, and sequence automation runner (covered in WS-6).
- Deep dynamic templating resolution, egress heuristic secret filtering, and environment variable hover tooltips (covered in WS-7).
- Custom TLS certificate configuration and TLS error override dialogs (covered in WS-8).
- Model Context Protocol (MCP) bounded probe integration (covered in WS-9).
- Global concurrency ceilings and Prometheus telemetry metrics (covered in WS-10).

### Constraints and Assumptions

- **Existing Tab System Integration:** WebSocket session tabs must seamlessly integrate into PyPost's existing tab bar and workspace architecture without altering standard tab navigation behavior.
- **Strict Layering & Modularity:** Presenters and widgets must adhere to the project's architectural layering standards, ensuring clear separation between UI presentation, state coordination, and underlying transport protocols.
- **Headroom & Code Quality Standards:** Module size caps and architectural baseline limits must be strictly respected.
- **Accessible State Display:** Status must never be conveyed solely through color differences; every state must feature distinct text and symbolic glyphs/icons.
- **Offline Testability:** All automated tests must execute deterministically in offline/isolated environments without relying on external network endpoints.

## Functional Requirements

- **FR-1: Profile Opening & Tab Management**:
  - Double-clicking a WebSocket connection item in the collections tree opens a new session tab populated with the profile's saved configuration (name, URL, headers, params, subprotocols).
  - If a tab for the selected profile is already open, the application focuses the existing tab rather than opening a duplicate.
  - Closing a tab releases the associated session and terminates any active connection cleanly.
  - Tab state restoration upon application startup re-opens previously open WebSocket tabs in an `Idle` state without initiating automatic network connections.

- **FR-2: Connection Lifecycle Control**:
  - Provide an explicit **Connect** action to initiate a handshake with the configured endpoint.
  - When the connection is in-flight or established, provide an explicit **Disconnect** (or **Cancel**) action to terminate the session.
  - The Connect/Disconnect action must remain visually and functionally distinct from the message Send action.

- **FR-3: Multi-Modal State Feedback & Badging**:
  - Display the current session state in both the tab header area and the main tab strip.
  - Represent each lifecycle state (`Idle`, `Connecting`, `Open`, `Closing`, `Reconnecting`, `Failed`) with:
    - An explicit text label describing the state.
    - A distinct symbolic glyph or icon (e.g. hollow circle for Idle, animated/tilde for Connecting, filled circle for Open, cross for Failed).
  - Include summary metrics in the header badge when available (e.g. negotiated subprotocol, message count, elapsed duration).

- **FR-4: Dynamic Connection Parameter Locking**:
  - Allow full editing of URL, query parameters, handshake headers, and subprotocols when the session is in `Idle` or `Failed` states.
  - Automatically switch connection parameter fields to read-only when the session transitions to `Connecting`, `Open`, `Closing`, or `Reconnecting`.
  - Display a prominent, contextual notice or banner indicating: *"Connection parameters are read-only while connected. Disconnect to edit."*
  - Re-enable editing immediately when the connection returns to `Idle` or `Failed`.

- **FR-5: Chronological Message & Event Stream Display**:
  - Display an integrated stream showing all sent messages, received messages, and connection lifecycle events in strict chronological order.
  - Each entry must indicate:
    - Timestamp (local/UTC time with millisecond precision).
    - Direction / Kind indicator (e.g. outbound message `->`, inbound message `<-`, informational event `(i)`).
    - Payload size (e.g. byte count).
    - Payload text or lifecycle description.
  - The stream must retain entries across temporary disconnections or reconnect attempts until explicitly cleared by the user or evicted by buffer bounds.

- **FR-6: Plain-Text Message Authoring & Dispatch**:
  - Provide a message composer area allowing multi-line text entry.
  - Provide a **Send Message** action (accessible via button click and keyboard shortcut).
  - Allow message dispatch only when the session is in the `Open` state.
  - If the user attempts to send while not connected, provide immediate feedback indicating that an active connection is required.

- **FR-7: Secret Masking at Stream Ingestion**:
  - Ingest raw network frames and lifecycle events through the secret masking pipeline before appending to the stream view.
  - Replace values matching hidden environment variables with standard redaction placeholders (`***`), ensuring sensitive tokens or passwords are never displayed in cleartext.

- **FR-8: Automation & Identity Support**:
  - Assign unique, stable automation identities (`WS_*`) to all key UI controls, including the URL bar, Connect/Disconnect button, state badge, parameter tables, stream list, composer editor, and Send button.
  - Ensure all identifiers are resolvable by automated GUI testing harnesses and end-to-end test agents.

## Non-Functional Requirements

- **NFR-1: Visual Accessibility & Contrast**:
  - All status indications must satisfy WCAG 2.1 accessibility criteria by conveying state through text labels and distinct geometric glyphs in addition to color accents.
  - High-contrast visual distinctions must be maintained across all supported UI themes.
- **NFR-2: Smooth UI Responsiveness & Batched Intake**:
  - Stream updates must be ingested in periodic batches (e.g. ~33 ms flush cycle) to prevent UI thread starvation and maintain smooth 30+ FPS responsiveness during high-throughput message bursts.
  - Virtualized list rendering must be used to ensure consistent scrolling performance regardless of the number of retained messages.
- **NFR-3: Deterministic Resource Teardown**:
  - Closing a tab, closing the main window, or quitting the application must deterministically abort or close active network connections within a bounded timeout, preventing orphan background threads or hanging sockets.
- **NFR-4: Secret Security & Privacy**:
  - Redaction of sensitive values must occur prior to rendering in the stream model or storing in memory buffers, preventing accidental credential leakage via screen capture, memory dumps, or logs.
- **NFR-5: Modularity & Layering Compliance**:
  - Presentation and UI logic must remain cleanly decoupled from transport-level network code.
  - Regression limits and line-of-code caps across touched modules must remain strictly within specified architectural boundaries.
- **NFR-6: Test Automation & Reliability**:
  - Automated test suites must cover tab opening, state transitions, connection parameter locking, message dispatch, stream rendering, and tab closure.
  - All automated tests must declare explicit timeouts and run deterministically against local mock servers without internet access.

## Main Entities and Attributes

- **WebSocket Connection Profile**:
  - `id`: Unique identifier of the saved profile.
  - `name`: User-facing name of the connection profile.
  - `url`: Target endpoint URL (e.g. `ws://localhost:8080/feed` or `wss://api.example.com/v1`).
  - `headers`: Key-value pairs representing HTTP handshake headers.
  - `params`: Key-value pairs representing URL query parameters.
  - `subprotocols`: List of requested WebSocket subprotocol strings.

- **WebSocket Session Tab**:
  - `tab_id`: Unique identifier associated with the workspace tab page.
  - `profile_id`: Reference to the underlying connection profile.
  - `current_state`: Current lifecycle state of the session (`Idle`, `Connecting`, `Open`, `Closing`, `Reconnecting`, `Failed`).
  - `is_connected`: Boolean indicating if the session is currently in an active communication state.
  - `read_only_parameters`: Boolean flag indicating whether connection parameter inputs are locked.

- **Session State Indicator**:
  - `state_name`: Textual representation of the state (e.g. "Connecting", "Open", "Failed").
  - `symbolic_glyph`: Accessible symbol/icon representing the state (e.g. hollow circle, spinning marker, solid circle, exclamation mark).
  - `status_summary`: Contextual details (e.g. negotiated subprotocol, connection duration, message throughput).

- **Connection Configuration Editor**:
  - `url_field`: Text input for endpoint URL.
  - `query_params_table`: Key-value table editor for URL query parameters.
  - `headers_table`: Key-value table editor for handshake request headers.
  - `subprotocols_field`: Input field for specifying supported subprotocols.
  - `lock_notice`: Informational banner displayed when fields are disabled during active connections.

- **Chronological Message Stream**:
  - `entries`: Ordered sequence of stream events.
  - `entry_count`: Total number of visible stream entries.
  - `direction`: Transmission direction of each entry (`Inbound`, `Outbound`, `Informational`).
  - `timestamp`: Time of event occurrence with millisecond precision.
  - `formatted_payload`: Masked and formatted content displayed to the user.

- **Message Composer**:
  - `text_editor`: Input area for authoring message content.
  - `send_action`: Trigger to transmit the authored message across the active socket.
  - `is_send_enabled`: Condition determining whether the send action is active (requires Open state).

## User Scenarios

### Scenario 1: Opening a Profile and Connecting
1. The user navigates the collection tree and double-clicks a saved WebSocket profile named "Live Order Book".
2. PyPost opens a new session tab labeled "ws Live Order Book" in the main workspace, displaying the endpoint URL `wss://stream.example.com/orders` and configured headers.
3. The session tab initializes in the `Idle` state with a hollow circle glyph and `Idle` text badge.
4. The user clicks the **Connect** button (or presses `Ctrl+Shift+Enter`).
5. The session state transitions to `Connecting...` with an animated glyph. The Connect button changes to **Cancel**, and the URL and header fields become read-only with a notice: *"Connection parameters are read-only while connected. Disconnect to edit."*
6. The server accepts the handshake. The session state transitions to `Open` with a solid circle glyph, displaying the negotiated subprotocol in the header badge.
7. The message composer and Send button become enabled.

### Scenario 2: Composing and Sending a Message
1. With the connection in the `Open` state, the user clicks into the message composer area.
2. The user types a plain-text subscription command: `{"action": "subscribe", "symbol": "BTC-USD"}`.
3. The user clicks **Send Message** (or presses `Ctrl+Enter`).
4. The message is transmitted over the socket.
5. The sent message immediately appears in the chronological stream with an outbound indicator (`->`), timestamp, payload size, and the sent text.
6. A few milliseconds later, the server replies with an acknowledgment.
7. The reply appears in the stream with an inbound indicator (`<-`), timestamp, payload size, and the server's response text.

### Scenario 3: Preventing Mid-Session Parameter Modifications
1. While the session is in the `Open` state, the user attempts to click into the URL bar to modify query parameters.
2. The URL input and header tables are locked in read-only mode, and a visual tooltip reminds the user: *"Disconnect to edit connection settings."*
3. The user clicks the **Disconnect** button.
4. The connection terminates cleanly, transitioning through `Closing...` to `Idle`.
5. The URL and header fields immediately become editable again, and the read-only notice disappears.

### Scenario 4: Handling Connection Failure
1. The user enters an invalid or unreachable WebSocket URL `ws://127.0.0.1:9999/nonexistent` and clicks **Connect**.
2. The session transitions to `Connecting...`.
3. The network connection fails.
4. The session transitions to `Failed` with a cross/error glyph and explicit error description in the badge (e.g. `Failed - Connection refused`).
5. A lifecycle event entry is added to the stream recording the failure timestamp and error reason.
6. The connection fields return to an editable state, allowing the user to correct the URL and retry.

### Scenario 5: Clean Tab Teardown and Safe Restart
1. The user has an active, connected session tab exchanging real-time telemetry messages.
2. The user clicks the close button (`X`) on the session tab.
3. PyPost deterministically sends a standard close frame, terminates the underlying socket, and frees tab resources without leaving hanging background connections.
4. The user restarts PyPost with previously open tabs saved in settings.
5. The restored WebSocket tab re-opens in the `Idle` state, displaying the saved configuration without attempting to connect automatically.

### Scenario 6: Secret Masking in Handshake and Messages
1. The user configures a WebSocket profile with a handshake header `Authorization: Bearer {{API_SECRET}}`, where `API_SECRET` is marked as a hidden environment variable.
2. The user connects and sends a message containing the token.
3. When the handshake lifecycle event and sent message entry are added to the stream display, the secret token value is automatically replaced with `***`.
4. Cleartext credentials are never rendered in the UI stream or stored unmasked in the view buffers.

## Q&A

| Question | Answer |
| --- | --- |
| Why is Connect/Disconnect separate from Send Message? | WebSocket is a persistent, stateful protocol. Unlike HTTP where sending a request implicitly opens and closes a connection, WebSockets require establishing an active connection before messages can be exchanged, and keeping it open across multiple message transmissions. |
| Why must connection parameters be read-only during active sessions? | Modifying HTTP handshake headers or URL query parameters on a running socket does not alter the already-established connection. Allowing edits while connected causes confusion where users believe they updated active connection parameters. Freezing fields with a clear explanatory notice eliminates this ambiguity. |
| Why are state indicators required to use text and symbols rather than color alone? | Accessibility compliance (WCAG 2.1). Relying solely on color (such as green/red dots) prevents users with color blindness or those using high-contrast/monochrome displays from reliably discerning connection states. Combining explicit text and distinct geometric glyphs ensures universal clarity. |
| What happens when the user closes a tab while a connection is active? | The application performs a deterministic graceful teardown: it initiates a normal socket closure, cleans up event listeners, and releases memory buffers. If the socket does not close within a brief safety window, it is aborted to prevent lingering connections. |
| Why do restored tabs open in the `Idle` state instead of auto-connecting? | Safety and predictability. Initiating automatic network connections upon application launch can trigger unwanted traffic, consume network bandwidth, or fail unexpectedly if authentication tokens or network environments are not yet ready. Connecting must always be an intentional user action. |
| How does secret masking operate at this stage (WS-4)? | Any sensitive environment variables or hidden keys active in the workspace are redacted during stream entry creation (`build_stream_entry`) before entries reach the stream model. Hidden values appear as `***`, preventing accidental credential exposure. |
| How does this story differ from subsequent stories (WS-5, WS-6, WS-7)? | WS-4 delivers the minimal complete client (connect, plain-text compose/send, view stream). WS-5 will add advanced stream filtering, searching, detail inspector pane, and file export. WS-6 will add multi-format composers (JSON/Hex/Base64), presets, and sequence runners. WS-7 will add dynamic variable resolution and advanced egress filtering. |
