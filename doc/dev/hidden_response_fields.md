# Hidden Response Fields Architecture and Decomposition (PYPOST-1312 / PYPOST-1376 / PYPOST-1386 / PYPOST-1387 / PYPOST-1395 / PYPOST-1396)

## Overview

Modern API workflows frequently handle sensitive information such as authentication credentials,
API tokens, passwords, session identifiers, and Personally Identifiable Information (PII). When
executing requests in PyPost, these fields pose dual security risks:

1. **Desktop GUI Exposure**: Displaying secrets in plain text within `ResponseView` creates risk during
   screen sharing, presentations, or shoulder-surfing. Users require sensitive response fields to be
   masked by default with an intuitive, in-place click-to-reveal mechanism.
2. **MCP Tool Agent Leakage**: When requests are exposed as Model Context Protocol (MCP) tools for AI
   coding agents, returning raw credentials can leak secrets into LLM contexts or remote logs. MCP outputs
   require permanent, irreversible masking with zero reveal capabilities exposed to agents.
3. **Data Integrity**: Masking is strictly a presentation and serialization transformation. Raw
   in-memory responses (`ResponseData`) and history records remain pristine for scripting and auditing.

Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) addresses these requirements. Planning
task [PYPOST-1376](https://pypost.atlassian.net/browse/PYPOST-1376) established the architecture, selector
specifications, security boundaries, and decomposition into four focused child stories scheduled for Sprint 2032.
Subsequent hardening task [PYPOST-1395](https://pypost.atlassian.net/browse/PYPOST-1395) expanded sample
masking configurations across the remaining bundled reference collections (GitHub, GitLab, and Jira Cloud)
with dedicated automated contract verification. Performance optimization task
[PYPOST-1396](https://pypost.atlassian.net/browse/PYPOST-1396) introduced asynchronous background worker thread
formatting for medium-sized (50 KB – 100 KB) payloads ([`ResponseMaskWorker`](response_mask_worker.md))
to maintain a fluid 60 FPS UI experience without freezes. Editor scalability task
[PYPOST-1386](https://pypost.atlassian.net/browse/PYPOST-1386) refactored the Request Editor
[`HiddenFieldsTable`](hidden_fields_table.md) from `QTableWidget` to a virtualized
`QAbstractTableModel` + `QTableView` stack so large selector catalogs (>1,000 paths) stay
responsive with minimal per-row memory. Inline syntax guidance task
[PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387) adds advisory validation
(`validate_field_selector`, model `BackgroundRole` / `ToolTipRole`, and
`FieldSelectorDelegate`) so unsupported selectors are highlighted while drafting without
blocking save.

---

## Child Tasks Breakdown & Implementation Roadmap

To avoid monolithic implementation risks and adhere to repository sizing standards (all child stories
≤ 5 Story Points using the Fibonacci scale), Epic PYPOST-1312 is decomposed into four distinct stories
under active **Sprint 2032** ("Hide Selected Response Fields"):

| Child Key | Provisional ID | Summary | SP | Dependencies | Primary Layer / Area |
| :--- | :---: | :--- | :---: | :---: | :--- |
| [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) | **MASK-1** | Request model, persistence, and RequestEditor UI for hidden response fields | 3 | None | Data models, tab isolation, serialization, editor UI |
| [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) | **MASK-2** | Permanent MCP output masking for hidden response fields | 3 | PYPOST-1377 | McpResponseSanitizer, tool serialization, security boundary |
| [PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379) | **MASK-3** | Interactive click-to-reveal response masking in GUI ResponseView | 5 | PYPOST-1377 | GUI widget rendering, click detection, highlighter coexistence |
| [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380) | **MASK-4** | Integration test suite, edge-case coverage, and developer documentation | 3 | PYPOST-1377, 1378, 1379 | End-to-end contracts, edge cases, fixtures, documentation |

**Total Estimated Effort**: 14 SP across 4 stories.

### Execution Sequence

```
      [MASK-1: Model, Persistence & RequestEditor UI] (3 SP)
                      /                \
                     /                  \
                    v                    v
  [MASK-2: MCP Permanent Mask] (3 SP)   [MASK-3: GUI Click-to-Reveal] (5 SP)
                    \                    /
                      \                /
                        v            v
      [MASK-4: Integration Tests & Dev Docs] (3 SP)
```

1. **Phase 1 (Foundation)**: Execute **MASK-1** ([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377)) to establish the `hidden_response_fields` model attribute, persistence round-tripping, tab isolation copying, and editor configuration UI.
2. **Phase 2 (Parallel Implementation)**:
   - Execute **MASK-2** ([PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378)) for server-side irreversible MCP output sanitization.
   - Execute **MASK-3** ([PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379)) for desktop GUI click-to-reveal presentation in `ResponseView`.
3. **Phase 3 (Verification & Documentation)**: Execute **MASK-4** ([PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)) to build end-to-end integration contracts across GUI and MCP boundaries, edge-case test matrices, and reference collections.

---

## Architectural Specifications

### 1. RequestData Schema Extension, Tab Copy Isolation, and RequestEditor UI (MASK-1)

The configuration of which response fields to hide lives as part of the canonical request definition:

#### Data Model Extension (`pypost/models/models.py`)
- **Schema Field**:
  ```python
  class RequestData(BaseModel):
      ...
      hidden_response_fields: list[str] = Field(default_factory=list)
  ```
- **Serialization & Backward Compatibility**:
  - Pydantic serializes `hidden_response_fields` into standard JSON string arrays when persisting requests via `StorageManager.save_collection`.
  - Using `Field(default_factory=list)` guarantees 100% backward compatibility: legacy collections, fixtures, or exports lacking `hidden_response_fields` load cleanly with an empty list `[]` without requiring schema migrations or disk rewrites.
  - Strict type validation enforces that all configured selectors are strings (`list[str]`).

#### Persisted Field Dirty-Tracking (`pypost/core/request_persisted_fields.py`)
- **Canonical Registry**:
  `"hidden_response_fields"` is registered in `_PERSISTED_FIELD_NAMES` and `_DRAFT_FIELD_NAMES`.
- **Dirty Checking Mechanics**:
  - `persisted_fields_equal(a, b)`: Compares `a.hidden_response_fields == b.hidden_response_fields` across request versions.
  - `request_draft_fields_equal(a, b)`: Validates draft changes against `factory_request_draft()`.
  - Any addition, deletion, or reordering of selectors compared to a tab's baseline snapshot triggers `is_tab_dirty(tab)` in `tab_dirty.py`, correctly marking the tab dirty (`*`) and informing unsaved change prompts.

#### Tab Copy Isolation Deep-Copy Semantics (`pypost/core/request_persisted_fields.py`)
- **Copy Semantics**:
  Per the [Request Data Copy Policy](request_data_copy_policy.md), `copy_request_for_isolated_tab(data: RequestData) -> RequestData` performs a deep copy of the request model:
  ```python
  copy = data.model_copy(deep=True)
  copy.hidden_response_fields = list(data.hidden_response_fields)
  return copy
  ```
- **Isolation Guarantee**:
  Ensures that mutable list instances of `hidden_response_fields` are completely detached across tabs. Modifying field selectors in an isolated tab draft never mutates the original request or sibling tabs.

#### `HiddenFieldsTable` Component API (`pypost/ui/widgets/hidden_fields_table.py`)

Virtualized single-column selector editor
([PYPOST-1386](https://pypost.atlassian.net/browse/PYPOST-1386) /
[PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387)).
Full Model/View details, syntax validation, facades, observability, and troubleshooting:
[Virtualized Hidden Fields Table](hidden_fields_table.md).

- **Architecture**:
  - View: `HiddenFieldsTable(QTableView)` in `pypost/ui/widgets/hidden_fields_table.py`.
  - Model: `HiddenFieldsTableModel(QAbstractTableModel)` in
    `pypost/ui/models/hidden_fields_table_model.py` (also re-exported from the widget module).
  - Rows are lightweight `HiddenFieldRecord` dataclasses; the view requests `DisplayRole` /
    `EditRole` only for visible cells (no per-row `QTableWidgetItem` allocations).
  - Syntax: pure `validate_field_selector` in `pypost/core/field_selector_syntax.py`;
    committed cells expose soft error `BackgroundRole` and guidance `ToolTipRole`;
    `FieldSelectorDelegate` provides as-you-type editor feedback (advisory — always commits).
- **Widget Identification**: Registered with `REQUEST_HIDDEN_FIELDS_TABLE = "request_hidden_fields_table"` via `set_widget_id()`.
- **Table Structure**: Single column labeled `"Field Selector"`, configured with `QHeaderView.ResizeMode.Stretch`.
- **Auto-Expanding Trailing Row**: Model invariant keeps exactly one blank trailing record.
  Committing non-empty text on that row inserts a new blank trailer (same interaction pattern as
  PyPost's `KeyValueTable` / `EmptyRowKeyValueTable`).
- **Public API** (unchanged for `RequestEditor` and existing tests):
  - `set_data(data: list[str]) -> None`: Populates the table with existing non-empty selectors, filtering out whitespace, and appends a trailing empty row.
  - `get_data() -> list[str]`: Extracts all non-empty selector strings in row order, omitting trailing or intermediate blank rows. Invalid selectors are retained as authored.
  - `add_row(selector: str = "") -> None`: Appends a selector row or focuses and edits the trailing empty row if currently blank.
  - `remove_selected_rows() -> None`: Deletes highlighted rows (preserving the trailing empty row structure) and emits change signals.
- **Compatibility Facades** (legacy `QTableWidget`-style introspection):
  - `rowCount() -> int` / `columnCount() -> int` forward to the model.
  - `item(row, col)` returns `_TableItemFacade` with `.text() -> str` (not a full `QTableWidgetItem`).
- **Signals**:
  - `data_changed = Signal()`
  - `changed = Signal()`
  - Forwarded from the model so dirty tracking in `RequestEditor` is unchanged.
- **User Interactions**:
  - Context menu (`QContextMenuEvent`): Provides "Add Selector" and "Remove Selected" actions.
  - Keyboard shortcuts (`QKeyEvent`): Pressing `Delete` or `Backspace` outside cell edit mode deletes selected rows.

#### `RequestEditor` Detail Tab Integration (`pypost/ui/widgets/request_editor.py`)
- **Tab Layout**:
  Embedded as a dedicated `"Hidden Fields"` tab in `RequestWidget.detail_tabs`:
  - Informational label with styling guidance: `"Response fields or dot-notation paths to hide (e.g. token, password, user.secret)"`.
  - Action toolbar containing "Add Selector" and "Remove Selected" buttons connected to table methods.
  - Embedded `HiddenFieldsTable(self)`.
- **Data Lifecycle Integration**:
  - `load_data(req)`: Calls `self.hidden_fields_table.set_data(self.request_data.hidden_response_fields)` when initializing or switching requests.
  - `update_request_data()`: Updates `self.request_data.hidden_response_fields = self.hidden_fields_table.get_data()`.
  - `get_request_data_from_ui()`: Extracts draft state with `hidden_response_fields=self.hidden_fields_table.get_data()`.
  - Change propagation: Connected signals `data_changed` and `changed` to `self.on_data_changed` to immediately update tab dirty state.

### 2. Fail-Closed MCP Permanent Masking Boundary (MASK-2)

When requests are invoked via MCP tools, security isolation from external AI agents is paramount. Unlike desktop GUI users who can interactively inspect unmasked values using click-to-reveal (MASK-3), automated AI agents are treated as untrusted consumers with respect to sensitive credentials.

```
Agent Tool Invocation
  → MCPServerImpl._call_tool_inner
    → RequestService._execute_request_sync
      → ExecutionResult(response)
        → format_structured_tool_result(..., hidden_response_fields=request.hidden_response_fields)
          → McpResponseSanitizer.sanitize_body
            → sensitive_text_sanitizer.redact_json_response_fields
              → Irreversible Output with "***"
```

#### Pipeline Integration
1. **Tool Execution Dispatch**:
   In `MCPServerImpl._call_tool_inner` (`pypost/core/mcp_server_impl.py`), `item` represents the executed `RequestData`. The configured field selectors are extracted:
   ```python
   hidden_fields = (
       item.hidden_response_fields
       if isinstance(item, RequestData)
       else None
   )
   ```
2. **Result Serialization**:
   `format_structured_tool_result` accepts `hidden_response_fields: Sequence[str] | None = None` and passes it directly to `McpResponseSanitizer.sanitize_body`.
3. **Sanitization Facade**:
   `McpResponseSanitizer.sanitize_body` (`pypost/core/mcp_response_sanitizer.py`) coordinates body sanitization:
   ```python
   fields = hidden_response_fields if hidden_response_fields is not None else hidden_fields
   if fields:
       body = sts.redact_json_response_fields(body, fields)
   return sts.sanitize_text(body, env_vars=env_vars, hidden_keys=hidden_keys)
   ```
   This ensures both request-level field selectors and global environment variable secrets (`hidden_keys`, Bearer tokens, Authorization headers) are redacted before output serialization.

#### Irreversible Security Boundary Invariant
- **Zero Reveal Parameters**:
  `build_tool_input_schema` in `pypost/core/mcp_tool_contract.py` constructs MCP tool schemas exclusively from discovered `{{mcp.request.<param>}}` placeholders and permitted environment variable overrides. No parameter (e.g. `unmask`, `reveal`, `reveal_secrets`, `show_hidden`, `raw`) exists or is advertised to agents.
- **Zero Reveal Tools**:
  `MCPServerImpl` registers only user-defined endpoints where `expose_as_mcp == True`. No auxiliary tools (such as `reveal_response_field`, `get_raw_body`, or `unmask_secret`) are registered on the MCP server.
- **No Reveal Bypass**:
  Masking is applied unilaterally during output serialization. Even if an agent crafts and sends unexpected parameters (e.g. `{"unmask": true}`), the input validator rejects or ignores them, and output serialization unconditionally redacts all configured fields.

#### Supported Selector Syntax & Path Evaluation
The engine in `sensitive_text_sanitizer.redact_json_response_fields` parses and evaluates four selector formats:
- **Simple / Root Keys**: Exact key match (e.g., `"token"`, `"password"`, `"api_key"`). Matches anywhere in the JSON hierarchy (root, nested objects, or list items).
- **Dot-Notation Paths**: Specific hierarchical paths from root (e.g., `"auth.token"`, `"data.user.credentials.secret"`). Matches exact nested object chains, leaving siblings untouched.
- **Array Wildcards & Shorthands**: Wildcard path syntax (`"users[*].email"`, `"items[*].secret"`) or dot-notation array shorthand (`"users.email"`, `"items.secret"`). Traverses arrays of objects and redacts the matching key across every array item.
- **Response Header Prefix**: Selectors prefixed with `header:` (e.g., `"header:Authorization"`, `"header:X-Auth-Token"`). Handled by `sensitive_text_sanitizer.sanitize_headers`, redacting matching response headers alongside standard sensitive header names.

#### Non-JSON Pass-Through and Graceful Error Fallback
- **Robust Exception Handling**:
  If the response body is plain text, HTML, XML, binary, or malformed JSON, `redact_json_response_fields` safely catches `(json.JSONDecodeError, TypeError, ValueError)`.
- **Pass-Through Behavior**:
  On exception, the raw body text is returned intact to allow standard downstream text sanitization (`sanitize_text`), which continues to mask known environment secret variable values and Bearer tokens without raising unhandled exceptions or failing open.
- **Diagnostic Safety**:
  Debug logs record only the exception type name (`reason=JSONDecodeError`), guaranteeing no partial or malformed sensitive payloads are leaked to logging streams.

#### Display-Only Immutability of In-Memory ResponseData
- **Output-Only Transformation**:
  Masking occurs strictly during serialization into the `TextContent(type="text", text=output_text)` payload returned across the MCP JSON-RPC protocol.
- **Pristine Internal State**:
  The underlying `ExecutionResult.response` (`ResponseData`) and history entries stored via `HistoryManager` remain completely unmodified.
- **Compliance & Post-Processing**:
  In-memory response data remains authentic for post-request scripts, test assertions, audit logs, and desktop GUI inspection.

#### Telemetry Metrics & Structured Logging
- **Observability Metric**:
  When `hidden_fields` are configured on an executed request, `MCPServerImpl._call_tool_inner` increments the low-cardinality Prometheus / OpenTelemetry counter:
  - Metric name: `hidden_value_masks_applied_total`
  - Label: `surface="mcp"`
  - Method: `self._metrics.track_hidden_value_mask_applied("mcp")`
- **Structured Logging (Zero Secret Leakage)**:
  - `mcp_response_masking_applied method=<method> tool=<tool> selector_count=<count>` (DEBUG in `MCPServerImpl`)
  - `redact_json_response_fields_completed selectors_count=<count> masked_fields_count=<count>` (DEBUG in `sensitive_text_sanitizer`)
  - `redact_json_response_fields_skipped_non_json reason=<exception_type>` (DEBUG in `sensitive_text_sanitizer`)
  - All log entries strictly record numeric counts and schema keys, never logging payload secrets or sensitive token values.

### 3. Interactive Click-to-Reveal GUI Masking Architecture in ResponseView (MASK-3)

In desktop GUI mode, users need confidentiality during screen sharing and pair programming while retaining full interactive access to inspect, copy, or set variables from response data:

```
display_response(response, hidden_fields)
  → ResponseMaskController.format_masked_json(raw_json, hidden_fields)
    → FoldableCodeView.setText(masked_json)
      → ResponseMaskController.set_masked_spans(spans)
        → Apply ExtraSelection visual formats
        → JsonHighlighter highlights "***" as valid string literal
          → Viewport Mouse Hover: PointingHandCursor & Tooltips
          → Viewport Left-Click: In-place QTextCursor toggle ("***" <-> raw_value)
            → Downstream span offset delta shifting
            → Search match counter & code folding synchronization
```

#### MaskedTokenSpan Data Structure and JsonMaskFormatter AST Parsing
- **`MaskedTokenSpan` Model (`pypost/ui/widgets/response_mask_controller.py`)**:
  A lightweight dataclass that tracks character boundaries and state transitions within the `QTextDocument`:
  ```python
  @dataclass
  class MaskedTokenSpan:
      start_pos: int          # Character offset start in QTextDocument
      end_pos: int            # Character offset end in QTextDocument
      raw_value: str          # Unmasked JSON serialized literal (e.g. '"secret_token_123"' or '42')
      masked_value: str = '"***"'  # Masked placeholder string
      is_revealed: bool = False    # Presentation toggle state
      path: str = ""          # JSON dot-notation path (e.g. 'auth.token')
  ```
- **AST Parsing and Span Discovery (`JsonMaskFormatter`)**:
  - Rather than regex scraping (which is prone to false positives on escaped strings or keys matching value names), `format_masked_json` parses the JSON body into a Python AST structure (`dict` / `list` / primitive nodes).
  - `JsonMaskFormatter` walks the structure recursively, building the formatted JSON string buffer with `indent=self.indent_size`.
  - At each node, it resolves hierarchical path variants using `format_path_variants(path, key_str)` from `sensitive_text_sanitizer.py` (matching simple keys, dot paths, and array wildcards).
  - When a node matches a configured selector:
    - Instead of emitting the node's serialized value, it emits the placeholder string `'"***"'`.
    - It records the exact start and end character offsets in the emitted output stream: `start_pos = current_offset`, `end_pos = current_offset + len(masked_value)`.
    - It stores the true raw value (serialized with matching indentation via `json.dumps(val, indent=indent, ensure_ascii=False)`) in `raw_value`.
    - Appends a `MaskedTokenSpan` instance to the tracking list.
  - Returns `(pretty_json_str, spans)`.

#### ResponseMaskController Lifecycle & Visual Styling
`ResponseMaskController` (`QObject`) manages span tracking and user interactions for `FoldableCodeView`:
- **Viewport Event Filtering**:
  - Installs an event filter on `FoldableCodeView.viewport()` and enables `setMouseTracking(True)`.
  - On `QEvent.Type.MouseMove`:
    - Maps coordinate to character index via `code_view.cursorForPosition(pos).position()`.
    - Hit-tests against tracked spans via `span_at(char_pos)`.
    - If hovering over a span: updates cursor to `Qt.CursorShape.PointingHandCursor` and displays a tooltip via `QToolTip.showText` (`"Click to reveal"` or `"Click to re-mask"`).
    - If hovering outside all spans: restores `Qt.CursorShape.IBeamCursor` and hides tooltips via `QToolTip.hideText()`.
  - On `QEvent.Type.Leave`: restores `IBeamCursor` and dismisses tooltips.
- **ExtraSelection Visual Affordance (`update_visual_formats`)**:
  - Masking affordances are rendered using Qt's `QTextEdit.ExtraSelection` API on `FoldableCodeView`.
  - `ExtraSelection` paints decorations directly in the viewport layer without mutating document text, modifying character offsets, or interfering with `QSyntaxHighlighter`.
  - **Masked State (`is_revealed == False`)**:
    - Background: neutral gray tint (`QColor(128, 128, 128, 48)`).
    - Underline: dashed underline (`QTextCharFormat.UnderlineStyle.DashUnderline`).
    - Tooltip: `"Click to reveal"`.
  - **Revealed State (`is_revealed == True`)**:
    - Background: subtle green tint (`QColor(76, 175, 80, 40)`).
    - Underline: dotted underline (`QTextCharFormat.UnderlineStyle.DotLine`).
    - Tooltip: `"Click to re-mask"`.
- **Lifecycle Cleanup**:
  - `clear()` empties tracked spans, clears extra selections, restores `IBeamCursor`, and hides active tooltips.
  - Automatically invoked on `clear_body()` and prior to new response rendering in `display_response()`.

#### In-Place Click-to-Reveal Toggle Mechanics and Span Offset Shifting
- **Click Detection (`eventFilter` & `handle_click`)**:
  - On `QEvent.Type.MouseButtonRelease` with `Qt.MouseButton.LeftButton`:
    - Checks `not self.code_view.textCursor().hasSelection()` to ensure text drag-selection is not mistaken for a click.
    - Resolves `char_pos = self.code_view.cursorForPosition(pos).position()`.
    - Calls `handle_click(char_pos)`.
- **In-Place QTextCursor Replacement**:
  - Locates target span `span = self.span_at(char_pos)`.
  - Computes `old_len = span.end_pos - span.start_pos`.
  - Selects replacement text: `new_text = span.raw_value if not span.is_revealed else span.masked_value`.
  - Toggles `span.is_revealed = not span.is_revealed`.
  - Uses `QTextCursor` to perform in-place replacement:
    ```python
    cursor = QTextCursor(self.code_view.document())
    cursor.setPosition(span.start_pos)
    cursor.setPosition(span.end_pos, QTextCursor.MoveMode.KeepAnchor)
    cursor.insertText(new_text)
    ```
    *(Note: In Qt `QPlainTextEdit`, programmatic cursor edits succeed even when `isReadOnly() == True`, preventing user typing while allowing scriptable modifications).*
- **Downstream Span Offset Delta Shifting**:
  - Calculates length delta: `delta = len(new_text) - old_len`.
  - Updates target span boundary: `span.end_pos = span.start_pos + len(new_text)`.
  - Shifts all subsequent spans (`other.start_pos > span.start_pos`) in the tracked list:
    ```python
    for other in self._spans:
        if other.start_pos > span.start_pos:
            other.start_pos += delta
            other.end_pos += delta
    ```
  - Spans preceding the toggled position remain unaffected. This preserves exact coordinate integrity across any sequence of reveals and re-masks.
  - Updates visual formats via `update_visual_formats()`.

#### Subsystem Coexistence
- **Syntax Highlighting (`JsonHighlighter`)**:
  - Masked placeholder `'"***"'` matches the standard JSON string literal regex pattern (`r'"[^"\\]*(\\.[^"\\]*)*"'`).
  - Replacing text via `QTextCursor.insertText()` automatically triggers Qt's incremental block re-highlighting without modifying `JsonHighlighter` rules.
  - Highlighting updates smoothly without infinite loops or UI flickering.
- **Search Navigation & Match Counter Synchronization**:
  - PyPost's search engine searches directly within the active `QTextDocument`.
  - While masked, searching for the raw secret produces zero matches; searching for `"***"` matches masked fields.
  - When revealed, the raw secret is physically present in the document and immediately searchable via `Ctrl+F`, `Next`, and `Previous`.
  - After toggling a span, if `response_view.search_input` has text, `handle_click` triggers `_on_search_text_changed()`, instantly updating match navigation and the match count indicator (e.g. `"1 of 2"`).
  - Re-masking immediately updates search matches back to the masked state.
- **Code Folding Block Stability (`FoldController`)**:
  - PyPost's `FoldController` identifies foldable block regions from indentation and brace/bracket structure (`{}`, `[]`).
  - Toggling scalar strings alters character count on the current line but preserves line numbers, indentation, and brace pairs.
  - Following each toggle, `self.code_view.fold_controller().ensure_scanned()` is called to ensure fold regions remain valid and intact.
- **Context Menu Integration ("Set Variable" & "Copy")**:
  - When text is highlighted in `FoldableCodeView`, the custom context menu provides:
    - `"Set Variable"` (active when environment keys exist): emits `variable_set_requested(key, selected_text)`.
    - `"Copy"`: copies selected text to system clipboard.
  - If a user selects an unmasked secret and clicks "Set Variable" or "Copy", the authentic secret value is read from the cursor (`cursor.selectedText()`) and emitted or copied.
  - Because `eventFilter` checks `not self.code_view.textCursor().hasSelection()`, drag-selecting revealed text never accidentally triggers a re-mask toggle.

#### Operating Bands, Background Offloading & Streaming Safety
- **Operating Bands Routing**:
  - **Small Payloads (`< 50 KB`)**: Formatted and masked synchronously via `format_masked_json` in sub-frame latency (<5 ms).
  - **Medium Payloads (`50 KB – 100 KB`)**: Asynchronously formatted via dedicated background worker [`ResponseMaskWorker`](response_mask_worker.md) (`QThread`), preventing UI stutters and keeping frame rates at 60 FPS while setting placeholder `"Formatting masked response..."` to guarantee zero secret flash. Obsolete background tasks are cancelled cooperatively upon tab switches or rapid response arrivals.
  - **Large Documents (`> 100 KB`)**: If the payload exceeds `LARGE_DOC_CHAR_THRESHOLD` (`100 * 1024` chars), `display_response` logs `response_masking_large_doc_fallback` and bypasses pretty-printing, AST traversal, and span tracking, setting raw text directly to protect editor performance.
- **In-Flight Streaming Response Safety**:
  - During streaming requests, chunks arrive incrementally via `ResponseView.append_body(chunk)` without attempting partial AST parsing.
  - Upon request completion, `TabsPresenterWorker._on_request_finished` calls `display_response(response, hidden_fields=tab.request_data.hidden_response_fields)`, cleanly replacing the streamed text with the formatted, masked JSON document.

#### Raw ResponseData Immutability & Telemetry Metrics
- **Immutability of In-Memory `ResponseData`**:
  - All masking and unmasking transformations are presentation-only, operating strictly on the `QTextDocument` in `ResponseView`.
  - `response.body` on the `ResponseData` instance and history records stored via `HistoryManager` remain completely unmodified.
  - Re-indenting JSON via `set_indent_size()` safely re-applies formatting from `self._last_response` and `self._last_hidden_fields`.
- **Telemetry Counter**:
  - When masking spans are initialized in `display_response`, the system tracks telemetry via:
    - Metric: `hidden_value_masks_applied_total`
    - Label: `surface="gui_response"`
    - Invocation: `self._metrics.track_hidden_value_mask_applied("gui_response")`
- **Structured Logging (Zero Leakage)**:
  - `response_masking_initialized span_count=<count> selectors_count=<count>` (DEBUG)
  - `response_masking_spans_updated span_count=<count>` (DEBUG)
  - `click_to_reveal_toggle path=<path> revealed=<bool>` (DEBUG)
  - `response_masking_large_doc_fallback payload_size=<size> threshold=<threshold>` (DEBUG)
  - All logs record paths and counts, never exposing secret values.

### 4. Selector Syntax & Matching Rules

The selector engine supports four syntax formats:

| Selector Format | Pattern | Example | Semantics |
| :--- | :--- | :--- | :--- |
| **Simple Key** | `<key>` | `token`, `password`, `secret` | Matches JSON keys with this exact name at any nesting depth. |
| **Dot-Notation Path** | `<parent>.<child>` | `auth.token`, `data.user.secret` | Matches exact hierarchical object paths. |
| **Array Wildcard Path** | `<array>[*].<field>` | `users[*].email`, `items[*].secret` | Matches specific fields across array elements. |
| **Header Selector** | `header:<Name>` | `header:Authorization` | Targets HTTP response headers for MCP sanitization. |

### 5. Integration Testing, Edge-Case Verification, and Reference Collections (MASK-4)

The final phase of Epic PYPOST-1312 (Story [PYPOST-1380](https://pypost.atlassian.net/browse/PYPOST-1380)) establishes an end-to-end integration test harness, a comprehensive edge-case validation matrix, and realistic reference collection fixtures to prove the safety and correctness of the dual-surface masking architecture.

#### Test Architecture (`tests/test_hidden_response_fields_integration_edge_cases.py`)

The integration test suite lives in `tests/test_hidden_response_fields_integration_edge_cases.py` and exercises the end-to-end pipelines across both MCP server serialization and desktop GUI `ResponseView` rendering:

```
                              ExecutionResult (ResponseData)
                                     /             \
                                    /               \
                                   v                 v
                 MCP Serialization Pipeline     GUI Presentation Pipeline
               (format_structured_tool_result)   (ResponseView.display_response)
                            |                                 |
                            v                                 v
                 Irreversible "***" Redaction     MaskedTokenSpan AST Tracking
                 Zero Agent Reveal Parameters     Interactive Click-to-Reveal
                            \                                 /
                             \                               /
                              v                             v
                       Verified Invariant: ResponseData.body Unmutated
```

- **Test Suite Structure**:
  - Test class: `TestHiddenResponseFieldsIntegrationEdgeCases` parameterized with Qt application fixture (`qapp: QApplication`).
  - Strict execution timeout: `pytestmark = pytest.mark.timeout(60)` to prevent test hangs.
  - Realistic mock factory: `_make_exec_result(body, status_code, headers)` builds authentic `ExecutionResult` and `ResponseData` instances matching live runtime execution.
- **Architectural Verification Guarantees**:
  - **Dual-Surface Consistency**: Exercises identical `ResponseData` instances sequentially through MCP serialization and GUI `ResponseView`, verifying expected redactions across both boundaries.
  - **Memory Immutability Invariant**: Asserts that `exec_result.response.body == original_body_str` remains byte-for-byte identical after all transformations.
  - **MCP Fail-Closed Schema Invariant**: Validates via `server.list_tools()` that registered tool definitions expose zero reveal/unmask parameters, preventing agent prompt injection or leakage.
  - **Span Index Stability**: Verifies that toggling arbitrary spans in `ResponseMaskController` shifts downstream character positions correctly without off-by-one errors or text corruption.

#### Edge-Case Validation Matrix

The test suite validates 8 comprehensive integration scenarios covering complex JSON topologies, primitive values, error formats, and concurrency:

| Scenario | Scope / Area | Verification Criteria | Test Method |
| :--- | :--- | :--- | :--- |
| **Scenario 1** | **Cross-Cutting Dual Consumption** | Same `ResponseData` passed to MCP and GUI. MCP produces permanent `***`; GUI produces interactive `MaskedTokenSpan`s allowing reveal and re-mask. Raw `ResponseData.body` remains unmutated. Tool schema has zero reveal params. | `test_scenario_1_cross_cutting_e2e_contract` |
| **Scenario 2** | **Deeply Nested Keys (>5 Levels)** | Path `level1.level2.level3.level4.level5.level6.secret` resolves exact target in deep AST hierarchy. Sibling keys at depth 6 (`public`) and parallel branches at depth 3 (`other.secret`) remain unmasked. | `test_scenario_2_deeply_nested_paths` |
| **Scenario 3** | **Array Wildcards & Heterogeneity** | Nested wildcards (`items[*].token`), root array wildcards (`[*].id`), and heterogeneous arrays (containing strings, integers, `None`, lists, dicts) traversed without exceptions. | `test_scenario_3_array_wildcard_selectors` |
| **Scenario 4** | **Primitive Values & Nulls** | Non-string primitives (integers `1234`, floats `3.1415`, booleans `true`/`false`, and `null`) masked cleanly as `***`. GUI click-to-reveal faithfully renders literal unquoted/typed values. | `test_scenario_4_non_string_primitives_and_null_masking` |
| **Scenario 5** | **Duplicate Keys in Distinct Branches** | Qualified dot path `user.id` masks only `user.id` leaving `organization.id` and `metadata.id` intact. Unqualified selector `name` masks all occurrences across distinct object branches. | `test_scenario_5_duplicate_keys_in_distinct_branches` |
| **Scenario 6** | **Non-JSON Payloads & HTTP 204** | HTML error pages (500), plain text (401), and malformed JSON safely pass through without crashes. HTTP 204 No Content renders empty body with zero spans and valid status display. | `test_scenario_6_non_json_and_empty_response_handling` |
| **Scenario 7** | **Multi-Tab Concurrency Isolation** | `copy_request_for_isolated_tab` deep-copies `hidden_response_fields`. Selector mutations in Tab B do not pollute Tab A or dirty baselines. Concurrent `ResponseView` instances manage independent spans. | `test_scenario_7_multi_tab_concurrency_isolation` |
| **Scenario 8** | **Reference Collection Fixture** | Validates `examples/collections/google_drive.json` request `gdrive-about-get`. Asserts disk persistence, Pydantic model serialization, and live execution through MCP and GUI masking pipelines. | `test_scenario_8_reference_collection_fixture_validation` |

#### Reference Collection Fixtures & Bundled Catalog Masking Examples (PYPOST-1380 / PYPOST-1395)

To provide developers and users with authentic, production-grade reference configurations,
PyPost configures `hidden_response_fields` across all bundled example collections in
`examples/collections/`. These shipped configurations demonstrate best practices for masking
credentials, security attributes, and Personally Identifiable Information (PII) across both
interactive desktop GUI sessions and autonomous AI agent tool invocations via MCP.

##### Bundled Collections Masking Overview

| Bundled Collection | Request ID | Endpoint | Selector Patterns | Masked Properties | Target Sensitivity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Google Drive** (`google_drive.json`) | `gdrive-about-get` | `GET /about` | Bare keys & dotted path | `emailAddress`, `permissionId`, `user.emailAddress` | User PII & account permission identifier |
| **GitHub** (`github_mcp.json`) | `github-get-authenticated-user` | `GET /user` | Bare keys & dotted path | `email`, `two_factor_authentication`, `plan.name` | User email, 2FA security status, billing tier |
| **GitLab** (`gitlab_mcp.json`) | `gitlab-get-current-user` | `GET /api/v4/user` | Bare keys (multi-scope) | `email`, `commit_email`, `public_email` | Primary, commit, and public user email addresses |
| **Jira Cloud** (`jira_mcp.json`) | `jira-get-current-user` | `GET /rest/api/3/myself` | Bare keys | `emailAddress`, `accountId` | Atlassian account email and unique account ID |
| **Jira Cloud** (`jira_mcp.json`) | `jira-search-assignable-users` | `GET /rest/api/3/user/assignable/search` | Root array wildcard paths | `[*].emailAddress`, `[*].accountId` | Array of assignable user emails and account IDs |

##### 1. Google Drive Collection (`examples/collections/google_drive.json`)

- **Request ID**: `gdrive-about-get`
- **Request Name**: `"Get Current User and Storage Quota"`
- **Endpoint**: `GET {{ google_drive_base_url }}/about` with query parameter `fields=user(displayName, emailAddress, permissionId), storageQuota`
- **Configured `hidden_response_fields`**:
  ```json
  "hidden_response_fields": [
    "emailAddress",
    "permissionId",
    "user.emailAddress"
  ]
  ```
- **Demonstrated Patterns**: Combines bare key selectors (`emailAddress`, `permissionId`) with
  qualified dotted path selectors (`user.emailAddress`). When Google Drive returns user profile
  and quota data, `emailAddress` and `permissionId` are masked while `displayName` and
  `storageQuota` remain unredacted.

##### 2. GitHub MCP Collection (`examples/collections/github_mcp.json`)

- **Request ID**: `github-get-authenticated-user`
- **Request Name**: `"GitHub Get Authenticated User"`
- **Endpoint**: `GET {{ github_api_url }}/user`
- **Configured `hidden_response_fields`**:
  ```json
  "hidden_response_fields": [
    "email",
    "two_factor_authentication",
    "plan.name"
  ]
  ```
- **Demonstrated Patterns**:
  - `email`: Bare key selector masking top-level and nested email fields.
  - `two_factor_authentication`: Bare key selector protecting security posture flags (boolean).
  - `plan.name`: Dotted object path selector targeting the nested billing plan name
    (`plan: {"name": "pro", ...}`) without redacting non-sensitive sibling billing attributes.

##### 3. GitLab MCP Collection (`examples/collections/gitlab_mcp.json`)

- **Request ID**: `gitlab-get-current-user`
- **Request Name**: `"GitLab Get Current User"`
- **Endpoint**: `GET {{ gitlab_base_url }}/api/v4/user`
- **Configured `hidden_response_fields`**:
  ```json
  "hidden_response_fields": [
    "email",
    "commit_email",
    "public_email"
  ]
  ```
- **Demonstrated Patterns**: Multi-scope email masking protecting distinct PII attributes returned
  in GitLab's user profile schema. Redacts primary account email, author commit email, and public
  profile email simultaneously while preserving public profile fields (`name`, `username`, `web_url`).

##### 4. Jira Cloud MCP Collection (`examples/collections/jira_mcp.json`)

- **Request ID 1**: `jira-get-current-user`
  - **Request Name**: `"Jira Get Current User"`
  - **Endpoint**: `GET {{ jira_base_url }}/rest/api/3/myself`
  - **Configured `hidden_response_fields`**:
    ```json
    "hidden_response_fields": [
      "emailAddress",
      "accountId"
    ]
    ```
  - **Demonstrated Patterns**: Direct bare key selectors masking Atlassian account PII (`emailAddress`)
    and immutable Atlassian user identity GUIDs (`accountId`).

- **Request ID 2**: `jira-search-assignable-users`
  - **Request Name**: `"Jira Search Assignable Users"`
  - **Endpoint**: `GET {{ jira_base_url }}/rest/api/3/user/assignable/search`
  - **Configured `hidden_response_fields`**:
    ```json
    "hidden_response_fields": [
      "[*].emailAddress",
      "[*].accountId"
    ]
    ```
  - **Demonstrated Patterns**: Root-level array wildcard paths (`[*].field`). Because Jira's assignable
    user search returns a top-level JSON array of user objects (`[{"accountId": "...", ...}]`),
    the `[*]` wildcard selector matches each element in the array, masking sensitive attributes
    across every returned user record while keeping user display names and active statuses visible.

##### Dual-Surface Presentation and Safety Guarantees

Every bundled collection request configured with `hidden_response_fields` enforces strict
dual-surface safety contracts:

1. **MCP Server Output Sanitization (`MCPServerImpl` / `McpResponseSanitizer`)**:
   - Irreversible masking: sensitive values matching configured selectors are replaced with `"***"`.
   - Tool schemas expose zero reveal parameters or bypass options to AI coding agents.
   - Prevents confidential tokens and user PII from leaking into agent prompt contexts, LLM completions,
     or persistent MCP logs.
2. **Desktop GUI Presentation (`ResponseView` / `ResponseMaskController`)**:
   - Interactive click-to-reveal: values are rendered as masked token spans with dashed underlines (`***`).
   - Clicking on a masked span toggles between revealed plain text and masked state.
   - Protects against accidental exposure during screen sharing, demos, and presentations.
3. **Pristine Data Model Immutability**:
   - Masking transforms only serialized text representations for presentation and agent egress.
   - Raw `ResponseData.body` and historical request logs remain intact in memory for test assertions
     and developer scripting.

##### Automated Contract Verification (`tests/test_reference_collection_masking_contract.py`)

To prevent regressions, ensure schema conformance, and guard against accidental removal of
sample masking configurations, PyPost executes automated contract tests under
`tests/test_reference_collection_masking_contract.py` (PYPOST-1395):

- **Collection Model Schema Conformance**: Verifies that `github_mcp.json`, `gitlab_mcp.json`,
  `jira_mcp.json`, and `google_drive.json` load cleanly via `read_collection_file` into PyPost's
  Pydantic `Collection` model (`version: "1.0.0"` or `"2.0.0"`).
- **Exact Field Configuration Assertions**: Asserts the exact presence of configured
  `hidden_response_fields` on target user-identity and search requests.
- **Round-Trip Serialization Fidelity**: Asserts that `collection.model_dump_json()` preserves
  `hidden_response_fields` arrays with exact fidelity across disk and memory round-trips.
- **MCP Wire Sanitization**: Asserts that executing tools against loopback responses permanently
  redacts all configured fields to `***` in MCP `TextContent` envelopes.
- **GUI Token Spans**: Asserts that loading responses into `ResponseView` creates active
  `MaskedTokenSpan` objects with valid start/end offsets and correct click-to-reveal toggle behavior.

#### Developer Testing and Verification Guide

Developers extending selector syntax, modifying response views, or altering MCP sanitization pipelines should follow this verification workflow:

1. **Run Reference Collection Masking Contract Tests**:
   ```bash
   make test PYTEST_ARGS="tests/test_reference_collection_masking_contract.py"
   ```
2. **Run Integration and Edge-Case Tests**:
   ```bash
   make test PYTEST_ARGS="tests/test_hidden_response_fields_integration_edge_cases.py"
   ```
3. **Run All Related Unit and Component Suites**:
   ```bash
   make test PYTEST_ARGS="tests/test_hidden_response_fields.py tests/test_mcp_response_masking.py tests/test_gui_response_view_click_to_reveal.py"
   ```
4. **Verify Reference Collection Integrity & Path Freshness**:
   ```bash
   make test PYTEST_ARGS="tests/test_collections.py -k test_google_drive"
   make check-github-mcp-path-freshness
   make check-gitlab-mcp-path-freshness
   make check-jira-mcp-path-freshness
   ```
5. **Execute Static Analysis and Quality Gates**:
   ```bash
   # Run flake8, documentation linters, and link checks
   make lint
   make lint-docs
   make check-docs-links

   # Run type checks against baseline
   make typecheck

   # Run complete automated repository quality gate
   make check
   ```

---

### 5. Unified JSON Selector Path Evaluation Engine (PYPOST-1394)

To eliminate duplicated AST traversal and pattern matching across `SensitiveTextSanitizer`
and `ResponseMaskController`, PYPOST-1394 extracted a centralized domain engine:
`pypost.core.json_selector_engine.JsonSelectorEngine`.

Key capabilities:
- **Pre-Compiled Rule Partitioning**: Partitions selectors into $O(1)$ bare field lookups (`_bare_keys`)
  and compiled path matchers (`CompiledPathSelector`), bypassing string allocations for non-matching nodes.
- **Unified Wildcard Semantics**: Standardizes wildcard handling (`items[*].secret`, `items.*.secret`,
  `[*].id`) across MCP and GUI pipelines.
- **Running Offset Tracking**: Replaces $O(M \times N)$ chunk summation in `JsonMaskFormatter` with an
  incremental $O(1)$ offset counter.
- **Zero UI Dependencies**: Lives in `pypost/core/` for safe execution in headless daemon and MCP environments.

For complete API specifications and code examples, see
[Unified JSON Selector Path Evaluation Engine](json_selector_engine.md).

---

### 6. Virtualized Hidden Fields Editor Table (PYPOST-1386 / PYPOST-1387)

Enterprise requests can configure hundreds or thousands of masking selectors. The original
`HiddenFieldsTable` subclassed `QTableWidget` and allocated a concrete item per row, which
slowed initial load and scrolling for large catalogs.

PYPOST-1386 moved the editor to Qt Model/View virtualization; PYPOST-1387 layered advisory
inline syntax validation on the same stack:

- **`HiddenFieldsTableModel`**: Owns `list[HiddenFieldRecord]` (including cached
  `FieldSelectorSyntaxResult`), trailing blank-row expansion, batch `set_data` /
  `remove_rows`, `BackgroundRole` / conditional `ToolTipRole`, and DEBUG structured logs
  (counts only; never selector text).
- **`HiddenFieldsTable(QTableView)`**: Viewport-virtualized presentation with preserved public
  API, lightweight `item(row, col).text()` facades, and `FieldSelectorDelegate` for live
  editor highlight/tooltip while typing.
- **`validate_field_selector`**: Pure core vocabulary check shared by model and delegate;
  validation is advisory — `get_data()` still returns invalid strings unchanged.
- **Caller contract**: `RequestEditor` still uses `set_data` / `get_data` / `add_row` /
  `remove_selected_rows` and the dual `data_changed` / `changed` signals — persistence and
  masking pipelines are untouched.

Verification:

```bash
make test PYTEST_ARGS="tests/test_hidden_fields_virtualization_repro.py"
make test PYTEST_ARGS="tests/test_request_hidden_fields_model_and_ui.py"
make test PYTEST_ARGS="tests/test_field_selector_syntax.py"
make test PYTEST_ARGS="tests/test_hidden_fields_syntax_validation_repro.py"
```

For architecture diagrams, API reference, syntax roles, and troubleshooting, see
[Virtualized Hidden Fields Table](hidden_fields_table.md).

---

## Comparison: GUI vs MCP Masking

| Dimension | GUI ResponseView | MCP Server Output |
| :--- | :--- | :--- |
| **Consumer** | Human developer via desktop GUI | External AI coding agent via MCP protocol |
| **Threat Model** | Visual observation, screen sharing, shoulder-surfing | Agent context ingestion, prompt injection, log leakage |
| **Reversibility** | **Reversible**: click-to-reveal toggle on demand | **Irreversible**: permanent redaction with `***` |
| **Reveal Capability** | Left-click on token span in `FoldableCodeView` | **None**: zero reveal parameters or tools |
| **Rendering** | Interactive `QPlainTextEdit` with syntax highlights | Formatted JSON string in MCP `TextContent` |
| **Underlying Data** | In-memory `ResponseData` remains unmutated | In-memory `ExecutionResult.response` remains unmutated |

---

## References

- Virtualized Hidden Fields Table: [`doc/dev/hidden_fields_table.md`](hidden_fields_table.md)
- Unified JSON Selector Engine: [`doc/dev/json_selector_engine.md`](json_selector_engine.md)
- Background Worker Thread Formatting for Medium JSON Responses: [`doc/dev/response_mask_worker.md`](response_mask_worker.md)
- ResponseMaskWorker Test Suite: [`tests/test_response_mask_worker.py`](../../tests/test_response_mask_worker.py)
- Hidden Fields Virtualization Repro: [`tests/test_hidden_fields_virtualization_repro.py`](../../tests/test_hidden_fields_virtualization_repro.py)
- Field Selector Syntax Tests: [`tests/test_field_selector_syntax.py`](../../tests/test_field_selector_syntax.py)
- Hidden Fields Syntax Validation Repro: [`tests/test_hidden_fields_syntax_validation_repro.py`](../../tests/test_hidden_fields_syntax_validation_repro.py)
- PYPOST-1386 Architecture Design: [`ai-tasks/PYPOST-1386/20-architecture.md`](../../ai-tasks/PYPOST-1386/20-architecture.md)
- PYPOST-1387 Architecture Design: [`ai-tasks/PYPOST-1387/20-architecture.md`](../../ai-tasks/PYPOST-1387/20-architecture.md)
- Reference Collection Masking Contract Tests: [`tests/test_reference_collection_masking_contract.py`](../../tests/test_reference_collection_masking_contract.py)
- Google Drive Reference Collection Fixture: [`examples/collections/google_drive.json`](../../examples/collections/google_drive.json)
- GitHub Reference Collection Fixture: [`examples/collections/github_mcp.json`](../../examples/collections/github_mcp.json)
- GitLab Reference Collection Fixture: [`examples/collections/gitlab_mcp.json`](../../examples/collections/gitlab_mcp.json)
- Jira Cloud Reference Collection Fixture: [`examples/collections/jira_mcp.json`](../../examples/collections/jira_mcp.json)
- GitHub MCP Example Collection: [`doc/dev/github_mcp_collection.md`](github_mcp_collection.md)
- GitLab MCP Example Collection: [`doc/dev/gitlab_mcp_collection.md`](gitlab_mcp_collection.md)
- Jira MCP Collection E2E: [`doc/dev/jira_mcp_collection_e2e.md`](jira_mcp_collection_e2e.md)
- Epic Decomposition Notes: [`ai-tasks/PYPOST-1312/decomposition-notes.md`](../../ai-tasks/PYPOST-1312/decomposition-notes.md)
- Step 2 Architecture Design: [`ai-tasks/PYPOST-1376/20-architecture.md`](../../ai-tasks/PYPOST-1376/20-architecture.md)
- PYPOST-1395 Architecture Design: [`ai-tasks/PYPOST-1395/20-architecture.md`](../../ai-tasks/PYPOST-1395/20-architecture.md)
- Sensitive Data Masking Policy: [`doc/dev/sensitive_data_masking_policy.md`](sensitive_data_masking_policy.md)
- RequestData Copy Policy: [`doc/dev/request_data_copy_policy.md`](request_data_copy_policy.md)
- MCP Integration Guide: [`doc/dev/mcp_integration.md`](mcp_integration.md)
- Integration & Edge-Case Tests: [`tests/test_hidden_response_fields_integration_edge_cases.py`](../../tests/test_hidden_response_fields_integration_edge_cases.py)
- MASK-4 Roadmap & Verification: [`ai-tasks/PYPOST-1380/00-roadmap.md`](../../ai-tasks/PYPOST-1380/00-roadmap.md)
- PYPOST-1395 Roadmap & Verification: [`ai-tasks/PYPOST-1395/00-roadmap.md`](../../ai-tasks/PYPOST-1395/00-roadmap.md)
- PYPOST-1396 Roadmap & Verification: [`ai-tasks/PYPOST-1396/00-roadmap.md`](../../ai-tasks/PYPOST-1396/00-roadmap.md)
