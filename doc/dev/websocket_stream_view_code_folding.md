# WebSocket Stream View Code Folding

## Overview

The WebSocket stream inspection view (`WebSocketStreamView` and `StreamDetailPane`) supports
code folding for structured message payloads formatted in JSON, YAML, or XML. When inspecting
real-time bidirectional streaming communication (or recorded transcripts), payload messages often
contain deeply nested structures such as JSON RPC payloads, structured event schemas, YAML
configurations, or XML fragments.

Integrating hierarchical code folding directly into `StreamDetailPane` enables developers to
selectively collapse and expand objects, lists, mappings, and markup tags. This improves readability
and simplifies payload analysis without interrupting stream consumption.

Key capabilities:
- **Automatic Format Detection**: Automatically sniffs syntax using `detect_body_format()` to
  identify JSON, YAML, or XML structures on message selection.
- **Interactive Gutter Chevrons & Double-Click**: Line numbers and visual fold chevrons
  (`▼` expanded, `▶` collapsed) render in the gutter. Users can toggle fold regions via single
  click on chevrons or double click anywhere on the gutter / line number area.
- **Bulk Folding Controls**: Dedicated "Fold All" and "Unfold All" toolbar buttons collapse or
  expand all detected hierarchical regions across the active message.
- **Hex Mode Interaction**: Activating hexadecimal inspection mode switches the view to plain text,
  suppresses fold indicators, and disables folding buttons to prevent parsing binary columns.
- **Word Wrap Preservation**: Toggling word wrap between wrapped and unwrapped layouts preserves all
  active fold states because folding operates on logical document blocks.
- **Non-Structured Fallback**: Messages formatted as plain text, raw strings, binary buffers, or
  unparseable formats render cleanly with fold controls gracefully disabled.

## Architecture

The code folding capability in the WebSocket stream view integrates the shared folding framework
into the stream inspection hierarchy:

```
pypost/ui/
├── widget_ids.py                               # Widget identity constants
└── widgets/
    ├── fold/
    │   ├── fold_controller.py      # AST fold region & block visibility controller
    │   ├── fold_region.py          # BodyFormat enum and FoldRegion dataclass
    │   ├── format_detector.py      # Syntax heuristic & format sniffer
    │   ├── structure_scanner.py    # Scanner registry and protocol
    │   ├── json_structure_scanner.py  # JSON AST scanner
    │   ├── yaml_structure_scanner.py  # YAML structure scanner
    │   └── xml_structure_scanner.py   # XML element scanner
    ├── foldable_code_view.py                   # Read-only QPlainTextEdit with gutter
    ├── line_number_area.py                     # Gutter widget delegating paint & clicks
    └── websocket/
        ├── stream_model.py                     # StreamListModel & entry abstractions
        └── stream_view.py                      # WebSocketStreamView & StreamDetailPane
```

### Component Roles

- **`StreamDetailPane` (`pypost.ui.widgets.websocket.stream_view`)**:
  Hosts message metadata (direction, size, timestamp, truncation warnings), action buttons
  (Copy, Set as variable, Wrap, Hex, Fold All, Unfold All), and the code display editor.
  Replaces raw `QTextEdit` with `FoldableCodeView`.
- **`FoldableCodeView` (`pypost.ui.widgets.foldable_code_view`)**:
  A specialized read-only `QPlainTextEdit` with an attached `LineNumberArea` gutter. It manages line
  number layout, draws fold chevrons, intercepts mouse press / double-click gutter events, and
  delegates folding mechanics to an internal `FoldController`.
- **`LineNumberArea` (`pypost.ui.widgets.line_number_area`)**:
  Gutter sub-widget that receives Qt paint and mouse events. Handles `mouseDoubleClickEvent` by
  delegating to `_editor.line_number_area_mouse_double_click(event)` to toggle fold regions
  regardless of horizontal click position within the gutter.
- **`FoldController` (`pypost.ui.widgets.fold.fold_controller`)**:
  Executes format-specific AST scanners against the document text, manages the set of collapsed
  region IDs (`_collapsed_ids`), and manipulates Qt block visibility via `QTextBlock.setVisible()`.
- **`detect_body_format` (`pypost.ui.widgets.fold.format_detector`)**:
  Applies syntax heuristics (checking for valid JSON start/end tokens, YAML indentation and key
  patterns, XML tags) to detect whether an incoming message payload represents JSON, YAML, XML,
  or plain text.

### Event and Rendering Flow

1. **Selection or Streaming Update**:
   - The user selects a frame in `WebSocketStreamView`, or follow-tail selects an incoming frame.
   - `StreamDetailPane.set_entry(entry)` receives the `StreamEntry`.
2. **Format Detection & Editor Initialization**:
   - In text mode (when hex mode is inactive), `detect_body_format(None, entry.payload)` determines
     the format.
   - The pane updates `_editor.set_body_format(detected_format)` and passes text via
     `_editor.setPlainText(entry.payload)`.
   - Structural scanning executes via `fold_controller().ensure_scanned()`.
   - Fold buttons ("Fold All", "Unfold All") are enabled if format is JSON, YAML, or XML.
3. **Gutter Interaction**:
   - Clicking a chevron toggles the targeted block's region.
   - Double-clicking anywhere on the line's gutter toggles the block's fold state.
   - `FoldController` updates block visibility and refreshes the viewport and gutter.

## API / Usage

### `StreamDetailPane` Methods

`StreamDetailPane` exposes methods and properties for controlling code display and folding:

```python
from pypost.ui.widgets.websocket.stream_view import StreamDetailPane
from pypost.ui.widgets.fold.fold_region import BodyFormat

pane = StreamDetailPane(parent=None)

# Retrieve attached FoldController
controller = pane.fold_controller()

# Collapse all hierarchical regions in active message
pane.fold_all()

# Expand all regions back to full visibility
pane.unfold_all()

# Inspect current detected body format
fmt = pane.body_format()  # Returns BodyFormat.JSON, YAML, XML, or PLAIN
```

- **`fold_all() -> None`**:
  Collapses all foldable blocks in the active payload editor. Emits debug log
  `websocket_stream_folding_fold_all_invoked`.
- **`unfold_all() -> None`**:
  Expands all collapsible blocks in the active payload editor. Emits debug log
  `websocket_stream_folding_unfold_all_invoked`.
- **`fold_controller() -> FoldController`**:
  Returns the underlying `FoldController` instance driving block visibility and region queries.
- **`body_format() -> BodyFormat`**:
  Returns the currently active `BodyFormat` enum value (`JSON`, `YAML`, `XML`, or `PLAIN`).
- **`set_entry(entry: Optional[StreamEntry]) -> None`**:
  Renders payload and metadata for the given stream entry, automatically detecting syntax format
  and updating fold controls.

### Toolbar Buttons and Widget IDs

The action toolbar in `StreamDetailPane` provides the following buttons and identifiers
defined in `pypost.ui.widget_ids`:

- `WS_STREAM_DETAIL_FOLD_ALL_BUTTON` (`"pypost_ws_stream_detail_fold_all_button"`):
  Collapses all detected fold regions across the active message payload.
- `WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON` (`"pypost_ws_stream_detail_unfold_all_button"`):
  Expands all detected fold regions back to full visibility.
- `WS_STREAM_DETAIL_WRAP_BUTTON` (`"pypost_ws_stream_detail_wrap_button"`):
  Toggles line wrapping mode between `WidgetWidth` and `NoWrap`.
- `WS_STREAM_DETAIL_HEX_BUTTON` (`"pypost_ws_stream_detail_hex_button"`):
  Toggles hexadecimal memory dump inspection view.
- `WS_STREAM_DETAIL_COPY_BUTTON` (`"pypost_ws_stream_detail_copy_button"`):
  Copies payload or selected text to the system clipboard with secret sanitization.
- `WS_STREAM_DETAIL_SET_VAR_BUTTON` (`"pypost_ws_stream_detail_set_var_button"`):
  Opens variable capture dialog for selected text or entire payload.

## Configuration and Behaviors

### Interaction with Hex Mode

- When the **Hex** button is activated:
  - The payload is formatted as a three-column hexadecimal memory dump (offset, hex, ASCII).
  - The editor format is switched to `BodyFormat.PLAIN`.
  - The "Fold All" and "Unfold All" buttons are disabled.
  - No fold chevrons are drawn in the gutter, preventing invalid fold calculations on hex dump text.
- When Hex mode is deactivated:
  - The original payload text is restored.
  - The format is automatically re-detected via `detect_body_format()`.
  - Fold buttons and gutter chevrons are re-enabled if structured data is detected.

### Interaction with Word Wrap

- Toggling the **Wrap** button toggles `QPlainTextEdit.LineWrapMode` between `WidgetWidth` and
  `NoWrap`.
- Because folding in `FoldController` manipulates logical `QTextBlock` elements rather than visual
  display lines, word wrap changes do not corrupt or reset active collapsed states.

### Unstructured and Plain Text Fallbacks

- If a stream entry contains unformatted text, binary strings, or invalid markup that fails syntax
  heuristics:
  - `detect_body_format()` classifies the payload as `BodyFormat.PLAIN`.
  - The editor renders the text without error.
  - "Fold All" and "Unfold All" buttons remain disabled.
  - Gutter renders clean line numbers without fold chevrons.

## Troubleshooting

### Stream Navigation & Rapid Updates

- **Symptom**: Fast streaming throughput causes UI lag during inspection.
- **Cause**: Re-scanning large payloads repeatedly.
- **Resolution**: Fold scanning is only executed for the message currently selected in
  `StreamDetailPane`. High-volume incoming frames flowing into `WebSocketStreamView` in the
  background do not trigger fold scanning unless explicitly selected or follow-tail auto-updates
  the detail pane.

### Fold Controls Disabled for JSON/YAML/XML

- **Symptom**: "Fold All" and "Unfold All" buttons are grayed out for a structured payload.
- **Check Hex Mode**: Verify that Hex mode is turned off. Hex mode intentionally suppresses fold
  controls.
- **Check Syntax Validity**: If the payload is malformed (e.g. truncated JSON closing bracket or
  invalid XML root), `detect_body_format()` may fall back to `BodyFormat.PLAIN`. Check the metadata
  bar to see if the message was marked as truncated.

### Collapsed Regions Not Expanding on Click

- **Symptom**: Clicking gutter does not toggle region.
- **Check Click Target**: Single click requires clicking the fold chevron column (leftmost area
  of the gutter). Double-clicking anywhere on the line number gutter toggles the region regardless
  of position.
