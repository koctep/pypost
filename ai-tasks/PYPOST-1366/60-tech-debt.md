# PYPOST-1366: Technical Debt Analysis

## Shortcuts Taken

- **Duplication of Gutter Mouse & Painting Logic**: `FoldableCodeView` and `CodeEditor` still share
  duplicated line-number area mouse press/double-click dispatch and chevron painting routines.
  While PYPOST-1366 enhanced gutter double-clicking via `line_number_area_mouse_double_click`, this
  logic is maintained separately in `FoldableCodeView` rather than in an extracted shared base class
  or mixin. This shares architectural technical debt with PYPOST-1369.
- **Synchronous Fold Region Scan on Message Selection**: When an entry is selected in
  `StreamDetailPane`, `_render_payload()` synchronously triggers
  `self._editor.fold_controller().ensure_scanned()`. This ensures immediate fold availability for
  the user, but bypasses the debounced scan pipeline for newly displayed payloads.

## Code Quality Issues

- **Shared Double-Click Event Handling**: Double-click handling in `LineNumberArea` invokes
  `getattr(self._editor, "line_number_area_mouse_double_click", None)` using dynamic reflection.
  A formal interface or abstract base class (`FoldableEditorProtocol`) would provide stricter typing
  and clearer contracts across editors.
- **Payload Format Detection Heuristics**: Format auto-detection in `detect_body_format` relies on
  string-prefix matching and fallback parsing (`json.loads`, `yaml.safe_load`,
  `xml.etree.ElementTree.fromstring`). For noisy text or mixed payload formats, exploratory parsing
  attempts could introduce minor overhead.

## Missing Tests

- **High-Throughput Stream Ingestion with Large Frames (>1MB)**: Automated tests currently validate
  typical JSON/XML/YAML messages up to several kilobytes. Dedicated stress tests measuring UI
  framerate and latency during continuous message streaming with frames >1MB are missing.
- **Malformed XML/YAML Payloads Under Rapid Selection Changes**: Rapidly toggling between malformed
  or truncated XML/YAML stream entries while background debounced scan timers are running lacks
  dedicated fuzzing test scenarios.

## Performance Concerns

- **Main Thread AST Scanning on Large Payloads**: In `StreamDetailPane`, fold region scanning runs
  synchronously on `setPlainText()` upon entry selection. For very large stream frames (>1MB),
  parsing JSON/XML/YAML on the Qt main GUI thread could cause momentary dropped frames during heavy
  message stream inspection.

## Follow-up Tasks

### [Medium] Extract Common Foldable Editor Base Class and Gutter Controller
- **Description**: Consolidate common line-number area painting, chevron drawing, and mouse
  interaction handling (single/double-click) between `FoldableCodeView` and `CodeEditor` into a
  shared `FoldablePlainTextEdit` base or gutter controller component.
- **Why needed**: Reduces code duplication across editors, ensures uniform gutter behavior, and
  simplifies maintenance of code folding features.
- **Impact**: Improves maintainability and eliminates divergent bug fixes across editor widgets.
- **Suggested approach**: Create `pypost/ui/widgets/fold/foldable_editor_base.py` and migrate shared
  gutter event delegation and painting into a reusable mixin.
- **Jira**: [PYPOST-1369](https://pypost.atlassian.net/browse/PYPOST-1369)

### [Low] Asynchronous Background Fold Scanning for Large Stream Payloads
- **Description**: Offload fold region discovery and AST parsing to a background worker thread or
  asynchronous task when stream frame payloads exceed a configurable size threshold (e.g. >500KB).
- **Why needed**: Prevents synchronous main-thread parsing from freezing the UI during rapid
  navigation across large WebSocket messages.
- **Impact**: Keeps the user interface responsive and fluid when inspecting high-volume or
  large-frame streaming sessions.
- **Suggested approach**: Utilize `QThreadPool` or an async scanning worker in `FoldController` with
  cancellation tokens for superseded entry selections.
- **Jira**: [PYPOST-1370](https://pypost.atlassian.net/browse/PYPOST-1370)

### [Low] Stress and Malformed Payload Test Suite for Streaming Views
- **Description**: Add automated stress tests covering streaming intake of large frames (>1MB),
  fuzzed malformed XML/YAML frames, and rapid selection changes with explicit pytest timeouts.
- **Why needed**: Guarantees system resilience against corrupt stream data and prevents regressions
  in memory or rendering performance.
- **Impact**: Increases test confidence under edge-case streaming workloads.
- **Suggested approach**: Create `tests/test_websocket_stream_folding_stress.py` with parameterized
  malformed payloads and large payload benchmarks marked with strict pytest timeouts.
- **Jira**: [PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371)
