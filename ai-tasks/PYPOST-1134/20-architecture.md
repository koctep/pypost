# PYPOST-1134: WS-6 Composer, saved presets and sequence runner

## Research

### R-1 Existing Baseline and Module Inventory

Research into current repository components establishing the baseline for WS-6:

1. **Persisted Domain Models (`pypost/models/websocket.py`):**
   - WS-2 established `WsMessageFormat` (`TEXT`, `JSON`, `HEX`, `BASE64`), `WebSocketMessagePreset` (`id`, `name`, `format`, `payload`), `WebSocketSequenceStep` (`preset_id`, `inline_payload`, `format`, `delay_ms`), `WebSocketSequence` (`id`, `name`, `steps`), and `WebSocketConnection` containing `presets: List[WebSocketMessagePreset]`, `sequences: List[WebSocketSequence]`, and `default_format: WsMessageFormat`.
   - `Collection` holds `websockets: List[WebSocketConnection]`, persisting automatically via Pydantic v2 JSON serialization.
2. **Codec and Payload Validation (`pypost/core/websocket_codec.py`):**
   - `validate_format(data, format)` validates `TEXT`, `JSON`, `HEX`, and `BASE64` payloads, returning `(is_valid: bool, error_msg: Optional[str])`.
   - `encode_payload(data, format)` converts text input into `str` or binary `bytes` (hex decoding or base64 decoding).
   - `decode_payload(payload, format)` renders raw incoming/outgoing bytes into display strings.
3. **Session Controller & State Machine (`pypost/core/qt/websocket_session.py`, `pypost/core/websocket_session_policy.py`):**
   - `WebSocketSessionController` provides `send_text(text: str)` and `send_binary(payload: bytes)`.
   - `SessionState` exposes `IDLE`, `CONNECTING`, `OPEN`, `CLOSING`, `RECONNECTING`, `FAILED`.
   - Outbound transmissions and sequence runs are allowed **only** when `state == SessionState.OPEN`.
4. **WebSocket Presenter (`pypost/ui/presenters/websocket_presenter.py`):**
   - Coordinates tab state, secret masking via `build_stream_entry`, and 33 ms batched stream ingestion.
   - Currently provides single-format composer handling (`handle_send_message`) with basic text input. Needs extension to coordinate multi-format composer dispatch, preset actions, and sequence runner execution.
5. **CodeEditor and Syntax Validation (`pypost/ui/widgets/code_editor.py`):**
   - `CodeEditor` inherits `VariableAwarePlainTextEdit`, supporting `BodyFormat` folding, line numbers, variable hovering, and syntax validation controllers.
6. **Module Cap Constraints (`scripts/audit_baseline_metrics.py`):**
   - New core logic (sequence planning, step resolution, format evaluation) must reside in a new pure Qt-free module `pypost/core/websocket_sequence.py`.
   - Asynchronous timer-paced sequence orchestration must reside in `pypost/core/qt/websocket_sequence_runner.py`.
   - The presets and sequences management UI belongs in `pypost/ui/widgets/websocket/presets_panel.py` and `pypost/ui/widgets/websocket/composer.py`, keeping `websocket_tab.py` and `connection_editor.py` modular and well under LOC thresholds.

### R-2 Benchmark and Behavioral Analysis

Comparing real-time protocol development workflows with Postman, Insomnia, and PyPost requirements:

- **Multi-Format Input:** Sending binary frames (Hex or Base64) requires converting human-readable hexadecimal or base64 strings into raw binary frames before dispatch. Per-format validation before transmission protects active sessions from protocol errors and immediate server disconnects.
- **Preset Management:** Presets store template strings (unresolved variables such as `{{API_KEY}}`). Loading a preset into the composer allows modification; `Send now` transmits the preset directly in one action without mutating the composer's current buffer.
- **Sequence Runner Timing:** Multi-step protocols (e.g. Handshake -> Subscribe -> Query) require millisecond-level pre-step pacing delays. Execution must use non-blocking Qt timers (`QTimer`) so the UI remains fully interactive and responsive (able to display incoming frames, process UI clicks, and handle user cancellation).
- **Execution Safety:** If a step references a deleted preset, execution must be blocked upfront with a clear named explanation. If a step fails mid-run or the connection is dropped, execution halts immediately and logs the failing step index and cause.

---

## Implementation Plan

### P-1 Delivery Phases

1. **Phase 1: Pure Sequence Planning & Step Validation Engine (`pypost/core/websocket_sequence.py`)**
   - Implement `SequenceExecutionPlan`, `StepExecutionPlan`, `StepExecutionResult`, and `SequenceRunOutcome`.
   - Implement plan compiler `build_sequence_plan(sequence, presets)` that resolves preset references, verifies integrity, detects missing presets, and pre-validates inline and preset payloads.
   - Pure Python / Qt-free, unit-tested headlessly.
2. **Phase 2: Qt Asynchronous Sequence Runner (`pypost/core/qt/websocket_sequence_runner.py`)**
   - Implement `WebSocketSequenceRunner(QObject)` with `QTimer` pacing.
   - Implement runner state machine (`IDLE`, `RUNNING`, `PAUSED`, `STOPPED`, `COMPLETED`, `FAILED`).
   - Implement step execution loop: pacing delay -> payload validation & encoding -> dispatch via `WebSocketSessionController` -> step outcome emission -> next step scheduling.
   - Implement safe mid-run cancellation (`stop()`) and step error halting.
3. **Phase 3: Multi-Format Composer Widget (`pypost/ui/widgets/websocket/composer.py`)**
   - Implement composer layout with `CodeEditor`, `Format:` combo (`Text`, `JSON`, `Hex`, `Base64`), `Preset:` combo + `Save...`, and `Sequence:` combo + `Run`/`Stop`.
   - Real-time syntax validation indicator and format switching.
   - Integrate keyboard shortcuts (`Ctrl+Enter` / `F5` for send).
4. **Phase 4: Messages Sub-Tab (`Messages` tab in `pypost_ws_detail_tabs`) (`pypost/ui/widgets/websocket/presets_panel.py`)**
   - Saved Messages (Presets) master list and detail pane: `New`, `Duplicate`, `Delete`, `Load into composer`, `Send now`, `Save`.
   - Sequences master list and detail pane: `New sequence`, `Duplicate`, `Delete`, step table with `Add step`, `Remove`, `Up`, `Down`, `Run`, `Stop`.
   - Step configuration for Preset references vs Inline payloads with pre-step delay (`delay_ms`).
   - Informative empty states for both presets and sequences.
5. **Phase 5: Presenter Coordination & Integration (`WebSocketPresenter`, `WebSocketTab`)**
   - Integrate composer and `Messages` sub-tab into `WebSocketTab`.
   - Wire presenter actions: `handle_send_message`, `handle_save_preset`, `handle_load_preset`, `handle_send_preset_now`, `handle_run_sequence`, `handle_stop_sequence`.
   - Enforce disconnected session guards (refuse send/run if not `Open`).
   - Wire sequence runner signals to stream logging and status notifications.
6. **Phase 6: Widget Identities & Automated Test Suites**
   - Register all `WS_*` widget IDs in `pypost/ui/widget_ids.py` and extend `tests/test_ui_identity_spotcheck.py`.
   - Implement comprehensive unit tests, runner tests, and GUI integration tests.

### Mandatory — Failing Repro (next Step 3)

- **Test Suite Location:** `tests/test_websocket_composer.py` and `tests/test_websocket_sequence.py`.
- **Desired Behavior Assertions:**
  1. **Multi-Format Send & Validation:** Assert that composing valid JSON, Hex, and Base64 transmits correctly encoded frames; assert that malformed JSON (syntax error), odd-length hex (`"123"`), and invalid Base64 (`"$$$"` ) are rejected with inline validation errors before send.
  2. **Preset Round-Trip & Dispatch:** Assert creating a preset persists to `connection.presets`, `Load into composer` populates the editor, and `Send now` transmits over an open session without altering the composer editor content.
  3. **Sequence Step Execution & Delays:** Assert running a 3-step sequence executes steps in strict chronological order with the configured `delay_ms` pacing, emitting frames to the session controller.
  4. **Mid-Run Cancellation:** Assert calling `stop()` during a pacing delay halts before the next step and leaves the session in `Open` state.
  5. **Missing Preset Safety Guard:** Assert that a sequence referencing a deleted `preset_id` is flagged as `<missing preset>` and attempting to run it is blocked with a descriptive error.
  6. **Connection Guard:** Assert that attempting to send or run while session is `Idle` or `Connecting` is refused with a clear message.
- **Forcing the Failure:** Running these tests against the current codebase will fail because `websocket_sequence.py`, `websocket_sequence_runner.py`, `composer.py`, and `presets_panel.py` do not yet exist or lack multi-format and sequence runner capabilities.
- **Sequencing:** Step 2 (architecture approved) -> Step 3 (automated red tests committed) -> Step 4 (implementation until all tests green).

---

## Architecture

### A-0 Decision Register

- **D-1: Pure vs Qt Layer Separation:** Sequence plan compilation, step resolution, and static format validation are implemented in Qt-free `pypost/core/websocket_sequence.py`. Timer-paced asynchronous execution and UI signals are implemented in `pypost/core/qt/websocket_sequence_runner.py`.
- **D-2: Atomic Upfront Validation vs Runtime Step Validation:** A sequence undergoes full pre-flight validation when `Run` is requested. If any step references a missing preset or has an invalid inline payload format, execution is blocked before any frame is sent. Runtime validation is also re-checked at dispatch time.
- **D-3: Non-Blocking Step Pacing:** Delays between steps are managed exclusively using `QTimer.singleShot` or an asynchronous timer loop on the Qt event loop, preventing UI thread blocking.
- **D-4: Disconnected Dispatch Policy:** Transmitting messages or running sequences when the session is not `Open` is immediately refused with user feedback; messages are never silently queued while offline.
- **D-5: Presets & Sequences Persistence:** Presets and sequences are stored in `WebSocketConnection.presets` and `WebSocketConnection.sequences`. Any edit or creation in the UI triggers `WebSocketRegistry.save_websocket(conn, collection_id)` to ensure persistence.
- **D-6: Stream Visibility:** Every message dispatched by a preset (`Send now`) or sequence step appears as a regular outbound `StreamEntry` in the chronological stream view, with its respective format and size.

### A-1 Component Architecture & Layering

```text
+--------------------------------------------------------------------------------+
| UI Layer (PySide6 / Widgets)                                                  |
|                                                                                |
|  +--------------------------------------------------------------------------+  |
|  | WebSocketTab                                                             |  |
|  |   +- Header (Connect / Disconnect, WebSocketStateBadge)                  |  |
|  |   +- pypost_ws_detail_tabs:                                              |  |
|  |   |    [Params] [Headers] [Subprotocols] [Messages]                      |  |
|  |   |                                          |                           |  |
|  |   |                     +--------------------+---------------------+     |  |
|  |   |                     | WebSocketPresetsPanel (pypost_ws_messages_tab) |  |
|  |   |                     |  - Presets Master/Detail                       |  |
|  |   |                     |  - Sequences Master/Detail & Steps Table       |  |
|  |   |                     +------------------------------------------+     |  |
|  |   +- WebSocketStreamView (Chronological frame inspector)                 |  |
|  |   +- WebSocketComposer (Multi-format CodeEditor + Quick Combos)          |  |
|  +---+----------------------------------------------------------------------+--+
|      | User actions (Send, Save preset, Run sequence, Stop, Load preset)
|      v
|  +--------------------------------------------------------------------------+
|  | WebSocketPresenter                                                       |
|  |   - Enforces SessionState.OPEN check for sends and sequence runs         |
|  |   - Resolves template variables per send / per step                      |
|  |   - Initiates WebSocketRegistry.save_websocket on preset/seq changes     |
|  |   - Coordinates with WebSocketSequenceRunner                             |
|  +---+--------------------------------------+-------------------------------+
+------|--------------------------------------|----------------------------------+
       | Outbound payload                     | Run plan / cancel
       v                                      v
+--------------------------------------+ +--------------------------------------+
| Core Qt Layer (core/qt/)             | | Core Qt Layer (core/qt/)             |
|                                      | |                                      |
| WebSocketSessionController           | | WebSocketSequenceRunner (QObject)    |
|   - send_text(str)                   | |   - Pacing via QTimer                |
|   - send_binary(bytes)               | |   - State machine                    |
|   - emits frame_sent -> Stream       | |   - Dispatches steps to Controller   |
+--------------------------------------+ +---+----------------------------------+
                                             | Evaluates plan & validates
                                             v
                                         +--------------------------------------+
                                         | Pure Core Layer (core/ - Qt Free)    |
                                         |                                      |
                                         | websocket_sequence.py                |
                                         |   - build_sequence_plan()            |
                                         |   - SequenceExecutionPlan            |
                                         |   - StepExecutionPlan                |
                                         |   - StepExecutionResult              |
                                         | websocket_codec.py                   |
                                         |   - validate_format()                |
                                         |   - encode_payload()                 |
                                         +--------------------------------------+
```

### A-2 Data Models & Planning Structures

#### 1. Persisted Domain Models (`pypost/models/websocket.py`)

Already defined and persisted in collection JSON:
```python
class WsMessageFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HEX = "hex"
    BASE64 = "base64"

class WebSocketMessagePreset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Message"
    format: WsMessageFormat = WsMessageFormat.JSON
    payload: str = ""

class WebSocketSequenceStep(BaseModel):
    preset_id: Optional[str] = None
    inline_payload: str = ""
    format: WsMessageFormat = WsMessageFormat.JSON
    delay_ms: int = Field(default=0, ge=0, le=600_000)

class WebSocketSequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Sequence"
    steps: List[WebSocketSequenceStep] = Field(default_factory=list)
```

#### 2. Pure Planning & Execution Models (`pypost/core/websocket_sequence.py`)

```python
@dataclass(frozen=True)
class StepExecutionPlan:
    step_index: int               # 0-based index
    display_name: str             # Preset name or "<inline>"
    format: WsMessageFormat       # Payload format
    raw_payload: str              # Template payload text
    delay_ms: int                 # Pacing delay waited BEFORE dispatch
    preset_id: Optional[str] = None

@dataclass(frozen=True)
class SequenceExecutionPlan:
    sequence_id: str
    sequence_name: str
    steps: tuple[StepExecutionPlan, ...]
    is_valid: bool
    validation_error: Optional[str] = None

@dataclass(frozen=True)
class StepExecutionResult:
    step_index: int
    display_name: str
    format: WsMessageFormat
    encoded_bytes_or_str: bytes | str
    byte_size: int
    delay_ms: int
    success: bool
    error_message: Optional[str] = None

@dataclass(frozen=True)
class SequenceRunOutcome:
    sequence_id: str
    sequence_name: str
    total_steps: int
    executed_steps: int
    status: str                   # "completed", "stopped", "failed"
    failure_step_index: Optional[int] = None
    failure_reason: Optional[str] = None
```

#### 3. Plan Compiler Function

```python
def compile_sequence_plan(
    sequence: WebSocketSequence,
    presets: Sequence[WebSocketMessagePreset],
) -> SequenceExecutionPlan:
    """Compile a sequence definition and its preset library into an executable plan.
    
    Verifies that all referenced presets exist and that inline and preset payloads
    are syntactically valid for their declared formats.
    """
```

### A-3 Sequence State Machine & Execution Flow

```text
                  +----------------------------------------------+
                  |                                              |
                  v                    run()                     |
            +------------+  ------------------------->  +-----------------+
  start --> |    IDLE    |                              |     RUNNING     |
            +------------+                              +-----------------+
                  ^                                       |   |   |   |
                  |                                       |   |   |   |
                  |         all steps complete            |   |   |   |
                  +---------------------------------------+   |   |   |
                  |                                           |   |   |
                  |              user stop()                  |   |   |
                  +-------------------------------------------+   |   |
                  |                                               |   |
                  |       step failure / format error             |   |
                  +-----------------------------------------------+   |
                  |                                                   |
                  |        socket disconnected mid-sequence           |
                  +---------------------------------------------------+
```

#### Detailed State Lifecycle

1. **`IDLE`**: Runner is inactive. Ready to accept `run_sequence()`.
2. **`RUNNING`**: Execution in progress. For each step `i = 0 ... N-1`:
   - State remains `RUNNING`.
   - Pacing Timer schedules `delay_ms` milliseconds via `QTimer`.
   - During delay, UI remains interactive. If user triggers `stop()`, pending timer is cancelled, runner transitions to `STOPPED`, then `IDLE`, and emits `sequence_finished(outcome="stopped")`.
   - When timer expires, runner verifies connection is still `SessionState.OPEN`. If disconnected, transitions to `FAILED` with reason `"Session disconnected during sequence execution"`.
   - Runner resolves template placeholders (using `TemplateService` / env vars).
   - Runner validates and encodes payload via `websocket_codec.encode_payload`. If format error occurs, transitions to `FAILED` with reason `"Step {i+1} format error: {err}"`.
   - Runner calls `session_controller.send_text(...)` or `send_binary(...)`.
   - Step outcome recorded, `step_completed` signal emitted.
   - Proceeds to step `i+1`.
3. **`COMPLETED`**: All `N` steps completed successfully. Emits `sequence_finished(outcome="completed")`. Returns to `IDLE`.
4. **`STOPPED`**: User pressed `Stop`. Pending timer cancelled. Emits `sequence_finished(outcome="stopped")`. Socket remains open. Returns to `IDLE`.
5. **`FAILED`**: Execution halted due to error. Emits `sequence_finished(outcome="failed", failure_reason=...)`. Socket remains open. Returns to `IDLE`.

### A-4 Wireframes & Messages Sub-Tab Interaction

#### 1. Messages Sub-Tab Layout (`pypost_ws_messages_tab` in `pypost_ws_detail_tabs`)

```text
+- pypost_ws_detail_tabs > Messages -----------------------------------------------+
| Saved Messages (Presets)                           Preset Detail                 |
| +- pypost_ws_presets_list ------+ +---------------------------------------------+|
| | subscribe              json   | | Name   [ subscribe                        ] ||
| | ping                   text   | | Format [ JSON v ]  (pypost_ws_preset_*)     ||
| | auth                   json   | | Payload (CodeEditor)                        ||
| | binary-query           hex    | | {"op":"subscribe","channel":"{{channel}}"}  ||
| +-------------------------------+ +---------------------------------------------+|
| [New] [Duplicate] [Delete]          [Load into composer] [Send now] [Save]       |
+----------------------------------------------------------------------------------+
| Sequences                                          Steps of "login+sub"          |
| +- pypost_ws_sequences_list ----+ +---------------------------------------------+|
| | login+sub          3 steps    | | # | Message         | Format | Delay before ||
| | ping-heartbeat     1 step     | | 1 | auth (preset)   | json   |        0 ms  ||
| |                               | | 2 | subscribe       | json   |      250 ms  ||
| |                               | | 3 | <inline>        | text   |    1 000 ms  ||
| +-------------------------------+ +---------------------------------------------+|
| [New sequence] [Duplicate] [Del]     [Add step] [Remove] [Up] [Down] [Run] [Stop] |
+----------------------------------------------------------------------------------+
```

#### 2. Composer Strip Quick Controls (`pypost_ws_composer_*`)

```text
+- Composer - pypost_ws_composer_edit --------------------------------------------+
| Format:[JSON v]  Preset:[subscribe v][Save...]  Sequence:[login+sub v][Run][Stop]|
| +-----------------------------------------------------------------------------+ |
| | {"op":"subscribe","channel":"{{channel}}"}                                  | |
| +-----------------------------------------------------------------------------+ |
| [Validation: Valid JSON]                         [ Send Message (Ctrl+Enter) ]  |
+---------------------------------------------------------------------------------+
```

#### 3. Empty States Guidance

- **Empty Presets State:** When `len(conn.presets) == 0`:
  `"No saved messages yet. Compose one and choose Save... in the composer, or [New]."`
- **Empty Sequences State:** When `len(conn.sequences) == 0`:
  `"No sequences yet. [New sequence] builds one from saved messages or inline payloads."`

### A-5 Validation, Error Handling & Safety Guards

1. **Per-Format Pre-Send Validation:**
   - `Text`: Accepts any valid UTF-8 string.
   - `JSON`: Validated via `json.loads(text)`. Syntax errors show line/col information.
   - `Hexadecimal`: Validated via `bytes.fromhex(text.strip())`. Enforces valid hex characters and even length.
   - `Base64`: Validated via `base64.b64decode(text.strip(), validate=True)`. Enforces valid characters and padding.
   - If invalid, transmission is blocked, and validation label highlights the error message.
2. **Missing Preset Safety Guard:**
   - If a sequence step references a preset whose ID does not exist in `conn.presets`:
     - Step message column displays `<missing preset: id>`.
     - `compile_sequence_plan` sets `is_valid=False` with error `"Step {i+1} references missing preset '{preset_id}'"`.
     - Clicking `Run` displays an error dialog/banner and refuses execution. No network frames are sent.
3. **Disconnected Session Guard:**
   - If `presenter.state != SessionState.OPEN`:
     - `Send Message` in composer is disabled or displays notice `"Cannot send message: WebSocket session is not connected."`.
     - `Send now` on a preset displays notice `"Cannot send preset: WebSocket session is not connected."`.
     - `Run` on a sequence displays notice `"Cannot run sequence: WebSocket session is not connected."`.
     - Outbound frames are never buffered or silently queued.
4. **Non-Destructive Stop:**
   - Halting a sequence via `Stop` cancels future step timers, records the stopped step index, and leaves the active WebSocket connection open and responsive.

### A-6 UI Automation Identities & Spot-Check Integration

The following widget IDs are declared in `pypost/ui/widget_ids.py` and asserted on live tabs in `tests/test_ui_identity_spotcheck.py`:

| Identity Constant | `objectName` / `accessibleIdentifier` | Role & Description |
| ----------------- | ------------------------------------- | ------------------ |
| `WS_COMPOSER_FORMAT_COMBO` | `pypost_ws_composer_format_combo` | Composer format selector (`Text`, `JSON`, `Hex`, `Base64`) |
| `WS_PRESET_COMBO` | `pypost_ws_preset_combo` | Quick preset selector in composer strip |
| `WS_PRESET_SAVE_BUTTON` | `pypost_ws_preset_save_button` | `Save...` button in composer strip |
| `WS_SEQUENCE_COMBO` | `pypost_ws_sequence_combo` | Quick sequence selector in composer strip |
| `WS_SEQUENCE_RUN_BUTTON` | `pypost_ws_sequence_run_button` | `Run` button for active sequence |
| `WS_SEQUENCE_STOP_BUTTON` | `pypost_ws_sequence_stop_button` | `Stop` button for active sequence |
| `WS_MESSAGES_TAB` | `pypost_ws_messages_tab` | `Messages` sub-tab inside `WS_DETAIL_TABS` |
| `WS_PRESETS_LIST` | `pypost_ws_presets_list` | Saved messages master list |
| `WS_PRESET_NAME_INPUT` | `pypost_ws_preset_name_input` | Preset name line edit |
| `WS_PRESET_FORMAT_COMBO` | `pypost_ws_preset_format_combo` | Preset format combo |
| `WS_PRESET_PAYLOAD_EDIT` | `pypost_ws_preset_payload_edit` | Preset payload CodeEditor |
| `WS_PRESET_NEW_BUTTON` | `pypost_ws_preset_new_button` | `[New]` preset button |
| `WS_PRESET_DUPLICATE_BUTTON` | `pypost_ws_preset_duplicate_button` | `[Duplicate]` preset button |
| `WS_PRESET_DELETE_BUTTON` | `pypost_ws_preset_delete_button` | `[Delete]` preset button |
| `WS_PRESET_LOAD_BUTTON` | `pypost_ws_preset_load_button` | `[Load into composer]` button |
| `WS_PRESET_SEND_BUTTON` | `pypost_ws_preset_send_button` | `[Send now]` preset button |
| `WS_SEQUENCES_LIST` | `pypost_ws_sequences_list` | Sequences master list |
| `WS_SEQUENCE_NEW_BUTTON` | `pypost_ws_sequence_new_button` | `[New sequence]` button |
| `WS_SEQUENCE_DUPLICATE_BUTTON` | `pypost_ws_sequence_duplicate_button` | `[Duplicate]` sequence button |
| `WS_SEQUENCE_DELETE_BUTTON` | `pypost_ws_sequence_delete_button` | `[Delete]` sequence button |
| `WS_SEQUENCE_STEPS_TABLE` | `pypost_ws_sequence_steps_table` | Sequence steps QTableWidget |
| `WS_SEQUENCE_STEP_ADD_BUTTON` | `pypost_ws_sequence_step_add_button` | `[Add step]` button |
| `WS_SEQUENCE_STEP_REMOVE_BUTTON` | `pypost_ws_sequence_step_remove_button` | `[Remove step]` button |
| `WS_SEQUENCE_STEP_UP_BUTTON` | `pypost_ws_sequence_step_up_button` | `[Move Up]` step button |
| `WS_SEQUENCE_STEP_DOWN_BUTTON` | `pypost_ws_sequence_step_down_button` | `[Move Down]` step button |

### A-7 Module Cap & Line-of-Code Governance

To strictly respect project SOLID metrics and file size limits:
- `pypost/core/websocket_sequence.py`: pure plan compilation and validation engine (~150 LOC).
- `pypost/core/qt/websocket_sequence_runner.py`: timer-based sequence execution runner (~200 LOC).
- `pypost/ui/widgets/websocket/composer.py`: standalone multi-format composer widget (~180 LOC).
- `pypost/ui/widgets/websocket/presets_panel.py`: standalone Messages sub-tab widget hosting presets and sequences master/detail (~350 LOC).
- `pypost/ui/widgets/websocket/websocket_tab.py`: imports `WebSocketComposer` and embeds `WebSocketPresetsPanel` in `WS_DETAIL_TABS` (~150 LOC).
- `pypost/ui/presenters/websocket_presenter.py`: coordinates preset actions, sequence runs, and validation checks (~350 LOC).

All new modules will be tracked in `scripts/audit_baseline_metrics.py`.

---

## Q&A

| Question | Answer |
| -------- | ------ |
| Why is sequence planning separate from sequence execution? | Separating planning (`websocket_sequence.py`) from execution (`websocket_sequence_runner.py`) allows step compilation, integrity verification, and format validation to be thoroughly unit-tested headlessly without Qt or QTimer dependencies. |
| How are binary payloads (Hex and Base64) transmitted over the WebSocket transport? | Hexadecimal strings (e.g. `48 65 6c 6c 6f`) and Base64 strings (e.g. `SGVsbG8=`) are decoded into raw binary `bytes` via `websocket_codec.encode_payload` and transmitted using `session_controller.send_binary(bytes)`. In the stream view, they are rendered with their wire size and format indicator. |
| What happens if a sequence step specifies `delay_ms = 0`? | The runner executes the step immediately (or on the next event loop turn via `QTimer.singleShot(0)`), ensuring deterministic execution without artificial latency while maintaining event loop responsiveness. |
| How does `Save...` in the composer work? | Clicking `Save...` prompts the user for a preset name (via `QInputDialog` or an inline name popover), creates a new `WebSocketMessagePreset` using the composer's current format and payload, appends it to `conn.presets`, persists it via `WebSocketRegistry.save_websocket`, and selects it in the preset combo. |
| What happens when the user clicks `Stop` while a sequence is running? | The active pacing `QTimer` is stopped immediately. The runner records that the sequence was stopped, emits `sequence_finished(outcome="stopped")`, and returns to `IDLE`. The WebSocket session remains in the `OPEN` state, allowing the user to inspect the stream or continue manual interactions. |
| How are missing presets handled? | If a sequence step references a preset ID that has been deleted from `conn.presets`, the step is rendered with `<missing preset: id>` and highlighted in red. `compile_sequence_plan` flags the plan as invalid. When the user attempts to run the sequence, an error notification explains that the referenced preset is missing, and execution is aborted before any step is sent. |
| How are environment variables resolved during sequence execution? | Payloads store template strings (e.g. `{"token": "{{API_KEY}}"}`). The runner resolves template variables dynamically at dispatch time using `TemplateService` and active environment variables, ensuring sequences work seamlessly across different environments. |
