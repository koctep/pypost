# PYPOST-1366: JSON/YAML/XML code folding in WebSocket stream view

## Research

### Current State and Component Inventory

1. **`WebSocketStreamView` & `StreamDetailPane` (`pypost/ui/widgets/websocket/stream_view.py`)**:
   - `WebSocketStreamView` is a composite container containing:
     - Top filter toolbar (`search_input`, `dir_combo`, `kind_combo`, `heartbeats_check`,
       `pause_btn`, `clear_btn`, `export_btn`).
     - Match counter label (`WS_STREAM_MATCH_COUNT`).
     - Buffer drop notice banner (`WS_STREAM_DROP_NOTICE`).
     - Vertical splitter containing `_list_view` (`StreamItemDelegate`, `StreamFilterProxyModel`)
       and `_detail_pane` (`StreamDetailPane`).
   - `StreamDetailPane`:
     - Displays payload and metadata for the currently selected `StreamEntry`.
     - Action toolbar currently contains:
       - `_copy_btn` (`WS_STREAM_DETAIL_COPY_BUTTON`): Copies payload to clipboard with secret
         sanitization.
       - `_set_var_btn` (`WS_STREAM_DETAIL_SET_VAR_BUTTON`): Captures selected text or payload as a
         variable.
       - `_wrap_btn` (`WS_STREAM_DETAIL_WRAP_BUTTON`): Toggles word wrap between `WidgetWidth` and
         `NoWrap`.
       - `_hex_btn` (`WS_STREAM_DETAIL_HEX_BUTTON`): Toggles between formatted text payload and hex
         dump view (`_format_hex_dump`).
     - Display editor:
       - Currently instantiated as raw `QTextEdit`: `self._editor = QTextEdit(self)`.
       - Marked read-only: `self._editor.setReadOnly(True)`.
       - Lacks line numbers, gutter fold indicators, block folding, or fold controls.

2. **Existing Code Folding Architecture (`pypost/ui/widgets/fold/` & `FoldableCodeView`)**:
   - `FoldableCodeView` (`pypost/ui/widgets/foldable_code_view.py`):
     - Inherits from `QPlainTextEdit` and embeds `FoldController` and `LineNumberArea`.
     - Already used in `ResponseView` (`pypost/ui/widgets/response_view.py`) for HTTP response
       payload folding.
     - Exposes:
       - `fold_controller() -> FoldController`
       - `set_body_format(body_format: BodyFormat) -> None`
       - `body_format() -> BodyFormat`
       - `fold_all() -> None`
       - `unfold_all() -> None`
       - `reveal_block(block_number: int) -> None`
       - `setText(text: str)` / `setPlainText(text: str)`
       - `update_indent_size(new_size: int)`
     - Gutter interactions:
       - `line_number_area_paint_event`: Draws line numbers and fold chevrons (`▼` expanded,
         `▶` collapsed).
       - `line_number_area_mouse_press`: Single click within `_CHEVRON_WIDTH` toggles the fold
         header block.
   - `FoldController` (`pypost/ui/widgets/fold/fold_controller.py`):
     - Manages region hierarchy, collapsed state set (`_collapsed_ids`), block visibility via
       `QTextBlock.setVisible(False/True)`.
     - Provides `fold_all()` (`collapse_all()`), `unfold_all()` (`expand_all()`), `toggle()`,
       `reveal_block()`, and `ensure_scanned()`.
     - Debounces structural scans on `document().contentsChanged` (or immediate via
       `ensure_scanned()`).
   - `FormatDetector` (`pypost/ui/widgets/fold/format_detector.py`):
     - `detect_body_format(headers, body) -> BodyFormat`: Analyzes Content-Type headers or applies
       syntax heuristics for JSON, XML, and YAML, falling back to `BodyFormat.PLAIN`.

3. **Gaps and Opportunities for Stream Detail Inspection**:
   - In `StreamDetailPane`:
     - Replacing `self._editor = QTextEdit(self)` with `FoldableCodeView(self)` gives immediate
       gutter line numbers and fold structure parsing.
     - Payload format detection: When `set_entry()` is invoked with a `StreamEntry`, detect
       whether the payload is JSON, YAML, XML, or PLAIN (using heuristics from
       `detect_body_format`).
     - Gutter interaction: While `FoldableCodeView` already has single-click chevron folding,
       adding double-click support on the gutter or fold header block fulfills requirement DoD 3.
     - Toolbar actions: Add "Fold All" and "Unfold All" toolbar buttons (or dropdown / context
       menu) with widget IDs `WS_STREAM_DETAIL_FOLD_ALL_BUTTON` and
       `WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON`.
     - Mode interactions:
       - Hex mode: When hex mode is toggled ON, set body format to `BodyFormat.PLAIN` and disable
         folding buttons to avoid invalid fold scans on hex dump lines. When hex mode is toggled
         OFF, re-detect payload format and re-enable folding.
       - Wrap mode: `FoldableCodeView` uses `QPlainTextEdit.LineWrapMode.WidgetWidth` vs `NoWrap`.
         Toggling wrap preserves folding state seamlessly because block visibility operates on
         logical `QTextBlock` elements independent of visual line wrapping.
       - Live streaming & selection: When new messages arrive while follow-tail is active,
         `set_entry()` refreshes `_editor`. Each payload selection initializes cleanly with
         expanded state (or scans structure immediately).

---

## Implementation Plan

### 1. Failing Repro Test (Step 3)

- **Test file**: `tests/test_websocket_stream_view_folding.py`
- **Objective**: Write comprehensive automated red repro tests validating the required folding
  capabilities in `StreamDetailPane` and `WebSocketStreamView` before applying implementation
  changes in Step 4.
- **Assertions**:
  1. `test_detail_pane_uses_foldable_code_view`: Asserts `pane._editor` is an instance of
     `FoldableCodeView` and provides `fold_controller()`, `fold_all()`, and `unfold_all()`.
  2. `test_json_payload_detected_and_folded`: Asserts setting a JSON `StreamEntry` detects
     `BodyFormat.JSON`, discovers fold regions, and allows collapsing/expanding blocks.
  3. `test_yaml_and_xml_payload_folding`: Asserts setting YAML and XML stream entries detects
     their respective formats and generates fold regions.
  4. `test_plain_and_binary_payload_no_folding`: Asserts plain text or binary frames produce no
     fold regions and default to `BodyFormat.PLAIN`.
  5. `test_fold_all_and_unfold_all_toolbar_buttons`: Asserts the presence and functionality of
     "Fold All" and "Unfold All" buttons in the detail pane toolbar.
  6. `test_hex_mode_disables_folding`: Asserts toggling Hex mode suppresses fold regions and
     disables fold buttons; toggling back restores format detection.
  7. `test_word_wrap_toggle_preserves_folding`: Asserts toggling word wrap switches wrap mode
     without disrupting collapsed fold regions.
  8. `test_gutter_double_click_folding`: Asserts double-clicking on fold headers or gutter toggles
     fold state.
  9. `test_streaming_follow_tail_updates_detail_safely`: Asserts rapid streaming entry updates do
     not throw exceptions or corrupt fold controller state.
- **Isolation**: Pure in-memory Qt unit tests using `StreamListModel` and mock `StreamEntry`
  instances with no live network dependencies.
- **Sequencing**:
  - Run Step 3 test -> Fails (currently `StreamDetailPane` uses `QTextEdit` and lacks fold buttons).
  - Proceed to Step 4 implementation -> Passes green.

### 2. Implementation Steps (Step 4)

1. **Widget IDs (`pypost/ui/widget_ids.py`)**:
   - Define `WS_STREAM_DETAIL_FOLD_ALL_BUTTON = "pypost_ws_stream_detail_fold_all_button"`.
   - Define `WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON = "pypost_ws_stream_detail_unfold_all_button"`.
   - Add constants to `__all__` export list.

2. **FoldableCodeView Enhancements (`pypost/ui/widgets/foldable_code_view.py`)**:
   - Ensure `mouseDoubleClickEvent` and `line_number_area_mouse_double_click` cleanly support
     toggling the fold block under the cursor when double-clicked.
   - Verify `setLineWrapMode` seamlessly switches between `WidgetWidth` and `NoWrap`.

3. **StreamDetailPane Integration (`pypost/ui/widgets/websocket/stream_view.py`)**:
   - Replace `QTextEdit` display editor with `FoldableCodeView`.
   - Add "Fold All" and "Unfold All" buttons to detail pane toolbar.
   - In `set_entry()`:
     - Detect payload format via `detect_body_format(None, entry.payload)`.
     - Set format on `FoldableCodeView`.
     - Update button enabled states (disabled for plain text or hex mode).
   - In `_render_payload()`:
     - If hex mode: render hex dump, set `BodyFormat.PLAIN`, disable fold buttons.
     - If normal text mode: detect format, render payload, call `ensure_scanned()`.
   - Connect Fold All / Unfold All button clicks to `_editor.fold_all()` and
     `_editor.unfold_all()`.

4. **Context Menu Actions**:
   - Support right-click context menu in `FoldableCodeView` containing Copy, Select All, Set
     Variable, Fold All, and Unfold All.

5. **Quality Verification**:
   - Execute `make check` to ensure tests, lint, and types pass cleanly.

---

## Architecture

### Component Structure Diagram

```mermaid
graph TD
    subgraph WebSocketStreamView
        FilerBar[Stream Filter Toolbar]
        Splitter[Splitter]
        ListView[Stream QListView]
        ProxyModel[StreamFilterProxyModel]
        DetailPane[StreamDetailPane]
    end

    subgraph DetailPaneSubcomponents[StreamDetailPane Components]
        HeaderLayout[Metadata & Truncation Labels]
        ToolbarLayout[Action Toolbar: Copy / SetVar / Wrap / Hex / FoldAll / UnfoldAll]
        FCV[FoldableCodeView (QPlainTextEdit)]
        Gutter[LineNumberArea (Gutter Widget)]
        FC[FoldController]
        FD[FormatDetector (detect_body_format)]
    end

    Splitter --> ListView
    Splitter --> DetailPane
    ListView --> ProxyModel
    DetailPane --> HeaderLayout
    DetailPane --> ToolbarLayout
    DetailPane --> FCV
    FCV --> Gutter
    FCV --> FC
    DetailPane --> FD
```

### Module Responsibilities and Interfaces

#### 1. `StreamDetailPane` (`pypost/ui/widgets/websocket/stream_view.py`)
- **Responsibility**: Hosts metadata header, action toolbar, and code viewer for selected message.
- **Interfaces**:
  - `set_entry(entry: Optional[StreamEntry]) -> None`
  - `current_entry -> Optional[StreamEntry]`
  - `is_wrap_mode -> bool`
  - `is_hex_mode -> bool`
  - Signals: `variable_capture_requested(str, str)`

#### 2. `FoldableCodeView` (`pypost/ui/widgets/foldable_code_view.py`)
- **Responsibility**: Read-only code editor with gutter line numbers, fold chevrons, and folding.
- **Interfaces**:
  - `fold_controller() -> FoldController`
  - `fold_all() -> None`
  - `unfold_all() -> None`
  - `reveal_block(block_number: int) -> None`
  - `set_body_format(body_format: BodyFormat) -> None`
  - `body_format() -> BodyFormat`

#### 3. `FoldController` (`pypost/ui/widgets/fold/fold_controller.py`)
- **Responsibility**: Parses AST fold regions and toggles block visibility.
- **Interfaces**:
  - `regions() -> list[FoldRegion]`
  - `is_collapsed(region_id: str) -> bool`
  - `toggle(region_id: str) -> None`
  - `collapse_all() -> None` / `fold_all() -> None`
  - `expand_all() -> None` / `unfold_all() -> None`
  - `ensure_scanned() -> None`

#### 4. `FormatDetector` (`pypost/ui/widgets/fold/format_detector.py`)
- **Responsibility**: Identifies structured syntax (JSON, YAML, XML, PLAIN) using heuristics.
- **Interfaces**:
  - `detect_body_format(headers: dict[str, str] | None, body: str) -> BodyFormat`

#### 5. `LineNumberArea` (`pypost/ui/widgets/line_number_area.py`)
- **Responsibility**: Gutter widget rendering line numbers and chevrons, delegating to editor.
- **Interfaces**:
  - `paintEvent(event: QPaintEvent)`
  - `mousePressEvent(event: QMouseEvent)`
  - `mouseDoubleClickEvent(event: QMouseEvent)`

### Lifecycle of Stream Message Folding

1. **Selection or Stream Arrival**:
   - `WebSocketStreamView._on_selection_changed` fires when the user selects a row or when
     follow-tail auto-selects the latest message.
   - `StreamDetailPane.set_entry(entry)` receives the `StreamEntry`.
2. **Format Detection & Rendering**:
   - If `entry` is None: editor cleared, format set to `BodyFormat.PLAIN`.
   - If `is_hex_mode` is True: hex dump formatted, format set to `PLAIN`, fold buttons disabled.
   - If `is_hex_mode` is False:
     - `detect_body_format(None, entry.payload)` determines syntax type.
     - `_editor.set_body_format(detected_format)` sets parser mode.
     - `_editor.setPlainText(entry.payload)` updates document text.
     - `_editor.fold_controller().ensure_scanned()` executes structural parsing.
     - If format in `(JSON, YAML, XML)`: "Fold All" and "Unfold All" buttons enabled.
     - Else: fold buttons disabled.
3. **User Interaction**:
   - Gutter click or double-click on fold header toggles block visibility via `FC.toggle()`.
   - "Fold All" collapses all detected hierarchical blocks.
   - "Unfold All" expands all blocks back to full visibility.
   - "Wrap" toggles line wrapping between `WidgetWidth` and `NoWrap` without changing fold states.
   - "Copy" extracts payload or selected text without mutation.

---

## Q&A

**Q: Why use `FoldableCodeView` rather than `CodeEditor`?**  
**A:** `CodeEditor` includes complex editing features such as auto-completion, variable insertion,
indentation keybindings, and validation banners, which are unnecessary and risky in a read-only
stream inspection view. `FoldableCodeView` is already designed for read-only code viewing with
clean gutter line numbers and fold controllers (as proven in `ResponseView`).

**Q: How does folding interact with Hex view mode?**  
**A:** Hex view formats raw bytes into offset/hex/ASCII columns, which do not conform to JSON, YAML,
or XML grammar. When Hex mode is activated, format detection is set to `PLAIN`, folding is
suppressed, and fold buttons are disabled. When switched back to text view, folding is restored.

**Q: Will code folding slow down message streaming during high throughput?**  
**A:** No. Folding is only processed for the single message currently displayed in the detail pane.
Messages streaming in the background or appending to `MessageStream` do not trigger fold scanning
unless selected. Furthermore, fold scanning is debounced or executed synchronously only on
selection.

**Q: Does toggling word wrap affect active fold regions?**  
**A:** No. Folding controls logical `QTextBlock` visibility in Qt's document model. Word wrapping
only alters how visible blocks reflow inside the viewport.
