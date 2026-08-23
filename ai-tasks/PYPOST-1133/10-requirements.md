# PYPOST-1133: WS-5 Stream inspector

## Programming Language

Python is the implementation language for the application runtime, data models, user interface presenters/views, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost supports interactive WebSocket communication through Epic PYPOST-1123. Previous foundational stories established the transport engine (WS-1), persistent models (WS-2), bounded stream buffers (WS-3), and the primary interactive session tab with basic chronological stream display and plain-text sending (WS-4).

During real-world development, testing, and debugging of WebSocket endpoints, streams often receive hundreds or thousands of high-frequency messages (market data feeds, telemetry updates, chat channels, sensor readings). Without dedicated stream inspection and triage tools, a fast-moving stream quickly overwhelms the user interface and makes diagnosing individual payloads impossible.

The goal of this task (WS-5) is to deliver a **high-performance, readable, and interactive Stream Inspector** that empowers developers to inspect busy streams while new data continues to arrive:
- **Smooth, virtualized scrolling on high-volume streams:** Maintain silky, non-stuttering scrolling and responsive rendering even when holding up to 5,000 messages, avoiding per-row widget allocation bottlenecks.
- **Precision multi-dimensional filtering:** Enable users to isolate relevant messages instantly by filtering across transmission directions (inbound, outbound), entry kinds (messages, lifecycle events), and toggling routine lifecycle noise (e.g. heartbeat pings/pongs).
- **Instant full-text search with match accounting:** Allow real-time textual searching across stream payloads with immediate feedback reporting total match counts.
- **Honest display pause and follow-tail navigation:** Give users total control over viewport movement. When viewing historical entries or pausing auto-scroll, the UI stops tailing while the underlying network session continues receiving in the background; resuming instantly jumps back to the live tail.
- **Deep single-entry inspection:** Provide a dedicated detail inspection pane allowing users to inspect full message contents with text wrapping, format conversion (e.g. hexadecimal inspection), and wire-size metadata.
- **One-click workflow continuity via variable capture:** Allow users to capture dynamic values (such as session tokens, order IDs, transaction hashes) directly from stream entries into environment variables ("Set as variable...") without manual retyping.
- **Secure and masked transcript export:** Provide dual-format export (structured JSON array and plain-text lines) incorporating dropped-message metadata and enforcing strict secret masking so shared transcripts remain safe and traceable.
- **Unambiguous stream clearing and drop accounting:** Allow emptying retained messages to start fresh while keeping the connection open, and clearly report when and why messages were evicted (capacity vs memory limits).

## User Stories

- As an **API developer testing high-frequency feeds**, I want the stream log to scroll smoothly and remain responsive without UI lag when thousands of messages arrive, so that I can inspect high-throughput WebSocket streams without freezing my application.
- As a **developer debugging specific payloads**, I want to filter the stream by direction (incoming vs outgoing) and entry kind (messages vs lifecycle events), so that I can focus only on relevant data exchanges.
- As a **tester searching for error codes or transaction IDs**, I want a search bar with real-time match count reporting, so that I can quickly locate specific payloads and know how many matching occurrences exist.
- As a **developer reviewing a filter that returned zero results**, I want clear visual feedback showing how many total messages are hidden and a one-click way to reset the filter, so that I never wonder if the stream is empty or simply filtered out.
- As an **engineer reading an incoming message**, I want to pause the live viewport following the tail while the session keeps receiving in the background, so that the message does not scroll away before I finish reading it.
- As an **API tester**, I want the pause control to explicitly state that it pauses display (not network intake), so that I understand background buffering continues without misleading me about network backpressure.
- As a **developer resetting a test scenario**, I want a Clear button that empties the current stream log and resets drop counters while keeping the active connection alive, so that I can start fresh without reconnecting.
- As an **operator monitoring long-running sessions**, I want a clear drop notice displaying how many messages were dropped and the specific cause (capacity or memory budget), so that I am always aware when stream history is truncated.
- As a **developer inspecting complex or binary payloads**, I want a detail pane with word-wrap toggles, format switching (e.g. hex view), and a copy button that preserves secret redaction, so that I can thoroughly analyze payload structure.
- As an **API developer chaining workflows**, I want to select a value in the stream detail pane and save it directly as an environment variable, so that I can immediately use server-generated identifiers in subsequent messages or HTTP requests.
- As a **tester sharing bug reports**, I want to export the stream transcript to JSON or plain-text files including drop counts and metadata, so that colleagues can review the recorded session with full context.
- As a **security-conscious engineer**, I want exported transcripts and copied clipboard entries to strictly mask sensitive environment secrets, so that credentials are never leaked outside the workspace.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Virtualized High-Capacity Stream Rendering:**
   - A stream containing 5,000 entries scrolls smoothly and maintains responsive user interaction without allocating per-row widgets.
   - Live stream updates continue to render smoothly via batched UI flushes (~33 ms cycles) without starving the main interface.
2. **Multi-Dimensional Filtering:**
   - The user can filter the stream by transmission direction (`All`, `Inbound / <-`, `Outbound / ->`).
   - The user can filter the stream by entry kind (`All`, `Messages`, `Lifecycle events`).
   - A lifecycle noise toggle allows hiding routine heartbeat events (pings/pongs) by default to prevent clutter, while allowing them to be shown on demand.
3. **Full-Text Search & Match Reporting:**
   - Real-time text search filters stream entries by payload and detail content.
   - An indicator prominently displays the number of matching entries relative to the total visible/retained entries (e.g. `12 matches`).
4. **Empty Filter State & Recovery:**
   - When active filters match zero entries, the view displays an informative empty state indicating the number of entries hidden by the filter.
   - An intuitive, one-click action (e.g. `[Clear filter]`) resets search and filter controls to restore full stream visibility.
5. **Follow-Tail Scrolling & Display Pause Control:**
   - The stream automatically follows the latest incoming entry when scrolled to the tail.
   - Scrolling up detaches auto-follow and shows a return-to-tail indicator with unread count (e.g. `↓ N new messages`).
   - An explicit Pause control stops auto-scrolling to the tail while the underlying connection continues to receive messages in the background.
   - The control label/tooltip explicitly clarifies that it pauses display tracking rather than network intake.
   - Resuming or clicking the return indicator scrolls the viewport immediately to the tail.
6. **Stream Buffer Clearing:**
   - A Clear action empties all entries from the stream view and resets drop/message counters.
   - Clearing the stream does not interrupt, disconnect, or alter the open WebSocket session.
7. **Drop Notice & Transparent Accounting:**
   - When the stream buffer reaches its limits (max entry capacity or memory budget) and evicts older entries, a visible drop notice reports the total count of evicted messages and the specific eviction reason (capacity vs memory budget).
8. **Single-Entry Detail Inspection:**
   - Selecting any row in the stream displays its full contents in a dedicated detail inspection pane.
   - The detail pane displays entry metadata: direction, kind, payload format, exact wire byte size, timestamp, and lifecycle status.
   - Provides inspection toggles: text word-wrap toggle and format toggle (e.g. formatted text vs hexadecimal presentation).
   - If a payload exceeded display truncation limits, the detail pane clearly marks it as truncated while showing true wire size.
9. **Secure Copy & Variable Capture:**
   - A Copy action copies the entry payload to the system clipboard with all sensitive environment variable secrets safely masked.
   - A **Set as variable…** action allows the user to capture selected text or the entire payload into a workspace environment variable.
10. **Dual-Format Masked Transcript Export:**
    - Provides export actions to save the retained stream as:
      - Structured JSON transcript array.
      - Formatted plain-text transcript file.
    - Exported files include header metadata detailing dropped message counts so transcripts are never misleadingly incomplete.
    - All exported data is strictly sanitized against sensitive environment secrets.
11. **UI Identity & Automation Coverage:**
    - Stable automation identities (`WS_*`) are assigned to all stream inspector controls, filter bars, search inputs, buttons, notices, and detail elements.
    - `tests/test_ui_identity_spotcheck.py` is extended to verify all stream inspector widget identities on a live tab.
    - Automated unit, GUI, and end-to-end test suites verify filtering, searching, pause/resume, clearing, detail inspection, variable capture, and export.

## Task Description

### Problem Statement

In WS-4, PyPost introduced the fundamental WebSocket session tab, allowing users to connect to an endpoint, send plain-text messages, and view a basic chronological stream. However, in active real-time systems, WebSocket streams often produce large volumes of continuous data:
- High message frequencies quickly fill the view, making it impossible to read individual messages as they scroll past.
- Routine background protocol messages (like periodic heartbeat pings and pongs) clutter the stream, burying business-critical application messages.
- Users cannot search for specific IDs, filter by traffic direction, or inspect large or binary payloads in detail.
- If users want to capture an authentication token or transaction identifier returned by the server, they must manually transcribe it.
- When stream buffers fill up and evict older entries, users have no visibility into how many messages were dropped or why.
- Sharing recorded sessions for bug triage requires exporting transcripts that preserve full technical context (including drop counts) without leaking private API secrets.

WS-5 addresses these needs by upgrading the session tab with a comprehensive Stream Inspector.

### Scope

**In Scope:**
- **Virtualized Stream View:** High-performance list display capable of rendering 5,000+ entries smoothly without per-row widget creation overhead.
- **Filter Bar Controls:** Direction filter (All, Inbound, Outbound), Kind filter (All, Messages, Lifecycle events), and Lifecycle noise toggle (Show/Hide routine heartbeats).
- **Text Search & Match Reporting:** Instant text search query filter with dynamic match count display.
- **Empty Filter State:** Contextual banner indicating hidden message count with a single-click filter reset action.
- **Follow-Tail & Display Pause Mechanics:** Auto-tail following when at the bottom, detach on scroll up with new message count badge, and an explicit Pause/Resume display control.
- **Stream Clearing:** Instant stream reset action that clears retained messages and counters without closing the socket.
- **Drop Accounting Notice:** Informational banner displaying total dropped messages categorized by cause (capacity vs memory limits).
- **Detail Inspection Pane:** Bottom/side inspection area displaying full selected message details, metadata, word-wrap toggle, hex/text view toggle, and truncation notices.
- **Clipboard Copy with Masking:** Copying selected payloads with secret redaction applied.
- **Set as Variable Action:** Capturing stream data into workspace environment variables.
- **Dual-Format Transcript Export:** Exporting masked stream transcripts to JSON and plain-text files with dropped message accounting.
- **Automation Identities:** Declaration and verification of stable widget IDs for all inspector components.

**Out of Scope:**
- Message composer improvements, BodyFormat switching, syntax validation, presets, and sequence runners (covered in WS-6).
- Deep egress heuristic secret sanitization and templating variable hover tooltips (covered in WS-7).
- Custom TLS certificate management and SSL error override dialogs (covered in WS-8).
- Model Context Protocol (MCP) bounded probe tools (covered in WS-9).
- Global concurrency ceilings and metrics scraping (covered in WS-10).

### Constraints and Assumptions

- **High-Rate Non-Blocking Ingestion:** Stream intake and UI updates must use batched flushes (~33 ms) to maintain high frame rates (~30+ FPS) regardless of incoming message velocity.
- **Honest Flow Control:** The client does not possess application-level network flow control over the WebSocket connection (per RFC 6455). Pausing the display must never pause socket reading. The UI must be honest about this distinction.
- **Secret Redaction Invariants:** Sensitive credentials from hidden environment variables must never be exposed in cleartext on the live view, on the clipboard, or in exported transcript files.
- **Stable Identity Conventions:** All new UI elements must declare stable `pypost_ws_stream_*` identifiers conforming to project automation standards.
- **Offline Deterministic Testing:** All automated tests must run reliably offline without external network dependencies.

## Functional Requirements

- **FR-1: Virtualized High-Capacity Stream Rendering**:
  - The stream view must support holding and scrolling through up to 5,000 entries smoothly without lag.
  - The rendering mechanism must not instantiate separate widget trees per row; rendering must be virtualized and memory-efficient.
  - Batching updates at ~33 ms intervals must prevent UI thread starvation during high-throughput message bursts.

- **FR-2: Direction & Kind Filtering**:
  - Provide a direction filter allowing the user to select `All`, `Inbound (<-)`, or `Outbound (->)`.
  - Provide a kind filter allowing the user to select `All`, `Messages`, or `Lifecycle Events`.
  - Provide a lifecycle noise toggle (`Show lifecycle events` / `Hide routine heartbeats`) that filters out repetitive ping/pong entries while retaining important connection lifecycle events (handshake, errors, disconnects).

- **FR-3: Text Search & Match Counting**:
  - Provide a search text input for filtering visible stream entries by substring match against payload content or lifecycle details.
  - Dynamically display the number of matching entries (e.g. `X matches` or `X of Y visible`).
  - Search matching must be case-insensitive by default and execute with minimal latency.

- **FR-4: Empty Filter Feedback & Recovery**:
  - When filtering or searching results in zero visible rows, display a clear message indicating that no entries match the criteria (e.g. *"No messages match 'query'. 1,284 hidden by current filter."*).
  - Provide an inline **Clear filter** button that resets search queries and filter dropdowns to their default states.

- **FR-5: Follow-Tail & Display Pause Control**:
  - When the viewport is scrolled to the latest entry, automatically scroll to follow new incoming messages.
  - When the user scrolls up to inspect previous messages, automatically detach follow-tail and display an unread banner (e.g. `↓ 42 new messages`) indicating how many new messages arrived. Clicking the banner jumps directly to the tail.
  - Provide an explicit **Pause / Resume** control in the stream toolbar.
  - Activating Pause stops viewport movement while the socket continues receiving data into the stream buffer.
  - The Pause control label and tooltip must clearly communicate that it pauses display tracking rather than network intake.
  - Resuming Pause re-engages follow-tail and immediately scrolls to the latest message.

- **FR-6: Stream Buffer Clearing**:
  - Provide a **Clear** button in the stream toolbar (and shortcut `Ctrl+K`).
  - Activating Clear removes all existing entries from the stream and resets message and drop counters.
  - The open connection must remain fully connected and active without interruption.

- **FR-7: Drop Notice & Capacity Accounting**:
  - When incoming message volume exceeds the stream's entry capacity (e.g. 5,000 entries) or memory budget (e.g. 64 MiB), the oldest entries are evicted.
  - When evictions occur, a persistent drop notice banner must appear above the stream (e.g. `(!) 412 messages dropped (capacity)` or `(!) 15 messages dropped (memory budget)`).
  - The drop notice must accurately differentiate and display the eviction cause (`capacity` vs `memory_budget`).

- **FR-8: Single-Entry Detail Inspection Pane**:
  - Clicking or selecting any row in the stream opens or updates a dedicated detail pane.
  - The detail pane must display complete entry metadata:
    - Direction (`Inbound`, `Outbound`, or `Lifecycle`)
    - Payload format (`text`, `json`, `hex`, `base64`)
    - Exact wire byte size (e.g. `96 B`, `4.2 KB`)
    - Precise timestamp (with millisecond resolution)
    - Full payload text or lifecycle reason detail.
  - Provide a **Wrap** toggle to switch between multi-line word wrapping and horizontal scrolling.
  - Provide a **Hex / Format** toggle to switch between textual representation and raw hexadecimal byte inspection.
  - If a large payload was truncated for stream display, the detail pane must visibly indicate the truncation while showing the actual wire size.

- **FR-9: Secure Clipboard Copy**:
  - Provide a **Copy** action in the detail pane.
  - Copying payload content to the clipboard must ensure all sensitive environment variable secrets remain safely redacted with standard placeholders.

- **FR-10: Environment Variable Capture ("Set as variable...")**:
  - Provide a **Set as variable…** action in the detail pane (and context menu).
  - Triggering this action prompts the user or opens the variable assignment dialog, allowing the selected text or full payload value to be assigned to an environment variable in the active environment.

- **FR-11: Dual-Format Transcript Export**:
  - Provide an **Export** action offering two formats:
    - **JSON transcript**: Array of structured message objects containing timestamps, directions, formats, payloads, and wire sizes.
    - **Plain-text transcript**: Clean text log with timestamp, direction symbol, size, and payload per line.
  - Exported files must include header metadata stating total messages and dropped message counts/reasons.
  - Exported files must apply secret masking to ensure no private credentials are saved in cleartext.

- **FR-12: UI Identities & Spot-Check Integration**:
  - Declare stable widget IDs for all inspector elements (`pypost_ws_stream_view`, `pypost_ws_stream_search_input`, `pypost_ws_stream_direction_filter`, `pypost_ws_stream_kind_filter`, `pypost_ws_stream_pause_button`, `pypost_ws_stream_clear_button`, `pypost_ws_stream_export_button`, `pypost_ws_stream_drop_notice`, `pypost_ws_stream_detail`).
  - Extend automated UI identity tests (`tests/test_ui_identity_spotcheck.py`) to verify that all stream inspector identifiers resolve properly on live tabs.

## Non-Functional Requirements

- **NFR-1: Visual Responsiveness & Performance**:
  - The stream view must handle 5,000 entries with smooth, stutter-free 60 FPS scrolling.
  - Ingestion batching (~33 ms) must keep the UI thread responsive (~30+ FPS) even when incoming message velocity exceeds 1,000 msgs/sec.
- **NFR-2: Honesty in Flow Control**:
  - The UI must never give the false impression that pausing the view throttles the server or pauses network reading. Explanatory tooltips and status text must clearly state that display scrolling is paused while network intake continues.
- **NFR-3: Secret Masking & Security**:
  - Sensitive environment variable values must never appear in cleartext in the live stream view, clipboard copies, or exported transcript files.
- **NFR-4: Data Traceability & Integrity**:
  - Transcripts and drop notices must always communicate when messages have been dropped, preventing partial logs from masquerading as complete histories.
- **NFR-5: Architectural Modularity**:
  - Filtering criteria, search predicates, and export payload formatting must remain purely functional and Qt-free where possible, enabling thorough headless unit testing.
- **NFR-6: Usability & Ergonomics**:
  - Filter resets and navigation shortcuts must allow quick recovery from empty filter states with a single click.
  - Standard hotkeys (`Ctrl+F` for stream search, `Ctrl+K` for clear stream) must operate intuitively.
- **NFR-7: Deterministic Test Automation**:
  - Automated test suites must run deterministically in isolated offline environments with bounded execution timeouts.

## Main Entities and Attributes

- **Stream Entry**:
  - `seq`: Monotonic sequence identifier for row stability.
  - `ts_utc`: Timestamp formatted in ISO-8601 with millisecond precision.
  - `kind`: Category of entry (`message` or `lifecycle`).
  - `direction`: Transmission direction (`in`, `out`, or `none`).
  - `payload_format`: Data format (`text`, `json`, `hex`, `base64`).
  - `payload`: Masked content string (truncated for display if oversized).
  - `byte_size`: Actual wire payload size in bytes.
  - `truncated`: Boolean flag indicating if display payload was truncated.
  - `detail`: Additional contextual metadata (close codes, failure reasons, subprotocol).

- **Stream Filter Configuration**:
  - `direction_filter`: Selected direction filter (`All`, `Inbound`, `Outbound`).
  - `kind_filter`: Selected kind filter (`All`, `Messages`, `Lifecycle`).
  - `search_query`: Text string for substring filtering.
  - `show_lifecycle_events`: Boolean flag indicating whether routine heartbeat events are visible.

- **Stream Inspector State**:
  - `is_paused`: Boolean indicating whether viewport auto-follow is paused.
  - `is_following_tail`: Boolean indicating whether the viewport is currently pinned to the newest entry.
  - `unread_count`: Number of new entries received since the user scrolled away from the tail.
  - `selected_entry`: Currently selected `StreamEntry` displayed in the detail pane.
  - `total_entries`: Total count of retained entries in the stream buffer.
  - `matched_entries`: Number of entries currently matching the active filter and search query.
  - `dropped_counts`: Mapping of eviction causes to dropped entry counts (e.g. `{"capacity": 412, "memory_budget": 0}`).

- **Detail Inspection Pane**:
  - `is_wrap_enabled`: Boolean toggle for line wrapping.
  - `view_mode`: Presentation format mode (`Formatted Text`, `Hexadecimal Bytes`).
  - `formatted_content`: Content string prepared for inspection.

- **Export Configuration**:
  - `export_format`: Chosen file format (`JSON`, `Plain-Text`).
  - `include_metadata`: Boolean flag determining whether drop statistics and timestamps are included in file headers.

## User Scenarios

### Scenario 1: Filtering a High-Rate Stream by Direction and Kind
1. The user connects to a high-frequency trading WebSocket endpoint `wss://market.example.com/trades`.
2. Hundreds of market update messages arrive every second. Sent subscription commands quickly scroll off screen.
3. The user opens the **Direction** filter dropdown in the stream toolbar and selects **Outbound (->)**.
4. The stream view immediately updates to show only messages sent by the user, hiding all incoming server broadcasts.
5. The user selects **Inbound (<-)** and opens the **Kind** filter to select **Messages**, hiding all informational connection lifecycle logs.
6. The user selects **All** to restore full stream visibility.

### Scenario 2: Searching Payloads and Clearing Empty Results
1. The user is debugging a specific transaction and enters `order_99824` into the stream search box.
2. The stream list instantly filters down to the 3 matching messages, and the search indicator reports: `3 matches (1,420 hidden)`.
3. The user modifies the search query to `nonexistent_id`.
4. The stream displays the empty filter state banner: *"No messages match 'nonexistent_id'. 1,423 hidden by current filter."* with a **[Clear filter]** button.
5. The user clicks **[Clear filter]**. The search box is cleared and the full stream list reappears immediately.

### Scenario 3: Pausing Display to Inspect Incoming Messages
1. With data streaming continuously, the user notices an interesting error reply.
2. The user clicks the **Pause** button in the stream toolbar.
3. The viewport stops auto-scrolling, allowing the user to read the message comfortably.
4. While paused, the server continues sending updates in the background. A badge indicates `↓ 85 new messages`.
5. The user finishes inspecting the message and clicks **Resume** (or clicks the `↓ 85 new messages` badge).
6. The view immediately jumps to the tail and resumes following incoming messages in real time.

### Scenario 4: Inspecting Entry Details and Word-Wrapping
1. The user clicks on a large incoming JSON message in the stream.
2. The bottom detail pane activates, displaying:
   `<- incoming · json · 1.4 KB · 14:22:01.814`
3. Long JSON lines extend past the horizontal boundary. The user clicks the **Wrap** toggle button.
4. The payload wraps across multiple lines for easy readability without horizontal scrolling.
5. The user clicks the **Hex** toggle to inspect the raw binary byte values corresponding to the payload.

### Scenario 5: Capturing an Identifier into an Environment Variable
1. In the detail inspection pane, the user highlights a session token string `"auth_session_918237"`.
2. The user clicks **Set as variable…** (or right-clicks and chooses the action).
3. PyPost prompts for the target variable name (defaulting to `SESSION_TOKEN` or existing variable).
4. The user confirms, and the active environment variable `SESSION_TOKEN` is immediately updated with the captured value.
5. The user can now use `{{SESSION_TOKEN}}` in subsequent WebSocket presets or HTTP requests.

### Scenario 6: Eviction and Drop Notice Accounting
1. A WebSocket session runs continuously for several hours, accumulating over 5,000 entries.
2. When the 5,001st entry arrives, the oldest entry is evicted to satisfy the memory and capacity bounds.
3. A drop notice banner appears above the stream: `(!) 1 message dropped (capacity)`.
4. As more messages arrive, the counter increments smoothly: `(!) 250 messages dropped (capacity)`.
5. The user clicks **Clear**. The stream entries are removed, and the drop notice banner disappears. The connection remains open and active.

### Scenario 7: Exporting a Masked Session Transcript
1. After reproducing a bug, the user clicks **Export** in the stream toolbar and chooses **Export as JSON**.
2. PyPost prompts for a save location and writes `websocket_transcript_2026-08-22.json`.
3. The exported JSON file contains an array of all retained stream entries along with header metadata recording the total retained count and dropped count (`"dropped": {"capacity": 250, "memory_budget": 0}`).
4. Any API tokens or passwords that matched hidden environment variables are safely masked as `***` in the exported file.

## Q&A

| Question | Answer |
| --- | --- |
| Why is virtualized list rendering required instead of item widgets? | Rendering thousands of rows with separate `QWidget` allocations creates severe memory overhead and causes UI stuttering during fast scrolling. Virtualized model/view rendering instantiates visual elements only for the handful of rows currently visible on screen, keeping CPU and memory usage constant regardless of stream length. |
| What is the difference between "Pause Display" and "Pause Intake"? | "Pause Display" stops the UI viewport from following the live tail while the application continues reading from the socket into the stream buffer. "Pause Intake" would mean stopping network reads, which WebSocket protocols do not support natively without risk of buffer bloat or connection drops. The UI explicitly presents this as Pause Display so users are not misled. |
| How does the lifecycle noise toggle improve usability? | WebSocket servers often exchange heartbeat ping/pong frames every 5-30 seconds to maintain connection health. In a long-running session, hundreds of routine pings clutter the stream. Hiding routine heartbeats by default keeps the view clean while still surfacing critical lifecycle events (connect, disconnect, errors). |
| Why does Clear empty the stream without disconnecting? | Users frequently run multi-stage test scenarios over a single connection and want to clear out setup traffic before testing a specific command. Forcing a disconnect to clear the stream would break active stateful sessions. |
| How does drop accounting help debugging? | If an issue occurred in historical messages that were evicted due to capacity limits, knowing that messages were dropped (and exactly how many) prevents engineers from erroneously concluding that the server never sent the missing frames. |
| Why are export files masked? | Transcripts are frequently attached to issue trackers, defect reports, or shared with teammates. Applying secret sanitization to export files guarantees that workspace credentials (like bearer tokens or passwords) are never accidentally leaked. |
| How does "Set as variable..." work with sensitive values? | When capturing a value from the stream, the user can choose to store it as a standard or hidden environment variable. Once stored as hidden, subsequent occurrences in the stream and exports are automatically redacted. |
