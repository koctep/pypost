# PYPOST-1367: Technical Debt Analysis

## Shortcuts Taken

- **Direct Embedding of FoldableCodeView Instead of Shared Base**: Rather than refactoring
  `McpResultView` and other viewer components (`ResponseView`, `StreamDetailPane`, `CodeEditor`) to
  derive from a unified, consolidated foldable viewer hierarchy or mixin, `McpResultView` embeds
  `FoldableCodeView` directly. This was a pragmatic shortcut to quickly deliver code folding in the
  MCP result inspection pane without triggering a broad refactor of existing editors. This shares
  architectural technical debt with PYPOST-1369.
- **Synchronous Fold Scan in `set_result()`**: `McpResultView.set_result()` invokes
  `self._body.fold_controller().ensure_scanned()` immediately upon displaying payload text. This
  guarantees fold regions are immediately available for the user and that bulk buttons reflect
  accurate states, but it bypasses the debounced scan mechanism and executes fold parsing
  synchronously on the main thread right after payload delivery.

## Code Quality Issues

- **Inline Pretty-Printing in `set_result()`**: `McpResultView` executes an inline `json.loads` and
  `json.dumps(parsed, indent=2)` pass if `fmt == BodyFormat.JSON` to ensure unindented tool
  responses obtain clean line-based fold regions. While practical, this couples presentation-tier
  pretty-printing directly into the widget rather than delegating formatting to a dedicated
  payload formatting pipeline or shared formatter service.
- **Format Detection Heuristic Fallbacks**: Format detection via `detect_body_format` on MCP tool
  results relies on text-prefix heuristics and trial parsing (`json.loads`, `yaml.safe_load`,
  `xml.etree.ElementTree.fromstring`) without Content-Type metadata (passing `headers=None`). For
  large mixed or arbitrary text responses, heuristic fallback parsing can trigger exploratory parse
  attempts before concluding the payload is `BodyFormat.PLAIN`.

## Missing Tests

- **Huge MCP Tool Results (>5MB) with Execution Timeouts**: Test coverage in
  `tests/test_mcp_result_view_folding.py` exercises typical small to medium JSON, YAML, and XML
  payloads. There are currently no automated tests verifying memory usage, rendering performance,
  and explicit test execution timeouts when an MCP tool returns massive payloads (>5MB, such as
  bulk database dumps or large file content reads).
- **Streaming Partial Tool Results**: MCP protocol supports progress notifications and future
  partial/streaming execution chunks. There are currently no tests or handling for incremental
  folding updates while a streaming tool call delivers chunks prior to final completion.

## Performance Concerns

- **Main Thread AST Parsing for Large Tool Results**: Fold region discovery executes synchronous
  AST parsing (`json.loads`, `yaml.compose_all`, `xml.etree.ElementTree`) via `ensure_scanned()` on
  the Qt main UI thread. For very large tool responses (several megabytes), synchronous AST
  traversal can introduce momentary frame drops or UI freezing on the main thread. This shares
  architectural debt with PYPOST-1370.

## Follow-up Tasks

### [Medium] Extract Consolidated Shared Foldable Viewer Base Class and Gutter Controller
- **Description**: Consolidate common line-number area painting, chevron drawing, and fold
  management logic between `FoldableCodeView`, `McpResultView`, and `CodeEditor` into a unified
  shared base component or reusable gutter controller mixin.
- **Why needed**: Eliminates duplicated gutter management and inspection patterns across response,
  stream, and MCP viewers, standardizing fold button and gutter behaviors.
- **Impact**: Improves maintainability and prevents divergent fixes across viewer widgets.
- **Suggested approach**: Create `pypost/ui/widgets/fold/foldable_editor_base.py` and extract
  shared gutter delegation and viewer mechanics.
- **Jira**: [PYPOST-1369](https://pypost.atlassian.net/browse/PYPOST-1369)

### [Low] Asynchronous Background Fold Scanning for Large Payloads
- **Description**: Offload fold region discovery and AST parsing to a background worker (`QThread`
  or worker pool) for tool result payloads exceeding 500KB.
- **Why needed**: Prevents synchronous AST parsing in `ensure_scanned()` from blocking the Qt main
  event loop when rendering large tool execution payloads.
- **Impact**: Keeps the user interface responsive and fluid when inspecting extensive tool outputs.
- **Suggested approach**: Implement asynchronous scanning in `FoldController` with debounced scan
  cancellation when tool selection or content changes.
- **Jira**: [PYPOST-1370](https://pypost.atlassian.net/browse/PYPOST-1370)

### [Low] Stress Test Suite for Massive MCP Results and Streaming Payloads
- **Description**: Add dedicated stress tests in `tests/test_mcp_result_view_folding.py` (or a
  dedicated stress test module) with >5MB tool result payloads, malformed JSON/YAML/XML payloads,
  and explicit test timeouts.
- **Why needed**: Verifies that large database dumps or bulk file reads do not cause unbounded
  memory consumption or UI deadlocks.
- **Impact**: Hardens the MCP client inspection against edge-case server payloads and prevents
  performance regressions.
- **Suggested approach**: Add parameterized stress test fixtures with synthetic multi-megabyte JSON
  and XML payloads guarded by strict `@pytest.mark.timeout` limits.
- **Jira**: [PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371)
