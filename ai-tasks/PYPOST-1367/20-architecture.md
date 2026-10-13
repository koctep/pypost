# PYPOST-1367: JSON/YAML/XML code folding in MCP result view

## Research

### Current State and Component Inventory

1. **`McpResultView` (`pypost/ui/widgets/mcp_client/mcp_result_view.py`)**:
   - `McpResultView` is the result inspection pane hosted inside `McpClientTab`
     (`pypost/ui/widgets/mcp_client/mcp_client_tab.py`).
   - Layout & sub-widgets:
     - Header label: `QLabel("Result", self)`
     - Progress label: `_progress = QLabel("", self)` (displays "Invoking..." when in-flight)
     - Elapsed label: `_elapsed = QLabel("", self)` with ID `MCP_CLIENT_ELAPSED_LABEL`
     - Content viewer: `_body = QPlainTextEdit(self)` with ID `MCP_CLIENT_RESULT_PANE`
   - Current API:
     - `set_in_progress()`: Clears elapsed and body text, sets progress label to "Invoking...".
     - `set_result(payload: dict[str, Any], elapsed_s: float, *, is_error: bool)`:
       Extracts content blocks and optional `structuredContent`, formats lines, calls
       `sanitize_text("\n".join(lines))`, and populates `_body.setPlainText(...)`.
     - `set_error(message: str, elapsed_s: float | None)`: Displays transport or validation error.
     - `clear()`: Clears progress, elapsed, and body text.
   - Current limitations:
     - Uses standard `QPlainTextEdit` without gutter, line numbers, or code folding.
     - Does not detect payload format (JSON, YAML, XML, or PLAIN).
     - Lacks "Fold All" and "Unfold All" controls.

2. **Existing Code Folding Architecture (`pypost/ui/widgets/foldable_code_view.py` & `fold/`)**:
   - `FoldableCodeView` (`pypost/ui/widgets/foldable_code_view.py`):
     - Subclasses `QPlainTextEdit` with an attached `LineNumberArea` gutter and `FoldController`.
     - Already used in `ResponseView` (`pypost/ui/widgets/response_view.py`) and `StreamDetailPane`
       (`pypost/ui/widgets/websocket/stream_view.py`).
     - Public API:
       - `fold_controller() -> FoldController`
       - `set_body_format(body_format: BodyFormat) -> None`
       - `body_format() -> BodyFormat`
       - `fold_all() -> None`
       - `unfold_all() -> None`
       - `reveal_block(block_number: int) -> None`
       - `setText(text: str)` / `setPlainText(text: str)`
       - `update_indent_size(new_size: int)`
     - Gutter interactions:
       - Single-click within `_CHEVRON_WIDTH` (`line_number_area_mouse_press`) toggles region.
       - Double-click on gutter (`line_number_area_mouse_double_click`) toggles region across
         the full gutter width (`require_chevron_zone=False`).
       - Chevrons drawn: `\u25b6` (`▶`) when collapsed, `\u25bc` (`▼`) when expanded.
   - `FoldController` (`pypost/ui/widgets/fold/fold_controller.py`):
     - Manages hierarchical `FoldRegion` models, collapsed region ID set (`_collapsed_ids`),
       and block visibility toggling (`QTextBlock.setVisible(False/True)`).
     - Provides `fold_all()` / `collapse_all()`, `unfold_all()` / `expand_all()`, `toggle()`,
       `reveal_block()`, and immediate sync via `ensure_scanned()`.
   - `FormatDetector` (`pypost/ui/widgets/fold/format_detector.py`):
     - `detect_body_format(headers: dict[str, str] | None, body: str) -> BodyFormat`:
       Detects JSON, YAML, and XML via Content-Type headers and syntax heuristics, falling back
       to `BodyFormat.PLAIN`.
   - `StructureScanner` implementations:
     - `JsonStructureScanner`, `YamlStructureScanner`, `XmlStructureScanner` parse blocks.

3. **Gaps and Opportunities in MCP Result View**:
   - Upgrading `McpResultView._body` from `QPlainTextEdit` to `FoldableCodeView`:
     - Retains `QPlainTextEdit` inheritance, preserving `MCP_CLIENT_RESULT_PANE` lookup and
       all existing API contracts (`setPlainText`, `toPlainText`, `isReadOnly`).
     - Adds line numbers and collapsible gutters out of the box.
   - Toolbar integration:
     - Place a horizontal action bar above or alongside the result header containing:
       - Header label ("Result")
       - Elapsed label (`MCP_CLIENT_ELAPSED_LABEL`)
       - "Fold All" button (`MCP_CLIENT_RESULT_FOLD_ALL_BUTTON`)
       - "Unfold All" button (`MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON`)
   - Syntax detection and fallback:
     - Run `detect_body_format(None, sanitized_text)` on incoming result payload.
     - If structured format (JSON, YAML, XML), apply `_body.set_body_format(...)`, trigger
       `ensure_scanned()`, and enable fold buttons.
     - If unstructured/plain text (or errors), set `BodyFormat.PLAIN` and disable fold buttons.
     - Non-destructive: `toPlainText()` and clipboard operations retain full underlying text.

---

## Implementation Plan

### 1. Failing Repro Test (Step 3)

- **Test file**: `tests/test_mcp_result_view_folding.py`
- **Objective**: Write comprehensive automated red repro tests validating the required folding
  capabilities in `McpResultView` before writing implementation code in Step 4.
- **Assertions**:
  1. `test_mcp_result_view_uses_foldable_code_view`:
     Asserts `_body` is an instance of `FoldableCodeView` with widget ID
     `MCP_CLIENT_RESULT_PANE` and exposes `fold_controller()`, `fold_all()`, and `unfold_all()`.
  2. `test_json_mcp_result_detected_and_folded`:
     Asserts passing a JSON tool execution payload detects `BodyFormat.JSON`, discovers fold
     regions, and allows collapsing/expanding blocks via `fold_all()` and `unfold_all()`.
  3. `test_yaml_and_xml_mcp_results_folding`:
     Asserts tool text blocks containing valid YAML or XML detect `BodyFormat.YAML` and
     `BodyFormat.XML`, creating fold regions.
  4. `test_plain_and_unstructured_mcp_results_no_folding`:
     Asserts plain text or unstructured strings result in `BodyFormat.PLAIN` with zero fold
     regions, keeping fold buttons disabled.
  5. `test_fold_all_and_unfold_all_buttons`:
     Asserts presence and functionality of "Fold All" (`MCP_CLIENT_RESULT_FOLD_ALL_BUTTON`)
     and "Unfold All" (`MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON`) buttons in `McpResultView`.
  6. `test_gutter_double_click_folding`:
     Asserts sending a mouse double-click event to `LineNumberArea` on a fold header block
     toggles block collapsed state.
  7. `test_error_result_displays_plain_text`:
     Asserts `set_error()` or `is_error=True` with error message displays cleanly as
     `BodyFormat.PLAIN` without folding anomalies.
  8. `test_clear_and_in_progress_resets_folding`:
     Asserts calling `set_in_progress()` or `clear()` empties text and resets fold controller.
- **Isolation**: Pure in-memory Qt unit tests with mock payloads; no external network or server
  dependencies.
- **Sequencing**:
  - Run Step 3 test -> Fails (currently `McpResultView` uses `QPlainTextEdit` and lacks fold
    buttons/format detection).
  - Proceed to Step 4 implementation -> Passes green.

### 2. Implementation Steps (Step 4)

1. **Widget IDs (`pypost/ui/widget_ids.py`)**:
   - Define `MCP_CLIENT_RESULT_FOLD_ALL_BUTTON = "pypost_mcp_client_result_fold_all_button"`.
   - Define `MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON = "pypost_mcp_client_result_unfold_all_button"`.
   - Export constants in `__all__`.

2. **McpResultView Refactoring (`pypost/ui/widgets/mcp_client/mcp_result_view.py`)**:
   - Replace `self._body = QPlainTextEdit(self)` with `FoldableCodeView(self)`.
   - Add "Fold All" and "Unfold All" buttons connected to `_body.fold_all()` and
     `_body.unfold_all()`.
   - In `set_result()`:
     - Assemble sanitized result text.
     - Call `detect_body_format(None, text)` to identify payload syntax.
     - Update `_body.set_body_format(detected_format)`.
     - Populate `_body.setPlainText(text)`.
     - Call `_body.fold_controller().ensure_scanned()`.
     - Enable or disable "Fold All" and "Unfold All" buttons based on detected format.
   - In `set_error()`, `set_in_progress()`, and `clear()`:
     - Set format to `BodyFormat.PLAIN` and disable fold buttons.

3. **Regression and Quality Verification**:
   - Run existing MCP client tests (`tests/test_mcp_client_tab.py`).
   - Run new red repro test (`tests/test_mcp_result_view_folding.py`).
   - Run quality gate checks via `make check`.

---

## Architecture

### Component Structure Diagram

```mermaid
graph TD
    subgraph McpClientTab
        ConnBar[Connection Bar]
        ToolBrowser[Tool Browser]
        InvokeForm[Tool Invoke Form]
        ResultView[McpResultView]
    end

    subgraph McpResultViewComponents[McpResultView Components]
        HeaderBar[Header & Toolbar Layout]
        HeaderLabel[Result Label]
        ProgressLabel[Progress Label]
        ElapsedLabel[MCP_CLIENT_ELAPSED_LABEL]
        FoldAllBtn[MCP_CLIENT_RESULT_FOLD_ALL_BUTTON]
        UnfoldAllBtn[MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON]
        FCV[FoldableCodeView (MCP_CLIENT_RESULT_PANE)]
        Gutter[LineNumberArea Gutter]
        FC[FoldController]
        FD[detect_body_format]
    end

    ResultView --> HeaderBar
    HeaderBar --> HeaderLabel
    HeaderBar --> ProgressLabel
    HeaderBar --> ElapsedLabel
    HeaderBar --> FoldAllBtn
    HeaderBar --> UnfoldAllBtn
    ResultView --> FCV
    FCV --> Gutter
    FCV --> FC
    ResultView --> FD
```

### Module Responsibilities and Interfaces

#### 1. `McpResultView` (`pypost/ui/widgets/mcp_client/mcp_result_view.py`)
- **Responsibility**: Hosts result header, elapsed time, fold buttons, and `FoldableCodeView`.
- **Public Interfaces**:
  - `set_in_progress() -> None`
  - `set_result(payload: dict[str, Any], elapsed_s: float, *, is_error: bool) -> None`
  - `set_error(message: str, elapsed_s: float | None) -> None`
  - `clear() -> None`
  - `body_view() -> FoldableCodeView` (or direct access via `_body`)
  - `fold_all() -> None`
  - `unfold_all() -> None`

#### 2. `FoldableCodeView` (`pypost/ui/widgets/foldable_code_view.py`)
- **Responsibility**: Code viewer widget subclassing `QPlainTextEdit` with gutter line numbers,
  chevrons, and folding controllers.
- **Interfaces**:
  - `fold_controller() -> FoldController`
  - `fold_all() -> None`
  - `unfold_all() -> None`
  - `set_body_format(body_format: BodyFormat) -> None`
  - `body_format() -> BodyFormat`
  - `setPlainText(text: str) -> None`
  - `toPlainText() -> str`

#### 3. `FoldController` (`pypost/ui/widgets/fold/fold_controller.py`)
- **Responsibility**: Manages AST fold regions and toggles block visibility.
- **Interfaces**:
  - `regions() -> list[FoldRegion]`
  - `is_collapsed(region_id: str) -> bool`
  - `toggle(region_id: str) -> None`
  - `collapse_all() -> None` / `fold_all() -> None`
  - `expand_all() -> None` / `unfold_all() -> None`
  - `ensure_scanned() -> None`

#### 4. `FormatDetector` (`pypost/ui/widgets/fold/format_detector.py`)
- **Responsibility**: Detects JSON, YAML, and XML syntax structures via heuristics.
- **Interfaces**:
  - `detect_body_format(headers: dict[str, str] | None, body: str) -> BodyFormat`

### Interaction Flow

1. User executes an MCP tool via the invoke form.
2. `McpResultView.set_in_progress()` displays "Invoking...", clears previous text, and sets format
   to `BodyFormat.PLAIN`.
3. Tool execution completes, invoking `McpResultView.set_result(payload, elapsed_s, is_error=...)`.
4. Result text is formatted and sanitized.
5. Format detection identifies syntax type (`JSON`, `YAML`, `XML`, or `PLAIN`).
6. Payload text is loaded into `FoldableCodeView`. If structured format is detected:
   - Line numbers and fold chevrons appear in the gutter.
   - "Fold All" and "Unfold All" buttons are enabled.
   - Single-click or double-click in gutter toggles target blocks.
   - "Fold All" / "Unfold All" collapses / expands entire document hierarchy.
7. If unstructured text or error is displayed:
   - Format is set to `PLAIN`.
   - Fold buttons are disabled.
   - Text renders cleanly without fold chevrons.

---

## Q&A

**Q: Why use `FoldableCodeView` rather than writing custom folding logic for MCP?**  
**A:** `FoldableCodeView` is already battle-tested across HTTP `ResponseView` and WebSocket
`StreamDetailPane`. Reusing it guarantees consistent visual styling, gutter mechanics, and
keyboard/mouse interaction standards across the entire application.

**Q: How are mixed-content MCP payloads handled (e.g. text blocks + structuredContent)?**  
**A:** The payload formatter serializes structured data into formatted blocks.
`detect_body_format` detects JSON or YAML formatting within the resulting text. Even if a
payload contains prefix text, the scanner and format heuristics accommodate valid structured
blocks, falling back gracefully to `BodyFormat.PLAIN` if the syntax is irregular.

**Q: Does folding affect copying or data extraction?**  
**A:** No. Folding manipulates visual `QTextBlock.setVisible(False/True)` within the Qt layout
engine. Underlying text buffer contents in `QTextDocument` remain untouched, ensuring standard
selection and clipboard copy actions preserve full output data.

**Q: Does double-clicking in the gutter toggle folding?**  
**A:** Yes. `FoldableCodeView` handles double-clicks via `line_number_area_mouse_double_click`,
which toggles the fold block under the cursor across the full gutter width without requiring
exact chevron alignment.
