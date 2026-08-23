# PYPOST-1135: WS-7 Environments, templating and secret masking

## Research

### R-1 Existing Baseline and Module Inventory

Research into current repository components establishing the baseline for WS-7:

1. **Environment and Secret Management Framework (`pypost/core/environment_manager.py`, `pypost/ui/presenters/env_presenter.py`):**
   - Workspace environments provide key-value variable maps (`env_vars: dict[str, str]`) and a set of sensitive variable names (`hidden_keys: set[str]`).
   - `EnvPresenter` acts as the source of truth for active environment variables and hidden keys in the desktop application. When an active environment changes or variables are edited, `EnvPresenter` emits `env_variables_changed`, `env_keys_changed`, and `env_hidden_keys_changed`.
   - `TabsPresenter` subscribes to these signals and pushes snapshots into open tabs (`doc/dev/variable_propagation.md`).

2. **Template Resolution Engine (`pypost/core/template_service.py`, `pypost/core/environment_variable_resolver.py`):**
   - `TemplateService` provides standard Jinja-compatible template rendering (`render_string(template_str, variables)`) and strict type conversions (`render_string_strict_conversion`).
   - Resolves `{{ VARIABLE }}` placeholders and registered functions (e.g. `{{ $guid }}`, `{{ $timestamp }}`).
   - If an expression contains syntax errors or references an undefined variable, `TemplateService` provides graceful fallback or diagnostic exceptions.

3. **Two-Tier Secret Masking Framework (`pypost/core/sensitive_text_sanitizer.py`, `pypost/core/sensitive_data_masking_policy.py`):**
   - **Tier 1 (Exact Replacement / Ingestion):** Replaces exact substrings matching values of variables in `hidden_keys` with `***` (`HIDDEN_PLACEHOLDER`). Preserves technical structural fidelity without regex-based mangling.
   - **Tier 2 (Heuristic Sanitization / Egress):** `sanitize_text(text, env_vars=..., hidden_keys=...)` performs comprehensive heuristic regex matching (bearer tokens, API keys, basic auth, JWTs, AWS credentials) combined with hidden-key replacement. Applied to clipboard copies, file exports, and MCP transcripts.

4. **Variable Hover & Inspection Mixins (`pypost/ui/widgets/mixins.py`, `pypost/ui/widgets/variable_aware_widgets.py`):**
   - `VariableHoverLocator` and `VariableHoverResolver` locate `{{ VAR }}` tokens under cursor and resolve their values against current variables and hidden keys.
   - `VariableHoverMixin` is mixed into `VariableAwareLineEdit` and `VariableAwarePlainTextEdit`.
   - `VariableAwareTableWidget` provides cell-level hover resolution with caching.
   - If a hovered variable is in `hidden_keys`, tooltip displays masked value `********`. If undefined, displays missing variable status.

5. **WebSocket Stream and Presenter Architecture (`pypost/core/websocket_stream.py`, `pypost/ui/presenters/websocket_presenter.py`):**
   - WS-4 established `WebSocketPresenter` as the single point of masking coordination before frames enter `MessageStream`.
   - `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes, ...)` creates immutable `StreamEntry` objects with exact secret masking applied.
   - `StreamListModel.append_batch` remains the sole writer to `MessageStream`.
   - Outgoing and incoming frames currently pass `env_vars` and `hidden_keys` to `build_stream_entry`, but template resolution at connect-time and send-time, two-tier egress sanitization, metric counter emission, and variable hover integration are not yet fully wired.

6. **Observability and Metrics Registry (`pypost/core/metrics_registry.py`, `pypost/core/metrics_otel.py`):**
   - `hidden_value_masks_applied_total` is registered with label `surface` (`"websocket"`, `"http"`, `"history"`, etc.).
   - Incrementing `hidden_value_masks_applied.labels(surface="websocket").inc()` records masking events for telemetry.

### R-2 Benchmark and Behavioral Analysis

Comparing real-time protocol development workflows with Postman, Insomnia, and PyPost security requirements:

- **Connect-Time vs Send-Time Resolution Timing:**
  - In persistent real-time protocols, connection initiation (the HTTP upgrade handshake) is an atomic event. URLs, query parameters, handshake headers, and requested subprotocols must be resolved at connection initiation and frozen for the duration of that specific connection. Modifying an environment variable while connected must not retroactively change what is recorded as the sent handshake in the stream log.
  - Conversely, outgoing message payloads sent across an open socket are distinct point-in-time transmissions. Users frequently capture dynamic session tokens or IDs from incoming frames and expect subsequent outgoing messages to resolve those new variables immediately without reconnecting.
- **Template Injection Immunity for Inbound Frames:**
  - Incoming payloads from external servers must strictly be treated as literal data. If an incoming message contains `{{ user_id }}` or malicious template syntax, passing it through `TemplateService` could leak internal client variables or trigger remote code/template execution. Inbound frames must only undergo exact hidden-secret masking, never template evaluation.
- **Non-Destructive Ingestion vs Deep Egress Sanitization:**
  - During live stream inspection, applying heuristic regex masks can mangle legitimate server payloads (e.g. hex dumps, UUIDs, or base64 tokens under debugging). Exact hidden-value replacement prevents secret leakage while preserving data structure.
  - For egress paths (clipboard copy, JSON/text file exports, MCP tool transcripts), full heuristic sanitization (`sanitize_text`) ensures sensitive data never escapes the process boundary into tickets, chat, or external systems.

---

## Implementation Plan

### P-1 Delivery Phases

1. **Phase 1: Connect-Time Handshake Parameter Resolution (`pypost/ui/presenters/websocket_presenter.py`)**
   - In `WebSocketPresenter.handle_connect()`:
     - Read connection parameters from `connection_editor` or `WebSocketConnection`.
     - Resolve target URL, query parameters, handshake headers, and requested subprotocols using `TemplateService`.
     - Build resolved `HandshakeTarget(url=resolved_url, headers=resolved_headers, subprotocols=resolved_subprotocols)`.
     - Pass resolved target to `WebSocketSessionController.open()`.
     - Sanitize URL and headers when emitting lifecycle events and log records (e.g., masking query string secrets and header values).
     - Ensure mid-session environment modifications do not mutate the active connection's frozen handshake parameters.

2. **Phase 2: Per-Send Message Payload Resolution (`pypost/ui/presenters/websocket_presenter.py`, `pypost/ui/widgets/websocket/composer.py`, `pypost/core/qt/websocket_sequence_runner.py`)**
   - Outgoing message payloads (composer text, saved presets, sequence steps) evaluate `{{ VARIABLE }}` placeholders dynamically at the instant of send:
     - Render template text via `TemplateService.render_string(payload, self._env_vars)` prior to encoding and transmission.
     - Ensure variables captured mid-session (via `variable_capture_requested` / `Set as variable...`) immediately update `_env_vars` and apply to subsequent sends.
     - Pass the resolved string to the codec and session controller.
     - Record the outbound frame in the stream with exact hidden-variable masking.

3. **Phase 3: Inbound Literal Safety & Tier 1 Masking (`pypost/core/websocket_stream.py`, `pypost/ui/presenters/websocket_presenter.py`)**
   - Guarantee that `_on_frame_received` passes incoming frames directly to `build_stream_entry` without calling `TemplateService`.
   - Update `_mask_secrets` / `build_stream_entry` to count applied masks and notify metrics when exact hidden values are replaced.
   - Assert incoming payloads with `{{ ... }}` remain unaltered literals (except for exact hidden variable matches).

4. **Phase 4: Tier 2 Egress Sanitization on Clipboard & File Export (`pypost/ui/widgets/websocket/stream_view.py`, `pypost/core/websocket_stream_export.py`)**
   - Detail Pane Clipboard Copy:
     - In `StreamDetailPane._on_copy_clicked()`, pass selected text or payload through `sanitize_text(text, env_vars=self._env_vars, hidden_keys=self._hidden_keys)` before writing to `QApplication.clipboard()`.
   - Dual-Format Transcript Exports:
     - Update `export_stream_to_json_file` and `export_stream_to_text_file` to accept `env_vars` and `hidden_keys`, applying `sanitize_text` to all exported payload strings, details, and metadata before disk serialization.
     - Update `WebSocketStreamView.export_json` and `export_text` to pass active `env_vars` and `hidden_keys`.

5. **Phase 5: Interactive Variable-Aware Hover Tooltips Across All WebSocket UI Inputs**
   - Connect active environment variables and hidden keys from `WebSocketPresenter` to child widgets:
     - `WebSocketConnectionEditor`: propagate to `url_input` (`VariableAwareLineEdit`), `subprotocols_input` (`VariableAwareLineEdit`), `params_table` (`WebSocketKeyValueTable`), and `headers_table` (`WebSocketKeyValueTable`).
     - `WebSocketComposer`: update `payload_edit` to `VariableAwarePlainTextEdit` (or ensure `VariableHoverMixin` is enabled) and propagate `set_variables` / `set_hidden_keys`.
     - `WebSocketPresetsPanel`: propagate variables and hidden keys to preset and sequence step payload editors.
   - Hovering displays resolved variable value, or `********` if hidden in `hidden_keys`, or unresolved indicator.

6. **Phase 6: Telemetry & Observability Accounting (`pypost/core/metrics_registry.py`, `pypost/ui/presenters/websocket_presenter.py`)**
   - Increment `hidden_value_masks_applied_total{surface="websocket"}` whenever a hidden variable is masked during stream ingestion or egress sanitization.
   - Enforce log redaction across all WebSocket components: log only `url_masked` and structured metadata; never log raw payloads or secret header values.

7. **Phase 7: Comprehensive Automated Verification**
   - Unit, integration, and GUI tests covering connect-time resolution, per-send dynamic resolution, inbound literal safety, two-tier masking, clipboard and export sanitization, hover tooltips, and metrics accounting.

### Mandatory — Failing Repro (next Step 3)

- **Test Suite Location:** `tests/test_websocket_environments_templating.py` and `tests/test_websocket_secret_masking.py`.
- **Desired Behavior Assertions:**
  1. **Connect-Time Handshake Templating:** Assert that connecting with URL `{{ WS_HOST }}/feed` and header `Authorization: Bearer {{ WS_TOKEN }}` resolves using active environment variables at connection time; assert that changing `WS_TOKEN` mid-session does not alter the active session's recorded handshake.
  2. **Per-Send Outgoing Payload Templating:** Assert that sending a composer message `{"order": "{{ ORDER_ID }}"}` resolves dynamically at send time; assert that updating `ORDER_ID` mid-session immediately updates the payload sent over the wire on the next send without reconnecting.
  3. **Inbound Literal Safety:** Assert that an incoming frame containing literal `{{ SECRET_KEY }}` or Jinja syntax is displayed and stored verbatim as literal text and is never rendered by `TemplateService`.
  4. **Tier 1 Stream Masking:** Assert that hidden variables used in outgoing frames or incoming payloads appear as `***` (`HIDDEN_PLACEHOLDER`) in `StreamEntry.payload`.
  5. **Tier 2 Egress Sanitization:** Assert that copying text from the stream detail pane to the clipboard, exporting to JSON transcript, and exporting to plain-text transcript applies `sanitize_text` to strip both hidden environment variables and heuristic sensitive patterns (Bearer tokens, API keys).
  6. **UI Variable Hover Tooltips:** Assert that hovering over `{{ VAR }}` in URL, headers, params, subprotocols, and composer displays the resolved value, or `********` if the variable is marked hidden.
  7. **Telemetry Increment:** Assert that `hidden_value_masks_applied_total{surface="websocket"}` increments when masking secrets.
  8. **Zero Secret Leakage:** Assert that hidden secrets never appear in logs or metric labels.
- **Forcing the Failure:** Running these tests against the current codebase will fail because:
  - `WebSocketPresenter.handle_connect()` does not yet resolve `TemplateService` variables for target URL, headers, and subprotocols.
  - `WebSocketComposer.send_current_payload()` transmits raw unrendered payload text without evaluating `TemplateService` expressions.
  - Stream export functions and clipboard copy do not pass `env_vars` and `hidden_keys` through `sanitize_text`.
  - Hover variables are not propagated to `composer` or `connection_editor` child tables.
  - `hidden_value_masks_applied_total{surface="websocket"}` is not incremented.
- **Sequencing:** Step 2 (architecture approved) -> Step 3 (automated red tests committed) -> Step 4 (implementation until all tests green).

---

## Architecture

### A-0 Decision Register

- **D-1: Connect-Time vs Send-Time Resolution Boundaries:** Handshake parameters (`url`, `params`, `headers`, `subprotocols`) are resolved once when `handle_connect()` is triggered, constructing a frozen `HandshakeTarget`. Message payloads (composer, presets, sequence steps) are resolved at the instant of send in `handle_send_message()` / `send_current_payload()` / sequence runner.
- **D-2: Inbound Payload Literal Immutability:** Inbound frames received from the transport/controller are never evaluated by `TemplateService`. They are treated strictly as raw bytes/text, processed only by `build_stream_entry` for Tier 1 exact hidden-secret masking.
- **D-3: Two-Tier Masking Separation:**
  - **Tier 1 (Stream Ingestion / Live Display):** Exact replacement of hidden environment variable values (`HIDDEN_PLACEHOLDER` / `***`). Avoids heuristic regex mangling on live technical debugging data.
  - **Tier 2 (Egress Surfaces):** Full heuristic sanitization (`sanitize_text`) applied on clipboard copy, JSON file export, plain-text file export, and MCP transcripts.
- **D-4: Invariant Seam Preservation:** `WebSocketPresenter` coordinates environment propagation, template resolution, and masking. `StreamListModel.append_batch` remains the sole writer to `MessageStream`. `WebSocketSessionController` remains Qt/stream-free and unaware of environments. No unmasked secret is ever stored in `MessageStream`.
- **D-5: Hover Tooltip Consistency:** WebSocket UI inputs (`WS_URL_INPUT`, `WS_SUBPROTOCOLS_INPUT`, `WS_PARAMS_TABLE`, `WS_HEADERS_TABLE`, `WS_COMPOSER_EDIT`, preset editors) inherit standard `VariableHoverMixin` / `VariableAwareTableWidget` behavior, displaying resolved values or `********` for hidden variables.
- **D-6: Observability & Metric Accounting:** The Prometheus/OpenTelemetry counter `hidden_value_masks_applied_total` is incremented with label `surface="websocket"` whenever a secret is masked during ingestion or egress.

### A-1 Component Architecture & Layering

```text
       Collections Tree                        EnvPresenter
      (WebSocket item)                      (env_vars, hidden_keys)
             | open                                    |
             |                                         | env_variables_changed
             v                                         | env_hidden_keys_changed
   +---------------------------------------------------+--------------------------+
   | WebSocketPresenter                               (ui/presenters)             |
   |                                                                              |
   |   - Holds active snapshot of `env_vars` and `hidden_keys`                    |
   |   - Connect-time: resolves URL, params, headers, subprotocols via             |
   |     TemplateService -> frozen HandshakeTarget                                |
   |   - Send-time: resolves outgoing payload via TemplateService                |
   |   - Ingestion: converts RawFrame -> StreamEntry via build_stream_entry       |
   |     (Tier 1 exact hidden-value masking)                                      |
   |   - Telemetry: increments hidden_value_masks_applied_total{surface="websocket"}|
   |   - Propagates env snapshot to UI widgets for hover tooltips                 |
   +---+-------------------------+------------------------+-----------------------+
       | HandshakeTarget         | Batched StreamEntries  | Snapshot (vars, keys)
       | Outgoing frames         | (33ms timer flush)     |
       v                         v                        v
   +---------------------------+ +--------------------+ +-------------------------+
   | WebSocketSessionController| | StreamListModel    | | WebSocketTab            |
   |        (core/qt)          | | (ui, virtualized)  | |  - Header & StateBadge  |
   |                           | | sole ring writer   | |  - ConnectionEditor     |
   | State machine & timers    | +---------+----------+ |    (URL, Params,        |
   | Qt/stream/env free        |           |          |     Headers, Subprotos)   |
   +-------------+-------------+           v          |  - WebSocketStreamView    |
                 |               +--------------------+ |    (Filters, Search,    |
                 |               | MessageStream      | |     DetailPane)         |
                 |               | (core, bounded)    | |  - WebSocketComposer    |
                 v               +---------+----------+ |    (Format, Edit,       |
   +---------------------------+           |            |     Presets, Sequences) |
   | WebSocketTransport        |           |            +------------+------------+
   | (core/qt)  QWebSocket     |           v                         |
   +---------------------------+     Egress Surfaces                 |
                                     (Tier 2 heuristic sanitization: |
                                      sanitize_text)                 v
                                     - Clipboard Copy <--------------+
                                     - JSON File Export <------------+
                                     - Plain Text File Export <------+
                                     - Agent / MCP Transcripts <-----+
```

### A-2 Data Flow and Lifecycle Resolution Timing

#### 1. Connect-Time Resolution Sequence

```text
User clicks 'Connect'
       |
       v
WebSocketPresenter.handle_connect()
       |
       +---> Read raw URL, Params, Headers, Subprotocols from ConnectionEditor
       |
       +---> TemplateService.render_string(url, env_vars)
       +---> TemplateService.render_string(param_keys/values, env_vars)
       +---> TemplateService.render_string(header_keys/values, env_vars)
       +---> TemplateService.render_string(subprotocols, env_vars)
       |
       +---> Construct resolved HandshakeTarget(url, headers, subprotocols)
       |
       +---> Emit lifecycle event with masked URL (query secrets masked)
       |
       +---> WebSocketSessionController.open(resolved_target)
```

#### 2. Per-Send Payload Resolution Sequence

```text
User clicks 'Send Message' / Sequence Step triggers
       |
       v
WebSocketPresenter.handle_send_message() / SequenceRunner
       |
       +---> Read raw template payload from Composer / Preset / Step
       |
       +---> TemplateService.render_string(raw_payload, env_vars)  <-- Dynamic send-time
       |
       +---> WebSocketCodec.encode_payload(rendered_payload, format)
       |
       +---> WebSocketSessionController.send_text() / send_binary()
       |
       v
Frame Sent Signal
       |
       v
build_stream_entry(frame, env_vars=env_vars, hidden_keys=hidden_keys)
       |  (Tier 1 exact hidden-value replacement with '***')
       |  (Increment hidden_value_masks_applied_total{surface="websocket"})
       v
StreamListModel.append_batch([entry]) -> MessageStream
```

#### 3. Inbound Frame Ingestion (Literal Safety) Sequence

```text
Transport receives frame from peer
       |
       v
WebSocketSessionController emits frame_received(RawFrame)
       |
       v
WebSocketPresenter._on_frame_received(RawFrame)
       |
       +---> NO TemplateService invocation (Literal Safety Invariant)
       |
       +---> build_stream_entry(RawFrame, env_vars=env_vars, hidden_keys=hidden_keys)
       |       (Tier 1 exact hidden-value replacement with '***')
       |       (Increment metric if hidden secret present in server frame)
       v
StreamListModel.append_batch([entry]) -> MessageStream
```

#### 4. Egress Sanitization Sequence (Tier 2)

```text
User clicks 'Copy' in StreamDetailPane
       |
       v
StreamDetailPane._on_copy_clicked()
       |
       +---> Extract text to copy (selection or entry payload)
       +---> sanitize_text(text, env_vars=env_vars, hidden_keys=hidden_keys)
       +---> Increment hidden_value_masks_applied_total{surface="websocket"}
       +---> QApplication.clipboard().setText(sanitized_text)

User clicks 'Export as JSON / Plain Text Transcript'
       |
       v
WebSocketStreamView.export_json() / export_text()
       |
       +---> export_stream_to_json_file(path, stream, env_vars=env_vars, hidden_keys=hidden_keys)
       +---> export_stream_to_text_file(path, stream, env_vars=env_vars, hidden_keys=hidden_keys)
       |       (Iterate entries, apply sanitize_text() to each payload/detail/meta)
       +---> Write sanitized file atomically to disk
```

### A-3 Module Responsibilities and Interface Definitions

| Module | Location | Primary Responsibilities |
| --- | --- | --- |
| `WebSocketPresenter` | `pypost/ui/presenters/websocket_presenter.py` | Coordinates environment snapshot, connects signals, performs connect-time and send-time template resolution via `TemplateService`, coordinates Tier 1 masking, propagates variables to UI, increments metrics. |
| `WebSocketSessionController` | `pypost/core/qt/websocket_session.py` | Headless session state machine, timers, frame transmission. Unaware of environment variables or template engines. |
| `WebSocketStream` | `pypost/core/websocket_stream.py` | `build_stream_entry` pure function with exact hidden-value replacement (`_mask_secrets`), ring buffer `MessageStream`. |
| `WebSocketStreamExport` | `pypost/core/websocket_stream_export.py` | Formats and writes JSON and Plain Text transcripts, applying Tier 2 `sanitize_text` across all exported entries. |
| `SensitiveTextSanitizer` | `pypost/core/sensitive_text_sanitizer.py` | Pure Tier 2 heuristic secret sanitization engine (`sanitize_text`). |
| `WebSocketConnectionEditor` | `pypost/ui/widgets/websocket/connection_editor.py` | Parameter editor hosting `VariableAwareLineEdit` and `WebSocketKeyValueTable`, supporting variable hover tooltips and read-only parameter locking. |
| `WebSocketComposer` | `pypost/ui/widgets/websocket/composer.py` | Multi-format message editor with `VariableHoverMixin` variable inspection, format validation, preset and sequence execution controls. |
| `StreamDetailPane` | `pypost/ui/widgets/websocket/stream_view.py` | Inspects selected frame, applies Tier 2 `sanitize_text` on clipboard copy, supports "Set as variable..." capture. |
| `MetricsRegistry` | `pypost/core/metrics_registry.py` | Registry hosting `hidden_value_masks_applied_total` counter with `surface` label. |

### A-4 Detailed API and Protocol Signatures

#### 1. `WebSocketPresenter` Enhancements

```python
class WebSocketPresenter(QObject):
    def __init__(
        self,
        connection: WebSocketConnection,
        settings: Optional[Any] = None,
        session_controller: Optional[WebSocketSessionController] = None,
        stream_model: Optional[StreamListModel] = None,
        env_vars: Optional[dict[str, str]] = None,
        hidden_keys: Optional[set[str]] = None,
        template_service: Optional[TemplateService] = None,
        metrics: Optional[MetricsRegistry] = None,
        parent: Optional[QObject] = None,
    ) -> None: ...

    def set_variables(self, variables: dict[str, str]) -> None:
        """Update active environment variables and propagate to child UI components."""

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Update active hidden keys and propagate to child UI components."""

    def handle_connect(self) -> None:
        """Resolve endpoint URL, params, headers, subprotocols via TemplateService and initiate connection."""

    def handle_send_message(self) -> None:
        """Resolve composer payload dynamically via TemplateService and transmit over active session."""
```

#### 2. `WebSocketStreamExport` Enhancements

```python
def format_json_transcript(
    stream: MessageStream,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Format stream entries as JSON with Tier 2 heuristic sanitization."""

def format_text_transcript(
    stream: MessageStream,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> str:
    """Format stream entries as plain text with Tier 2 heuristic sanitization."""

def export_stream_to_json_file(
    target_path: Path,
    stream: MessageStream,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> Path: ...

def export_stream_to_text_file(
    target_path: Path,
    stream: MessageStream,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> Path: ...
```

#### 3. `build_stream_entry` Mask Accounting

```python
def build_stream_entry(
    frame: RawFrame | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
    truncate_bytes: int = 262_144,
    seq: int,
    kind: str = "message",
    direction: str | None = None,
    payload_format: str | None = None,
    payload: str | None = None,
    byte_size: int | None = None,
    detail: str = "",
    ts_utc: str | None = None,
    on_mask_applied: Callable[[], None] | None = None,
) -> StreamEntry:
    """Construct a masked, display-truncated StreamEntry, invoking on_mask_applied if secrets are masked."""
```

### A-5 Two-Tier Masking Matrix

| Data Surface | Masking Tier | Implementation Mechanism | Justification |
| --- | --- | --- | --- |
| **Outbound message frames** | Tier 1 (Ingestion) | Exact replacement of `hidden_keys` values with `***` via `build_stream_entry` | Prevents secrets from appearing in the live UI stream while preserving payload format. |
| **Inbound message frames** | Tier 1 (Ingestion) | Exact replacement of `hidden_keys` values with `***` via `build_stream_entry` | Protects credentials echoed by servers; preserves exact structure without destructive heuristic regex mangling. |
| **Lifecycle events & Handshakes** | Tier 1 (Ingestion) | Exact replacement in event strings; query param secret masking in URLs | Prevents tokens in headers/URLs from entering the UI stream. |
| **Clipboard copy (Detail Pane)** | Tier 2 (Egress) | `sanitize_text(text, env_vars, hidden_keys)` | Eliminates hidden variables and heuristic token patterns before data enters OS clipboard. |
| **JSON & Text File Exports** | Tier 2 (Egress) | `sanitize_text` applied to all exported strings/payloads/metadata | Prevents credential leaks in exported files shared with external parties. |
| **MCP Transcripts & Probes** | Tier 2 (Egress) | `McpResponseSanitizer.sanitize_text` | Prevents LLMs/agents from observing hidden credentials. |
| **Application Logs** | Redacted | Strictly omit payloads, header values, and raw query strings; log `url_masked` | Invariant: logs must never contain user payloads or secrets. |
| **Metric Labels** | Low-cardinality | Labels restricted to `surface="websocket"`, `kind`, `direction` | Invariant: no URLs, headers, or payloads in metric labels. |

---

## Q&A

**Q: Why are handshake parameters resolved at connect time while message payloads resolve per send?**
**A:** The WebSocket handshake is an atomic HTTP upgrade exchange occurring once when the connection is established. Handshake parameters must be frozen at connect time so the stream log faithfully represents what was transmitted across the wire during that session. Message payloads, on the other hand, are discrete transmissions sent throughout an active session; resolving them per send allows developers to use environment variables captured dynamically from server responses earlier in the session.

**Q: How do we prevent template injection attacks on received server frames?**
**A:** Received server payloads are never passed to `TemplateService` or any template engine. `WebSocketPresenter._on_frame_received` passes incoming frames directly to `build_stream_entry`, which performs exact substring replacement for known hidden environment variables only. Server strings containing `{{ ... }}` remain inert literal text.

**Q: Why do we use two distinct masking tiers rather than applying heuristic sanitization everywhere?**
**A:** Heuristic sanitization (`sanitize_text`) uses broad regular expressions to catch sensitive patterns like API keys, bearer tokens, and JWTs. In a live stream inspection view during protocol debugging, heuristic regexes could inadvertently alter valid hexadecimal streams, binary representations, or test hashes. Exact replacement (Tier 1) masks known secret variables without corrupting arbitrary server responses. For egress points (Tier 2: clipboard, file export, MCP transcripts), heuristic sanitization is applied as a necessary defense-in-depth barrier.

**Q: Where does secret masking occur in the architecture?**
**A:** Secret masking is performed by `WebSocketPresenter` via `build_stream_entry` before entries are added to `MessageStream`. `StreamListModel.append_batch` remains the sole writer to `MessageStream`. As a result, no unmasked secret ever resides in `MessageStream`.

**Q: How are variable hover tooltips updated when switching environments?**
**A:** When the user switches environments in `EnvPresenter`, `TabsPresenter` receives `on_env_variables_changed` and `on_env_hidden_keys_changed`, forwarding the new snapshots to `WebSocketPresenter.set_variables()` and `set_hidden_keys()`. The presenter propagates these snapshots to `WebSocketConnectionEditor`, `WebSocketComposer`, and `WebSocketPresetsPanel`, ensuring all variable-aware inputs immediately display updated hover tooltips without requiring tab reloads.
