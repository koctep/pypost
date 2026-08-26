# WebSocket Guide

PyPost provides full interactive testing, inspection, and automation for WebSocket endpoints.
You can connect to `ws://` and `wss://` services, inspect live bi-directional frame streams,
compose messages in multiple formats, organize message presets and sequences, apply environment
variable templating with secret masking, and expose WebSocket profiles as bounded MCP probe tools
for AI assistants.

## Connecting to a WebSocket

To create and configure a WebSocket connection:

1. Open a WebSocket workspace tab:
   - **New blank tab:** Press `Ctrl+N` or click the tab-bar **+**, then choose **WebSocket**
     from the protocol picker. A draft tab titled **New WebSocket** opens with an empty URL
     field.
   - **Saved profile:** Click a WebSocket profile (`ws <name>`) in the Collections sidebar, or
     right-click it and choose **New tab** for an isolated editable copy (see
     [Collections](collections.md)).
2. Enter the target endpoint URL (`ws://` or secure `wss://`).
3. Under the connection details tabs:
   - **Params**: Configure query parameters appended to the connection URL.
   - **Headers**: Add custom HTTP handshake headers (for example, `Authorization` or `Origin`).
   - **Subprotocols**: Specify comma-separated WebSocket subprotocols (e.g., `graphql-ws`, `v1`).
4. Click **Connect** (or press `F5` / `Ctrl+Enter` while focused on the URL bar).

The connection status badge displays current lifecycle state: `DISCONNECTED`, `CONNECTING`,
`CONNECTED`, `CLOSING`, or `RECONNECTING`. When connected, handshake configuration fields
are locked to prevent accidental modification during an active session.

## Composing and Sending Messages

The message composer at the bottom of the WebSocket tab allows drafting and sending frames:

### Formats

- **Text (UTF-8)**: Plain text messages sent as standard text frames.
- **JSON**: Formatted JSON payloads. Includes JSON syntax validation and auto-formatting
  (`Ctrl+Shift+F`).
- **Binary**: Binary payloads formatted as Hexadecimal (e.g., `0xDE 0xAD 0xBE 0xEF`) or Base64.

### Sending

Click **Send** or press `Ctrl+Enter` inside the composer editor to transmit the active message.
Messages sent appear immediately in the stream inspector as outbound (`OUT`) frames.

## Presets and Sequences

PyPost allows managing reusable message templates and automated transmission sequences:

- **Presets**: Save frequently used messages with specific formats. You can create, duplicate,
  load into the composer, or send presets directly.
- **Sequences**: Chain multiple message presets into automated multi-step sequences.
  Configure per-step delay intervals (in milliseconds) and optional stop conditions.
  Click **Run** to execute the sequence or **Stop** to abort execution.

## Stream Inspector

The live stream inspector provides real-time visibility into all inbound and outbound frames:

### Filtering and Search

- **Direction Filter**: View `All`, `Inbound (IN)`, or `Outbound (OUT)` frames.
- **Frame Kind Filter**: Filter by `Text`, `Binary`, `Ping`, `Pong`, `Close`, or `Error`.
- **Text Search**: Real-time substring search across payload contents with match counters.

### Frame Details and Actions

Select any frame in the stream list to view its complete details:

- Formatted text payload view with word wrap toggle.
- Hex dump inspection for binary payloads.
- **Copy**: Copy raw or formatted payload to the clipboard.
- **Set Variable**: Extract values from message payloads directly into the active environment.
- **Follow Tail**: Toggle auto-scrolling to pin the view to newly arriving frames.
- **Clear**: Clear the current stream display buffer.

### Exporting Transcripts

Click **Export Stream** to save captured frames in one of three structured formats:

- **JSON**: Complete array of frame metadata and payload objects.
- **NDJSON**: Newline-delimited JSON, ideal for streaming log analysis and ingestion pipelines.
- **CSV**: Tabular export containing timestamp, direction, opcode, size, and payload columns.

## Buffer Retention and Session Limits

To prevent unbounded memory growth during high-throughput streaming:

- **Ring Buffer**: The stream viewer retains frames in a bounded memory buffer configured by
  `ws_max_stream_buffer_bytes` (default: 10 MB). When capacity is reached, older frames are
  evicted, and a drop counter notice is displayed in the inspector.
- **Session Ceiling**: PyPost enforces a concurrent active session limit configured by
  `ws_max_concurrent_sessions` (default: 10). Connecting beyond this limit displays an error
  advising you to disconnect unused sessions.

## Reconnection and Heartbeats

- **Automatic Reconnection**: When unexpected disconnections occur, PyPost attempts automatic
  reconnection using exponential backoff governed by `ws_reconnect_max_attempts`,
  `ws_reconnect_backoff_base_sec`, and `ws_reconnect_backoff_max_sec`.
- **Heartbeat Monitoring**: PyPost sends periodic ping frames (`ws_heartbeat_interval_sec`) and
  monitors pong responses (`ws_heartbeat_timeout_sec`). If the server fails to respond, the
  connection is flagged and dropped.

## Templating and Sensitive Data Masking

WebSocket URLs, handshake headers, and composer messages support environment variable
interpolation using `{{ variable_name }}` syntax.

Sensitive variables marked as **Hidden** in the active environment are automatically masked
in the stream inspector, logs, and exported transcript files, preventing credential leakage.

## AI Assistant Integration (MCP Probes)

You can expose WebSocket profiles as tools for local AI agents via the Model Context Protocol:

1. Enable **MCP Tool** on a saved WebSocket profile.
2. Configure bounded probe parameters:
   - `max_duration_sec`: Maximum listening window (default: 30s).
   - `max_messages`: Maximum number of frames to capture (default: 100).
   - `stop_when`: Optional regex pattern that halts the probe upon matching frame content.
3. AI agents invoking the tool receive a bounded JSON transcript of the captured session.

## Known Limitations

- **No `permessage-deflate` Compression**: PyPost uses Qt's native WebSocket engine, which does
  not support RFC 7692 per-message deflate compression extensions.
- **Handshake Response Introspection**: When a WebSocket handshake is rejected by the server
  (e.g., HTTP 401 or 403), the transport reports the HTTP status code and socket error, but raw
  HTTP response bodies and response headers returned during the failed upgrade are not
  inspectable.

## Related Documentation

- [Interface Overview](interface.md) — main window layout and tab controls
- [Collections](collections.md) — saving WebSocket profiles and downgrade caveats
- [Settings](settings.md) — configuring `ws_*` limits and timeouts
- [MCP Tools](mcp-tools.md) — exposing profiles to AI agents
