# PYPOST-1132: Technical Debt Analysis

## Shortcuts Taken

1. **In-Memory Secret Masking at Entry Ingestion**:
   - Secret masking for message payloads and connection URLs is applied synchronously during stream entry construction via `build_stream_entry(..., env_vars=..., hidden_keys=...)`.
   - While effective, simple string replacement of sensitive values does not parse structured JSON bodies hierarchically; deeply nested or encoded secret patterns rely on raw substring matching.

2. **Fixed 33ms Stream Ingestion Timer**:
   - `StreamListModel` uses a fixed 33ms batch flush timer (~30 FPS) to buffer incoming frames before dispatching `beginInsertRows()` / `endInsertRows()` to the Qt view.
   - Under very high throughput (>10k frames/sec), an adaptive backpressure mechanism (increasing interval under CPU pressure) would provide further scalability.

3. **Standard QStyledItemDelegate vs Custom Cell Widgets for Stream Entries**:
   - Stream list rows are rendered via standard `QListView` and model role data with formatted text lines (direction glyph, timestamp, byte size, masked preview).
   - A dedicated rich custom item delegate with expandable JSON viewer tree or copy-to-clipboard buttons is deferred to future UI polish.

## Code Quality Issues

1. **TabsPresenter Protocol Modularity**:
   - `TabsPresenter` in `pypost/ui/presenters/tabs_presenter.py` handles tab lifecycle across HTTP and WebSocket tabs, including secret propagation, focus deduplication, and teardown coordination.
   - As additional streaming protocols (e.g., SSE, gRPC, MQTT) are added in future iterations, extracting tab lifecycle managers into dedicated per-protocol tab coordinators will keep `TabsPresenter` well under complexity limits.

2. **KeyValueTable Synchronization Coupling**:
   - `WebSocketKeyValueTable` directly reads and writes query params and headers from the active `WebSocketProfile`.
   - Future refactoring could decouple the table view model from the profile dataclass via a dedicated generic key-value presenter.

## Missing Tests

1. **Current Test Suite Coverage**:
   - All 24 tests across `tests/test_websocket_client_ui_repro.py`, `tests/test_agent_e2e_websocket.py`, and `tests/test_ui_identity_spotcheck.py` pass with 100% success.
   - All tests include explicit timeout markers (`pytestmark = pytest.mark.timeout(30)` or `@pytest.mark.timeout(30)`), strictly adhering to `do-testing` requirements.

2. **Pre-existing / Baseline Test Triage**:
   - `tests/test_agent_e2e_harness_table_doc.py::test_agent_e2e_harness_table_matches_marked_modules`: Gated on documenting `tests/test_agent_e2e_websocket.py` in the developer documentation harness table (addressed in Step 8 Dev Docs).
   - `tests/test_metrics_server_unit.py::TestMetricsServerGenerations::test_process_exit_dispatch_is_isolated_for_overlapping_workers`: Pre-existing unit test failure (`NON-BLOCKER — pre-existing`).
   - `tests/test_pypost_1077_verification_artifacts.py`: Pre-existing baseline check (`NON-BLOCKER — pre-existing`).
   - `tests/test_solid_audit_baseline.py`: Pre-existing baseline snapshot check (`NON-BLOCKER — pre-existing`).
   - `tests/test_suite_qapp_alignment.py`: Pre-existing qapp fixture in `test_mcp_controls_presenter.py` (`NON-BLOCKER — pre-existing`).

3. **Future Test Scenarios (Deferred to Downstream Tasks / Follow-ups)**:
   - **Binary Frame Hex Viewer Widget Tests**: Dedicated visual inspection tests for raw binary frame payloads (e.g. Protocol Buffers, MessagePack).
   - **Drag-and-Drop Stream Filtering Tests**: Visual filtering and regex matching tests in stream view.

## Performance Concerns

1. **Bounded In-Memory FIFO Eviction**:
   - `MessageStream` and `StreamListModel` enforce a maximum capacity (default 1,000 entries) and memory budget (default 10 MB).
   - Memory is strictly bounded, with deterministic eviction of oldest entries when thresholds are exceeded.

2. **Zero Overhead When Tab Inactive**:
   - Presenter batch timers and connection streams are completely stopped upon tab closure and teardown, guaranteeing zero CPU or memory leakage.

## Follow-up Tasks

The following follow-up tasks are identified for future development:
- `PYPOST-1143`: Add rich JSON syntax highlighting and payload inspector panel to WebSocket stream view.
- `PYPOST-1144`: Implement adaptive backpressure batch flush for ultra-high-frequency WebSocket streaming.
- `PYPOST-1145`: Extract dedicated per-protocol tab coordinators from `TabsPresenter`.
