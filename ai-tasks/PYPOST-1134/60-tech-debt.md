# PYPOST-1134: Technical Debt Analysis

## Shortcuts Taken

1. **Synchronous Name Prompt in Preset Quick-Save**:
   - `WebSocketComposer._on_save_preset_clicked` uses `QInputDialog.getText` to synchronously prompt the user for a preset name. While standard for PySide6 desktop applications, headless or non-interactive UI automation tests must mock `QInputDialog.getText` when exercising this specific button click.
2. **Resilient Template Rendering Exception Fallback**:
   - In `WebSocketSequenceRunner._execute_current_step`, variable placeholder resolution catches broad exceptions from `TemplateService.render_string` and falls back silently to the raw template payload string. While this prevents sequence aborts caused by benign formatting in non-templated text, it does not surface a user-facing warning if an environment variable substitution fails due to a syntax typo.
3. **Default Step Insertion Values**:
   - When adding a new sequence step via `WebSocketPresetsPanel._on_step_add_clicked`, a hardcoded default step payload (`"New Step Payload"`, `TEXT`, `100 ms`) is appended directly to the table without an intermediate configuration dialog. Users must adjust the row parameters post-creation.

## Code Quality Issues

1. **Monolithic Presets & Sequences Widget**:
   - `WebSocketPresetsPanel` (~830 lines) manages both Saved Messages (Presets) CRUD and Sequence Step CRUD / Reordering in a single widget class. While it complies with architectural line limits and is logically segmented into helper sections, extracting subcomponents (`WebSocketPresetsMasterDetail` and `WebSocketSequencesMasterDetail`) into dedicated widget modules would improve cohesion and test isolation.
2. **Dual Presenter Property Accessors**:
   - `WebSocketPresenter` exposes duplicate properties (`state` / `_state` and `session_controller` / `_controller`) to preserve backwards compatibility across legacy WS-4/WS-5 presenter unit tests and newer WS-6 tests. These should be unified and deprecated aliases removed in a future cleanup cycle.
3. **Step Table UI In-Place Editing vs Cell Editors**:
   - In `WebSocketPresetsPanel`, step attributes are currently modified via programmatic helpers (`add_sequence_step`, `move_sequence_step_up`, `move_sequence_step_down`, `remove_sequence_step`) and re-rendered into `QTableWidget` items rather than custom in-cell combo/spinbox delegates. Adding custom item delegates would enhance UI ergonomics.

## Missing Tests

1. **Multi-Megabyte Payload Stress Testing**:
   - Tests currently validate standard payloads (up to tens of kilobytes). Automated stress tests exercising high-volume binary payloads (e.g. 5–10 MB Hex/Base64 frames) through the sequence runner under rapid timer intervals would ensure memory stability across long-running sessions.
2. **Live Preset Mutation During Sequence Execution**:
   - While `compile_sequence_plan` creates an immutable snapshot of presets and step definitions upfront, additional edge-case tests could verify behavior when a user concurrently modifies or deletes a preset in the UI while a sequence referencing that preset is actively executing.
3. **Zero-Delay High-Frequency Step Sequences**:
   - Current sequence runner tests verify paced execution (e.g. 50–100 ms delays) and immediate 0 ms single-shot dispatch. A dedicated test verifying a 50-step sequence with 0 ms delays executing in rapid succession would further validate event loop behavior under zero-latency conditions.

## Performance Concerns

1. **Real-Time Synchronous Validation on Keystroke**:
   - `WebSocketComposer` and `WebSocketPresetsPanel` revalidate payload syntax synchronously on every `textChanged` signal. For typical payloads (< 100 KB), JSON parsing and regex validation take < 0.1 ms. For very large payloads (multi-megabyte JSON or Hex strings), typing in the editor could cause minor UI frame drops. A 150 ms debounce timer for validation would eliminate potential typing lag for huge payloads.
2. **Template Service Instantiation**:
   - `WebSocketSequenceRunner` instantiates a `TemplateService()` instance per runner. While lightweight, sharing or caching template renderers across presenters would avoid redundant object allocations.

## Follow-up Tasks

1. **WS-7 (PYPOST-1135)**: Implement connect-time handshake secret resolution and deep egress heuristic masking.
2. **WS-8 (PYPOST-1136)**: Implement TLS certificate overrides, warning dialogs, and ephemeral trust exceptions.
3. **WS-9 (PYPOST-1137)**: Implement Model Context Protocol (MCP) bounded probe tool execution.
4. **Refactor Presets Panel Component**: Split `WebSocketPresetsPanel` into standalone `WebSocketPresetsSection` and `WebSocketSequencesSection` child widgets.
5. **Debounced Syntax Validation**: Introduce a debounced validation timer for `WebSocketComposer` payload editing on large payloads.
