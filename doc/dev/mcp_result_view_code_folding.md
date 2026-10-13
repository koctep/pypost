# MCP Result View Code Folding

## Overview

The Model Context Protocol (MCP) tool execution result inspection pane (`McpResultView`)
supports code folding for structured payloads formatted in JSON, YAML, or XML. MCP tool
responses frequently contain large, deeply nested data structures spanning hundreds or
thousands of lines. Code folding allows developers to collapse and expand nested objects,
arrays, mappings, sequences, and XML elements on demand, substantially improving readability
and hierarchy inspection while reducing visual clutter.

Key capabilities:
- **Interactive Gutter Chevrons**: Visual fold indicators (`▼` expanded, `▶` collapsed) in the
  gutter allow toggling fold regions via single-click or double-click anywhere across the gutter.
- **Bulk Folding Controls**: "Fold All" and "Unfold All" action buttons in the result header
  toolbar allow collapsing or expanding all foldable blocks across the document in a single click.
- **Dynamic Format Detection**: Automatic detection of payload format (JSON, YAML, XML, or plain
  text) using heuristic syntax parsing (`detect_body_format`).
- **Dynamic JSON Pretty-Printing**: Unindented single-line JSON tool responses are automatically
  pretty-printed with two-space indentation when detected, enabling multi-line block folding.
- **Error and In-Progress Handling**: In-progress executions and tool transport/call errors fall
  back to plain text rendering with folding controls disabled.
- **Unstructured Text Fallback**: Non-structured payloads (such as plain text, command logs, or
  unrecognized formats) render cleanly with gutter line numbers but no fold chevrons.
- **Read-Only Non-Destructive Presentation**: Code folding is purely visual and non-destructive;
  underlying result text is fully preserved for copying and downstream inspection.

## Architecture

The code folding feature in `McpResultView` builds upon the repository's modular code folding
subsystem located in `pypost/ui/widgets/fold/` and `pypost/ui/widgets/foldable_code_view.py`.

### Component Diagram & Hierarchy

```
McpResultView (QWidget)
├── QVBoxLayout
│   ├── QHBoxLayout (Header Row)
│   │   ├── QLabel ("Result")
│   │   ├── QLabel (progress: "Invoking...")
│   │   ├── QLabel (elapsed: "Elapsed: <time> s", id: MCP_CLIENT_ELAPSED_LABEL)
│   │   ├── QSpacerItem (addStretch)
│   │   ├── QPushButton ("Fold All", id: MCP_CLIENT_RESULT_FOLD_ALL_BUTTON)
│   │   └── QPushButton ("Unfold All", id: MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON)
│   └── FoldableCodeView (_body, id: MCP_CLIENT_RESULT_PANE)
│       ├── LineNumberArea (gutter: line numbers & fold chevrons)
│       └── FoldController (tracks regions, manages QTextBlock visibility)
│           └── StructureScanner (JsonStructureScanner, YamlStructureScanner, etc.)
```

### Component Roles

- **`McpResultView` (`pypost.ui.widgets.mcp_client.mcp_result_view`)**:
  Hosts the tool execution result header and body viewer. Replaces the legacy `QPlainTextEdit`
  with `FoldableCodeView`. Orchestrates payload formatting, format detection, dynamic
  pretty-printing, and fold button enable/disable states.
- **`FoldableCodeView` (`pypost.ui.widgets.foldable_code_view`)**:
  A specialized `QPlainTextEdit` configured with a `LineNumberArea` gutter widget. It renders line
  numbers and fold chevrons, intercepts gutter mouse clicks and double-clicks to toggle fold
  regions, and delegates visibility and scanning to an internal `FoldController`.
- **`FoldController` (`pypost.ui.widgets.fold.fold_controller`)**:
  Coordinates document scanning using the appropriate `StructureScanner` for the active
  `BodyFormat`. Maintains the set of collapsed region IDs (`_collapsed_ids`) and toggles block
  visibility via `QTextBlock.setVisible()`. Provides `fold_all()`, `unfold_all()`, `toggle()`,
  and `ensure_scanned()`.
- **`LineNumberArea` (`pypost.ui.widgets.line_number_area`)**:
  Shared gutter widget attached to `FoldableCodeView`. Draws line numbers and chevron fold
  indicators (`▼` / `▶`). Passes mouse events to `FoldableCodeView`.
- **`detect_body_format` (`pypost.ui.widgets.fold.format_detector`)**:
  Heuristic syntax detector that classifies raw text payloads into `BodyFormat.JSON`,
  `BodyFormat.YAML`, `BodyFormat.XML`, or `BodyFormat.PLAIN`.

## API / Usage

### `McpResultView`

Public API methods exposed by `McpResultView`:

#### `set_result(payload: dict[str, Any], elapsed_s: float, *, is_error: bool) -> None`
Renders MCP `call_tool` result content blocks and optional `structuredContent`.
- If `is_error` is `True`, prepends "Error", formats payload, sets format to `BodyFormat.PLAIN`,
  and disables fold buttons.
- If `is_error` is `False`, detects format via `detect_body_format`.
  - When `BodyFormat.JSON` is detected, parses and pretty-prints the payload with 2-space
    indentation if unindented.
  - Configures `_body.set_body_format(fmt)` and calls `fold_controller().ensure_scanned()`.
  - Enables "Fold All" and "Unfold All" buttons if `fmt` is JSON, YAML, or XML.
- Updates elapsed execution time label (`Elapsed: <elapsed_s:g> s`).

#### `set_error(message: str, elapsed_s: float | None) -> None`
Displays a transport or validation error string in the result pane.
- Sets format to `BodyFormat.PLAIN` and disables fold buttons.
- Updates or clears the elapsed label depending on whether `elapsed_s` is provided.

#### `set_in_progress() -> None`
Sets the pane into an in-flight state prior to tool execution completion.
- Clears the result body and elapsed label.
- Sets format to `BodyFormat.PLAIN` and disables fold buttons.
- Displays "Invoking..." in the progress label.

#### `clear() -> None`
Resets the pane to an empty state (e.g., on server disconnect or tab switch).
- Clears progress, elapsed, and body text.
- Disables fold buttons and resets format to `BodyFormat.PLAIN`.

#### `fold_all() -> None`
Collapses all foldable regions in the result body viewer. Delegates directly to
`_body.fold_all()` and logs debug telemetry.

#### `unfold_all() -> None`
Expands all foldable regions in the result body viewer. Delegates directly to
`_body.unfold_all()` and logs debug telemetry.

#### `fold_controller() -> FoldController`
Returns the underlying `FoldController` instance managing fold regions and block visibility.

#### `body_format() -> BodyFormat`
Returns the currently active `BodyFormat` of the result body viewer.

### Widget IDs

The following widget object names are defined in `pypost.ui.widget_ids` for automated UI
testing and widget lookup:

- **`MCP_CLIENT_RESULT_PANE`**:
  Object name `"mcp_client_result_pane"` on the `FoldableCodeView` body editor.
- **`MCP_CLIENT_RESULT_FOLD_ALL_BUTTON`**:
  Object name `"mcp_client_result_fold_all_button"` on the "Fold All" button.
- **`MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON`**:
  Object name `"mcp_client_result_unfold_all_button"` on the "Unfold All" button.
- **`MCP_CLIENT_ELAPSED_LABEL`**:
  Object name `"mcp_client_elapsed_label"` on the elapsed execution time label.

### Example Usage in Tests

```python
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.mcp_client.mcp_result_view import McpResultView

# Instantiate view
view = McpResultView()

# Populate with structured JSON tool response
payload = {
    "content": [
        {"type": "text", "text": '{"status": "ok", "items": [1, 2, 3]}'}
    ]
}
view.set_result(payload, elapsed_s=0.12, is_error=False)

# Verify format detection and folding
assert view.body_format() == BodyFormat.JSON
assert view.fold_controller().region_count() > 0

# Collapse and expand programmatically
view.fold_all()
assert view.fold_controller().collapsed_count() > 0

view.unfold_all()
assert view.fold_controller().collapsed_count() == 0
```

## Configuration and Behaviors

### Dynamic JSON Pretty-Printing
MCP tools often return JSON encoded as a single minified line inside a `text` content block
(e.g., `{"status":"ok","count":42}`). Because fold controllers operate on multi-line indentation
and line block spans, a single-line string has no foldable lines. When `detect_body_format`
identifies `BodyFormat.JSON`, `McpResultView` attempts to parse and re-dump the payload with
`indent=2`. If parsing succeeds, the formatted multi-line text is rendered, allowing users to
immediately fold nested objects and arrays.

### Gutter Indicators & Double-Click Toggling
- **Chevrons**: The gutter displays `▼` (expanded) or `▶` (collapsed) on lines that begin a
  fold region.
- **Single-Click**: Clicking inside the chevron zone toggles the fold region starting on that line.
- **Double-Click**: Double-clicking anywhere on the gutter line (including the line number digits)
  toggles the fold region for that line, providing convenient accessibility.

### Error and In-Progress States
- When a tool returns an error (`is_error=True` or `set_error()`), the result content is marked
  as plain text (`BodyFormat.PLAIN`).
- "Fold All" and "Unfold All" buttons are explicitly disabled (`setEnabled(False)`) to prevent
  confusing interactions on non-foldable text.
- Similarly, calling `set_in_progress()` or `clear()` disables fold buttons and resets the format
  to `BodyFormat.PLAIN`.

### Disabled Folding for Unstructured Text
- For plain text outputs, Markdown, shell execution logs, or unparsed outputs, `detect_body_format`
  returns `BodyFormat.PLAIN`.
- Gutter line numbers remain visible to aid reading, but no fold chevrons are drawn and fold
  buttons remain disabled.

## Troubleshooting

### Unindented JSON Payload Not Folding
- **Cause**: The payload returned by the MCP tool may contain invalid JSON syntax (e.g., trailing
  commas, unquoted keys, single quotes), preventing `json.loads()` from parsing and formatting it.
- **Behavior**: `detect_body_format` falls back to `BodyFormat.PLAIN` or the JSON pretty-print
  `try-except` block catches an exception and leaves the text as-is.
- **Resolution**: Check the raw tool output. If the tool generates non-standard JSON, ensure the
  server emits valid JSON syntax conforming to RFC 8259.

### YAML or XML Payloads Falling Back to Plain Text
- **Cause**: The XML or YAML payload lacks characteristic syntax markers (e.g., missing root tag
  in XML, or YAML formatted without key-value colons or list dashes).
- **Behavior**: `detect_body_format` assigns `BodyFormat.PLAIN` when heuristic confidence is low.
- **Resolution**: Ensure the tool output includes recognizable structural markers (e.g. `<?xml`,
  closing tags `</...>`, or structured YAML keys).

### Gutter Double-Click Not Responding
- **Cause**: Double-clicking on a line that is not the start line of a fold region
  (e.g., an interior line or a line inside an already collapsed block).
- **Behavior**: Gutter clicks only toggle regions when the target line matches the start line of a
  scanned `FoldRegion`.
- **Resolution**: Click or double-click on the top line of the block containing the chevron
  indicator (`▼` or `▶`).
