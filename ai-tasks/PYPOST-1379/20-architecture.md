# PYPOST-1379: [PYPOST-1312] Interactive click-to-reveal response masking in GUI ResponseView

Step 2 artifact for PYPOST-1379 (MASK-3). Translates approved requirements from
[`10-requirements.md`](10-requirements.md), parent epic architecture from
[`../PYPOST-1376/20-architecture.md`](../PYPOST-1376/20-architecture.md), and foundational specifications
from [`../PYPOST-1377/20-architecture.md`](../PYPOST-1377/20-architecture.md) (MASK-1 model) and
[`../PYPOST-1378/20-architecture.md`](../PYPOST-1378/20-architecture.md) (MASK-2 MCP) into a concrete,
production-grade architectural design for interactive click-to-reveal response masking in the desktop GUI.

---

## Research

### 1. Existing GUI Codebase Analysis

#### 1.1 `ResponseView` ([`pypost/ui/widgets/response_view.py`](file:///home/src/pypost/ui/widgets/response_view.py))
- **Structure & Layout**:
  - Encapsulates a top status/search bar layout (`self.status_layout`) and the main response body widget `self.body_view: FoldableCodeView`.
  - Top bar contains:
    - Status labels (`status_label`, `time_label`, `size_label`).
    - Integrated search controls (`search_input`, `search_prev_btn`, `search_next_btn`, `search_case_cb`, `search_status_label`).
    - Code folding toolbar actions (`fold_all_btn`, `unfold_all_btn`).
- **Body Rendering Pipeline (`display_response`)**:
  - `display_response(self, response: ResponseData)`:
    - Extracts `body_str` (decodes `bytes` to `str` if needed).
    - Detects content type via `detect_body_format(response.headers, body_str)`.
    - If `detected_format == BodyFormat.JSON`, binds `self.json_highlighter.setDocument(self.body_view.document())`; otherwise unbinds highlighter (`setDocument(None)`).
    - If `len(body_str) > LARGE_DOC_CHAR_THRESHOLD` (100 KB), skips formatting and sets raw text directly via `self.body_view.setText(body_str)`.
    - If `len(body_str) <= LARGE_DOC_CHAR_THRESHOLD` and format is JSON, parses via `json.loads(body_str)` and pretty-prints via `json.dumps(parsed, indent=self.indent_size)`.
    - Calls `self.body_view.fold_controller().ensure_scanned()` to index fold regions.
- **Mouse & Context Menu Handling**:
  - Context menu policy is set to `Qt.CustomContextMenu`.
  - Right-click emits `customContextMenuRequested`, triggering `show_context_menu(pos)`.
  - `show_context_menu`:
    - Reads `cursor = self.body_view.textCursor()`, `selected_text = cursor.selectedText().strip()`.
    - If text is selected and `self.current_env_keys` is set, constructs a `"Set Variable"` submenu listing existing environment keys plus `"New Variable..."`.
    - Choosing an item triggers `self.variable_set_requested.emit(key, selected_text)`.
    - Adds standard `"Copy"` (connected to `self.body_view.copy`) and `"Select All"` (`self.body_view.selectAll`).
    - If fold regions exist, appends `"Fold All"` and `"Unfold All"`.

#### 1.2 `FoldableCodeView` ([`pypost/ui/widgets/foldable_code_view.py`](file:///home/src/pypost/ui/widgets/foldable_code_view.py))
- **Inheritance & Gutter**:
  - Inherits from `QPlainTextEdit` with `LineWrapMode.NoWrap`.
  - Hosts `LineNumberArea` gutter on the left margin, rendering line numbers and fold chevrons (`\u25b6` collapsed, `\u25bc` expanded).
  - Handles gutter mouse clicks (`line_number_area_mouse_press`, `line_number_area_mouse_double_click`) to toggle code folding blocks.
- **Viewport & Text Manipulation**:
  - Main text area is `self.viewport()`.
  - `self.isReadOnly()` is set to `True`.
  - Important Qt characteristic: In `QPlainTextEdit`, programmatic text replacement via `QTextCursor` (`cursor.setPosition(...)`, `cursor.insertText(...)`) succeeds even when `isReadOnly()` is `True`. Read-only blocks user typing from keyboard, but programmatic operations remain fully supported.
  - Does not override `mousePressEvent`, `mouseReleaseEvent`, or `mouseMoveEvent` on the main text area, leaving mouse handling on the viewport open for event filtering or delegation.

#### 1.3 `JsonHighlighter` ([`pypost/ui/widgets/json_highlighter.py`](file:///home/src/pypost/ui/widgets/json_highlighter.py))
- **Highlighting Mechanism**:
  - Subclasses `QSyntaxHighlighter` and executes `highlightBlock(text)` per `QTextBlock`.
  - Uses regex rules for keywords (`true`, `false`, `null`), numbers, string literals (`r'"[^"\\]*(\\.[^"\\]*)*"'`), object keys (`r'("[^"\\]*(\\.[^"\\]*)*")\s*:'`), and template placeholders (`TEMPLATE_PLACEHOLDER_PATTERN`).
- **Coexistence Guarantee**:
  - Masked values formatted as `"***"` match the standard string literal pattern `r'"[^"\\]*(\\.[^"\\]*)*"'`. They are tokenized cleanly as string literals without regex failure or syntax corruption.
  - Programmatic text replacement via `QTextCursor.insertText()` causes Qt's document layout engine to automatically re-highlight the modified block.
  - No recursive re-highlighting loops occur because `JsonHighlighter` does not modify the document during `highlightBlock()`.

#### 1.4 Search Navigation and Match Counting
- **Search Engine**:
  - `_find_next()` and `_find_previous()` invoke `self.body_view.find(text, flags)` and reveal collapsed blocks via `self.body_view.reveal_block(cursor.blockNumber())`.
  - `_count_matches()` and `_current_match_index()` iterate through `self.body_view.document().find(text, cursor, flags)`.
- **Coexistence with Masked / Revealed Text**:
  - Because search operates directly on the underlying `QTextDocument`, searching finds whatever text is currently rendered in the document.
  - When masked, searching for `"***"` matches masked fields; searching for an unmasked secret yields zero matches.
  - When revealed, the unmasked secret is physically present in the `QTextDocument`, making it immediately searchable.
  - When a token is toggled, updating `_update_match_count()` keeps the match indicator ("1 of 3 matches") strictly synchronized without index drift.

#### 1.5 Code Folding Mechanics
- **`FoldController` ([`pypost/ui/widgets/fold/fold_controller.py`](file:///home/src/pypost/ui/widgets/fold/fold_controller.py))**:
  - Discovers fold regions based on braces `{}` / brackets `[]` and indentation levels.
  - Toggling a single-line scalar string (e.g. `"***"` <-> `"my-secret-key"`) alters the character length of the line, but does not alter line count, brace structure, or indentation. All fold regions remain structurally intact.
  - If a multiline structure is revealed (or re-masked), calling `self.body_view.fold_controller().ensure_scanned()` automatically re-indexes fold regions for the new line count.

#### 1.6 Streaming Chunk Appending (`append_body`)
- **Streaming Pipeline**:
  - During streaming execution, chunks arrive asynchronously and `tabs_presenter_worker.py` routes them to `ResponseView.append_body(chunk)`.
  - `append_body` moves the cursor to `QTextCursor.End` and calls `insertPlainText(chunk)`.
  - Masking must not attempt to parse incomplete JSON chunks mid-stream.
  - When the request completes, `tabs_presenter_worker._on_request_finished` invokes `display_response(response, hidden_fields=...)`, cleanly replacing the appended text with the fully formatted, masked JSON document.

#### 1.7 Large-Document Fallback
- **Threshold**: `LARGE_DOC_CHAR_THRESHOLD = 100 * 1024` (100 KB).
- **Fallback Strategy**:
  - If `len(body_str) > LARGE_DOC_CHAR_THRESHOLD`, `display_response` logs `display_response_skip_pretty_print` and bypasses pretty-printing, complex AST parsing, and token span tracking.
  - The raw body text is passed directly to `self.body_view.setText(body_str)`.
  - This ensures that payloads of several megabytes do not stall or freeze the GUI event loop.

---

### 2. Design of the MaskedTokenSpan & Click-to-Reveal Model

#### 2.1 Masked Token Span Data Structure
A lightweight dataclass `MaskedTokenSpan` tracks the state and coordinate boundaries of each masked token in the `QTextDocument`:

```python
@dataclass
class MaskedTokenSpan:
    start_pos: int          # Absolute character start offset in QTextDocument
    end_pos: int            # Absolute character end offset in QTextDocument
    raw_value: str          # Serialized unmasked JSON text (e.g. '"secret_token_123"' or '1234')
    masked_value: str = '"***"'  # Serialized masked placeholder text
    is_revealed: bool = False    # Current presentation state
    path: str = ""          # JSON dot-notation selector path (for debugging/metrics)
```

#### 2.2 Formatting and Span Detection
To ensure 100% selector consistency between the MCP security boundary (MASK-2) and GUI presentation (MASK-3), span detection utilizes the same path variant resolution logic from `pypost.core.sensitive_text_sanitizer.format_path_variants`:
- Simple keys: `"token"`, `"password"`, `"api_key"`.
- Dot-notation paths: `"data.user.secret"`, `"auth.token"`.
- Array wildcards: `"items[*].token"`, `"users.email"`.

A dedicated `JsonMaskFormatter` walks the parsed JSON structure while emitting pretty-printed text with `indent=self.indent_size`. Because it builds the output buffer incrementally, it records the exact `start_pos` and `end_pos` of each masked field at the moment of emission:
1. When a node matches a selector, it emits `'"***"'` and records `start_pos = current_offset`, `end_pos = current_offset + 5`.
2. It serializes the authentic value using `json.dumps(val, indent=indent, ensure_ascii=False)` and stores it in `raw_value`.
3. Returns `(formatted_text, spans)`.

#### 2.3 Visual Affordance via `QTextEdit.ExtraSelection`
To provide immediate visual affordance without mutating the underlying document or conflicting with `JsonHighlighter`:
- `ResponseMaskController` builds `QTextEdit.ExtraSelection` objects applied via `FoldableCodeView.setExtraSelections(selections)`.
- **Masked Token Format**:
  - Background: subtle neutral tint (`QColor(128, 128, 128, 48)`).
  - Underline: dashed underline (`QTextCharFormat.UnderlineStyle.DashUnderline`).
  - Tooltip: `"Click to reveal"`.
- **Revealed Token Format**:
  - Background: subtle accent tint (`QColor(76, 175, 80, 40)`).
  - Underline: dotted underline (`QTextCharFormat.UnderlineStyle.DotLine`).
  - Tooltip: `"Click to re-mask"`.
- `ExtraSelection` objects are rendered by Qt's viewport painting engine on top of syntax highlighting and do not alter text blocks or clipboard copy buffers.

#### 2.4 Hover & Click Interaction Mechanics
- **Mouse Tracking & Cursor Shape**:
  - `ResponseMaskController` installs an event filter on `FoldableCodeView.viewport()` and activates `setMouseTracking(True)`.
  - On `QEvent.Type.MouseMove`:
    - Checks if the character under cursor (`cursorForPosition(pos).position()`) falls within any span.
    - If inside a span, sets `viewport().setCursor(Qt.CursorShape.PointingHandCursor)`.
    - If outside, restores `viewport().setCursor(Qt.CursorShape.IBeamCursor)`.
- **Click-to-Reveal / Re-Mask Toggle**:
  - On `QEvent.Type.MouseButtonRelease` (or direct call to `handle_click(char_pos)`):
    - If `event.button() == Qt.MouseButton.LeftButton` and no text selection drag occurred (`not self.code_view.textCursor().hasSelection()`):
      - Hit-tests character position against `[span.start_pos, span.end_pos]`.
      - If a span is hit:
        - Toggles state: `new_text = span.raw_value if not span.is_revealed else span.masked_value`.
        - Replaces text via `QTextCursor`:
          ```python
          cursor = QTextCursor(self.code_view.document())
          cursor.setPosition(span.start_pos)
          cursor.setPosition(span.end_pos, QTextCursor.MoveMode.KeepAnchor)
          cursor.insertText(new_text)
          ```
        - Updates `delta = len(new_text) - len(old_text)`.
        - Updates `span.end_pos = span.start_pos + len(new_text)`.
        - Shifts `start_pos` and `end_pos` of all subsequent spans (`other.start_pos > span.start_pos`) by `delta`.
        - Re-applies `update_visual_formats()`.
        - Refreshes `fold_controller.ensure_scanned()`.
        - If search query is active, updates `_update_match_count()`.

#### 2.5 In-Memory Response Data Immutability
- All masking and unmasking transformations operate strictly on the `QTextDocument` within `ResponseView`.
- The original `ResponseData.body` string and historical records maintained by `HistoryManager` are never modified.

---

## Implementation Plan

### High-Level Approach

The implementation follows a test-driven development (TDD) workflow in Python:
1. **Step 3 (Failing Repro)**:
   - Create automated red test suite `tests/test_gui_response_view_click_to_reveal.py` using PySide6 `QTest`.
   - Assert all 8 interaction scenarios specified below.
   - Run tests to confirm failures against the current codebase where `ResponseView` lacks hidden field parameters and click-to-reveal handling.
2. **Step 4 (Development)**:
   - Create `pypost/ui/widgets/response_mask_controller.py` implementing `MaskedTokenSpan`, `JsonMaskFormatter`, and `ResponseMaskController`.
   - Update `pypost/core/sensitive_text_sanitizer.py` to ensure `format_path_variants` is publicly accessible.
   - Update `pypost/ui/widgets/response_view.py`:
     - Initialize `self.mask_controller = ResponseMaskController(self.body_view, self)`.
     - Update signature to `display_response(self, response: ResponseData, hidden_fields: Sequence[str] | None = None)`.
     - Wire masking into the JSON formatting branch when `hidden_fields` is provided and document size is within threshold.
     - Reset mask controller in `clear_body()`.
     - Store `_last_response` and `_last_hidden_fields` to preserve masking during `set_indent_size()`.
   - Update `pypost/ui/presenters/tabs_presenter_worker.py`:
     - Pass `hidden_fields=tab.request_data.hidden_response_fields` into `display_response` when request execution completes.
   - Run tests until green and execute quality gates (`make lint`, `make typecheck`, `make test`).

---

### Component Modifications and Signatures

#### 1. New Module: `pypost/ui/widgets/response_mask_controller.py`

```python
@dataclass
class MaskedTokenSpan:
    start_pos: int
    end_pos: int
    raw_value: str
    masked_value: str = '"***"'
    is_revealed: bool = False
    path: str = ""

class JsonMaskFormatter:
    """Formats JSON with indentation while detecting and recording masked token spans."""

    def __init__(self, selectors: set[str], indent: int = 2): ...
    def format(self, node: Any) -> tuple[str, list[MaskedTokenSpan]]: ...

def format_masked_json(
    raw_json: str,
    hidden_fields: Sequence[str],
    indent: int = 2,
) -> tuple[str, list[MaskedTokenSpan]]:
    """Parses JSON and returns pretty-printed text with masked placeholders and token spans."""
    ...

class ResponseMaskController(QObject):
    """Coordinates masked token spans, hover cursors, and click-to-reveal toggling in FoldableCodeView."""

    def __init__(self, code_view: FoldableCodeView, response_view: Any = None): ...
    def clear(self) -> None: ...
    def set_masked_spans(self, spans: list[MaskedTokenSpan]) -> None: ...
    def spans(self) -> list[MaskedTokenSpan]: ...
    def span_at(self, char_pos: int) -> MaskedTokenSpan | None: ...
    def handle_click(self, char_pos: int) -> bool: ...
    def update_visual_formats(self) -> None: ...
    def eventFilter(self, watched: QObject, event: QEvent) -> bool: ...
```

#### 2. Module Modification: `pypost/ui/widgets/response_view.py`

- Instantiate `self.mask_controller = ResponseMaskController(self.body_view, self)` in `init_ui()`.
- Update `display_response`:
  ```python
  def display_response(
      self,
      response: ResponseData,
      hidden_fields: Sequence[str] | None = None,
  ) -> None:
  ```
- In `display_response`:
  - Reset `self.mask_controller.clear()`.
  - Store `self._last_response = response` and `self._last_hidden_fields = list(hidden_fields) if hidden_fields else None`.
  - When `len(body_str) <= LARGE_DOC_CHAR_THRESHOLD` and `detected_format == BodyFormat.JSON`:
    - If `hidden_fields` is provided:
      ```python
      try:
          pretty_json, spans = format_masked_json(body_str, hidden_fields, indent=self.indent_size)
          self.body_view.setText(pretty_json)
          self.mask_controller.set_masked_spans(spans)
      except Exception:
          self.body_view.setText(body_str)
      ```
- In `clear_body`:
  - Call `self.mask_controller.clear()`.
  - Clear `self._last_response = None`, `self._last_hidden_fields = None`.
- In `set_indent_size`:
  - If `self._last_response`: re-invoke `self.display_response(self._last_response, self._last_hidden_fields)`.

#### 3. Module Modification: `pypost/ui/presenters/tabs_presenter_worker.py`

- In `_on_request_finished`:
  ```python
  hidden_fields = (
      tab.request_data.hidden_response_fields
      if tab.request_data and hasattr(tab.request_data, "hidden_response_fields")
      else None
  )
  tab.response_view.display_response(response, hidden_fields=hidden_fields)
  ```

---

### Mandatory — Failing Repro (next Step 3)

The failing repro test suite will be created in **Step 3** at:
- **Path**: `tests/test_gui_response_view_click_to_reveal.py`
- **Pytest Configuration**: Module-level `pytestmark = pytest.mark.timeout(60)` per `lsr-python` standard; uses `@pytest.mark.usefixtures("qapp")` for Qt UI event processing.

#### Required Test Scenarios:

1. **Default Masked Field Display**:
   - `test_default_masked_field_display`:
     - Calls `display_response(response, hidden_fields=["token", "client_secret"])`.
     - Asserts rendered document text contains `"token": "***"` and `"client_secret": "***"`.
     - Asserts unmasked sibling fields (e.g. `"status": "ok"`, `"id": 42`) remain in clear text.
     - Asserts `mask_controller.spans()` contains 2 initialized spans with `is_revealed == False`.

2. **In-Place Click-to-Reveal and Re-Mask Toggle**:
   - `test_inplace_click_to_reveal_and_remask`:
     - Locates the character position of `"***"`.
     - Simulates left-click via `mask_controller.handle_click(char_pos)` (and `QTest.mouseClick` on `body_view.viewport()`).
     - Asserts the text in `body_view.toPlainText()` changes in-place from `"***"` to the true secret value.
     - Asserts span state changes to `is_revealed == True`.
     - Clicks again at the revealed text position.
     - Asserts the text toggles back to `"***"` and span state reverts to `is_revealed == False`.
     - Asserts non-matching fields or whitespace clicks return `False` and do not modify document text.

3. **Coexistence with JsonHighlighter**:
   - `test_coexistence_with_json_highlighter`:
     - Verifies `JsonHighlighter` highlights the document when masked as valid string literals.
     - Triggers reveal and asserts highlighting updates without infinite loops, crashes, or unhandled exceptions.

4. **Coexistence with Search Navigation & Match Counting**:
   - `test_coexistence_with_search_and_match_count`:
     - Loads response with masked secret `"super_secret_key_999"`.
     - Sets `search_input.setText("super_secret_key_999")`.
     - Asserts match count displays `"No matches"` (total 0).
     - Clicks to reveal the secret.
     - Asserts search immediately finds the revealed text, and match count updates to `"1 of 1"` or `"1 match(es)"`.
     - Clicks to re-mask.
     - Asserts match count reverts to `"No matches"`.

5. **Coexistence with Code Folding and Context Menu**:
   - `test_coexistence_with_code_folding_and_context_menu`:
     - Loads nested JSON with foldable blocks and masked fields.
     - Folds an outer block; toggles a masked field inside an expanded sibling block.
     - Asserts fold regions remain valid and intact.
     - Selects the revealed secret text via `QTextCursor`.
     - Triggers context menu action "Set Variable"; asserts `variable_set_requested` emits the authentic unmasked secret string.
     - Triggers "Copy" action; asserts copied text contains the unmasked selection.

6. **Streaming Response Chunk Append Safety**:
   - `test_streaming_response_chunk_append_safety`:
     - Calls `response_view.append_body('{"chunk": 1, ')` followed by `response_view.append_body('"token": "secret"}')`.
     - Asserts append operations succeed without crashing or corrupting state.
     - Calls `display_response(final_response, hidden_fields=["token"])`.
     - Asserts complete masking applies cleanly to the final body.

7. **Large Document Fallback Performance**:
   - `test_large_document_fallback`:
     - Generates a response payload exceeding `LARGE_DOC_CHAR_THRESHOLD` (> 100 KB) containing hidden fields.
     - Calls `display_response(large_response, hidden_fields=["token"])`.
     - Asserts pretty-printing and token span tracking are safely bypassed (`mask_controller.spans() == []`).
     - Asserts raw text is rendered directly without UI thread stall.

8. **ResponseData Immutability**:
   - `test_response_data_immutability`:
     - Captures `raw_body = response.body`.
     - Executes multiple reveal and re-mask clicks.
     - Asserts `response.body == raw_body` and original `ResponseData` instance remains completely unmutated.

---

## Architecture

### 1. System Module Breakdown

```mermaid
flowchart TB
    subgraph UI_Layer["GUI Layer (pypost/ui)"]
        direction TB
        TPW["TabsPresenterWorker<br/>(pypost/ui/presenters/tabs_presenter_worker.py)"]
        RV["ResponseView<br/>(pypost/ui/widgets/response_view.py)"]
        RMC["ResponseMaskController<br/>(pypost/ui/widgets/response_mask_controller.py)"]
        JMF["JsonMaskFormatter<br/>Incremental offset tracker"]
        FCV["FoldableCodeView<br/>(pypost/ui/widgets/foldable_code_view.py)"]
        JH["JsonHighlighter<br/>(pypost/ui/widgets/json_highlighter.py)"]
        SEARCH["Search & Match Counter<br/>ResponseView search bar"]
        FOLD["FoldController<br/>(pypost/ui/widgets/fold/)"]
        CTX["Context Menu<br/>Set Variable / Copy"]

        TPW -->|display_response(response, hidden_fields)| RV
        RV -->|Delegates formatting & spans| RMC
        RMC --> JMF
        RV -->|Embeds| FCV
        RMC -->|Installs eventFilter on viewport| FCV
        RMC -->|Applies ExtraSelections| FCV
        FCV --- JH
        FCV --- SEARCH
        FCV --- FOLD
        FCV --- CTX
    end

    subgraph Core_Layer["Core Security & Shared Logic (pypost/core)"]
        STS["sensitive_text_sanitizer<br/>format_path_variants()"]
        JMF -.->|Reuses selector matching| STS
    end

    subgraph Model_Layer["Model Layer (pypost/models)"]
        RD["ResponseData<br/>(Immutable in-memory entity)"]
        RV -.->|Reads without mutating| RD
    end
```

---

### 2. Click-to-Reveal Interaction Flow

```mermaid
sequenceDiagram
    actor User
    participant View as ResponseView
    participant Ctrl as ResponseMaskController
    participant Formatter as JsonMaskFormatter
    participant CodeView as FoldableCodeView
    participant High as JsonHighlighter
    participant Search as Search Engine

    Note over View: Response received with hidden_fields=["token"]
    View->>Ctrl: format_masked_json(raw_body, hidden_fields)
    Ctrl->>Formatter: format(parsed_json)
    Formatter-->>Ctrl: (masked_text, spans)
    Ctrl-->>View: (masked_text, spans)
    View->>CodeView: setText(masked_text)
    View->>Ctrl: set_masked_spans(spans)
    Ctrl->>CodeView: setExtraSelections(visual_indicators)
    High-->>CodeView: Highlights "***" as valid JSON string

    Note over User,CodeView: User hovers over masked "***"
    CodeView->>Ctrl: viewport eventFilter: MouseMove(pos)
    Ctrl->>CodeView: viewport().setCursor(PointingHandCursor)

    Note over User,CodeView: User left-clicks on "***"
    CodeView->>Ctrl: viewport eventFilter: MouseButtonRelease(pos)
    Ctrl->>Ctrl: span = span_at(char_pos)
    Ctrl->>CodeView: QTextCursor.insertText(raw_secret)
    Note over Ctrl: Shifts subsequent spans by delta; span.is_revealed = True
    Ctrl->>CodeView: setExtraSelections(revealed_indicators)
    Ctrl->>Search: _update_match_count()
    High-->>CodeView: Re-highlights modified block automatically
```

---

### 3. Data Contracts and Interfaces

#### `MaskedTokenSpan`
```python
@dataclass
class MaskedTokenSpan:
    start_pos: int
    end_pos: int
    raw_value: str
    masked_value: str = '"***"'
    is_revealed: bool = False
    path: str = ""
```

#### `ResponseMaskController` Public API
```python
class ResponseMaskController(QObject):
    def __init__(self, code_view: FoldableCodeView, response_view: Any = None) -> None: ...
    def clear(self) -> None: ...
    def set_masked_spans(self, spans: list[MaskedTokenSpan]) -> None: ...
    def spans(self) -> list[MaskedTokenSpan]: ...
    def span_at(self, char_pos: int) -> MaskedTokenSpan | None: ...
    def handle_click(self, char_pos: int) -> bool: ...
    def update_visual_formats(self) -> None: ...
```

#### `ResponseView.display_response` Extension
```python
def display_response(
    self,
    response: ResponseData,
    hidden_fields: Sequence[str] | None = None,
) -> None:
    ...
```

---

## Q&A

- **Q: Why are visual indicators applied via `setExtraSelections()` instead of modifying document text or HTML formatting?**
  - **A**: `FoldableCodeView` is a plain text editor (`QPlainTextEdit`) operating on raw JSON. Injecting HTML tags or formatting markers directly into document text would invalidate JSON syntax, corrupt line character offsets, and break clipboard copying. `QTextEdit.ExtraSelection` applies styling (background tint, dashed underlines, tooltips) directly in the viewport painting layer without altering document characters, character offsets, or syntax highlighting.

- **Q: How does the system prevent index drift when multiple spans are toggled in arbitrary order?**
  - **A**: Spans are maintained in ascending document order by `start_pos`. Whenever any span is toggled, the difference in length (`delta = len(new_text) - len(old_text)`) is applied exclusively to subsequent spans (`other.start_pos > span.start_pos`). Spans located before the toggled position remain unchanged. This preserves exact character offsets across multiple clicks and toggles.

- **Q: What happens if a user selects a revealed secret and uses "Set Variable" or "Copy"?**
  - **A**: When a token is revealed, its authentic text is placed directly in the `QTextDocument`. Drag-selecting the text and choosing "Set Variable" reads `cursor.selectedText()`, which yields the authentic secret value and emits it via `variable_set_requested`. Similarly, standard clipboard "Copy" copies the exact text selected in the document.

- **Q: How does click-to-reveal avoid interfering with drag selection?**
  - **A**: In the viewport event filter, click detection on `MouseButtonRelease` verifies `not self.code_view.textCursor().hasSelection()`. If the user presses and drags the mouse across text, a selection is created; mouse release detects the active selection and does not trigger toggling, allowing users to freely highlight and select revealed text for copying.

- **Q: Why does the GUI use `display_response(response, hidden_fields)` rather than mutating `response.body`?**
  - **A**: Requirement FR-10 mandates strict immutability for `ResponseData`. The in-memory response data is the authoritative record of what the remote server returned; mutating it would corrupt post-request scripts, history storage, and debugging audits. Masking is purely a presentation-layer transformation.

- **Q: What happens during streaming responses?**
  - **A**: While chunks arrive, `ResponseView.append_body` streams plain text to the view without attempting partial masking. When the request terminates, `TabsPresenterWorker` invokes `display_response(response, hidden_fields=...)`, formatting the complete response cleanly with active masking.
