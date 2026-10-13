# Response View Code Folding

## Overview

The response inspection view (`ResponseView`) supports code folding for structured API responses
formatted in JSON, YAML, or XML. This enables developers to collapse and expand nested objects,
arrays, mappings, sequences, and XML elements on demand, substantially improving readability and
navigational efficiency when inspecting large or deeply nested payloads.

Key capabilities:
- **Interactive Gutter Chevrons**: Visual fold indicators (`▼` expanded, `▶` collapsed) in the
  gutter allow toggling fold regions via left-click.
- **Bulk Folding Controls**: "Fold All" and "Unfold All" buttons in the status/search toolbar and
  context menu allow collapsing or expanding all foldable blocks across the document at once.
- **Format Sniffing & Detection**: Automatic classification of payload format (JSON, YAML, XML, or
  plain text) via HTTP `Content-Type` header inspection with fallback to heuristic syntax parsing.
- **Search Interoperability**: Searching within response text automatically discloses and unfolds
  any collapsed regions enclosing the active match, ensuring search hits are visible.
- **Read-Only Preservation**: Folding manipulates block visibility non-destructively; clipboard
  copy, text selection, and variable extraction continue to access the underlying response body.
- **Graceful Plain-Text Fallback**: Non-structured payloads (such as plain text, HTML, or raw
  unparsed formats) render without fold controls or syntax errors.

## Architecture

The code folding feature in `ResponseView` is structured into decoupled components spanning
format detection, structural parsing, fold state management, and custom Qt widget presentation:

```
pypost/ui/widgets/
├── fold/
│   ├── format_detector.py        # Content-Type & payload structure detection
│   ├── fold_controller.py        # Fold region state & block visibility controller
│   ├── fold_region.py            # BodyFormat enum and FoldRegion dataclass
│   ├── structure_scanner.py      # Scanner registry and scanner protocol
│   ├── json_structure_scanner.py # JSON AST scanner
│   ├── yaml_structure_scanner.py # YAML mapping and sequence scanner
│   └── xml_structure_scanner.py  # XML element hierarchy scanner
├── foldable_code_view.py         # Read-only QPlainTextEdit with gutter & chevrons
├── line_number_area.py           # Shared gutter widget for line numbers & chevrons
├── json_highlighter.py           # Syntax highlighter for JSON payloads
└── response_view.py              # Hosts status, search, and FoldableCodeView
```

### Component Roles

- **`detect_body_format` (`pypost.ui.widgets.fold.format_detector`)**:
  Inspects response headers (`Content-Type`) and body text heuristics to determine the payload's
  `BodyFormat` (`JSON`, `YAML`, `XML`, or `PLAIN`).
- **`FoldableCodeView` (`pypost.ui.widgets.foldable_code_view`)**:
  A specialized `QPlainTextEdit` configured with a `LineNumberArea` gutter widget. It renders line
  numbers and fold chevrons, intercepts gutter mouse clicks to toggle fold regions, and delegates
  visibility and scanning to an internal `FoldController`.
- **`FoldController` (`pypost.ui.widgets.fold.fold_controller`)**:
  Coordinates document scanning using the appropriate `StructureScanner` for the active
  `BodyFormat`. Maintains the set of collapsed region IDs and toggles block visibility via
  `QTextBlock.setVisible()`. Extended with bulk operations (`fold_all()`, `unfold_all()`),
  synchronous scanning (`ensure_scanned()`), and match disclosure (`reveal_block()`).
- **`ResponseView` (`pypost.ui.widgets.response_view`)**:
  The user-facing response panel. Embeds `FoldableCodeView` as its `body_view`, triggers format
  detection upon `display_response()`, wires toolbar and context menu folding actions, manages JSON
  syntax highlighting, and coordinates search match revealing.

## API / Usage

### `detect_body_format()`

Determines the `BodyFormat` of a payload based on response headers or text heuristics.

```python
from pypost.ui.widgets.fold import BodyFormat, detect_body_format

# Header-driven detection
detected = detect_body_format({"Content-Type": "application/json"}, '{"id": 1}')
assert detected == BodyFormat.JSON

# Heuristic fallback (e.g. absent or generic Content-Type)
detected = detect_body_format(None, "<root><item>value</item></root>")
assert detected == BodyFormat.XML
```

- **`headers`**: Dictionary of response headers (can be `None` or empty).
- **`body`**: Raw payload string.
- **Returns**: `BodyFormat` enum member (`JSON`, `YAML`, `XML`, or `PLAIN`).

### `FoldableCodeView`

Subclasses `QPlainTextEdit` to provide gutter line numbering and code folding affordances.

```python
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.foldable_code_view import FoldableCodeView

view = FoldableCodeView(parent=None, indent_size=2)
view.setReadOnly(True)

# Set format to enable folding for a specific syntax
view.set_body_format(BodyFormat.JSON)
view.setPlainText('{\n  "name": "example",\n  "items": [1, 2]\n}')

# Bulk folding controls
view.fold_all()    # Collapse all detected blocks
view.unfold_all()  # Expand all blocks

# Reveal a specific line/block (e.g. search hit)
view.reveal_block(block_number=2)

# Access underlying fold controller
controller = view.fold_controller()
```

- **`set_body_format(body_format: BodyFormat)`**: Updates the active format and schedules a scan.
- **`fold_all()`**: Collapses all discovered fold regions across the document.
- **`unfold_all()`**: Expands all fold regions, restoring full visibility.
- **`reveal_block(block_number: int)`**: Expands any collapsed regions enclosing `block_number`.
- **`fold_controller()`**: Returns the attached `FoldController` instance.
- **`setText(text: str)`**: Compatibility alias for `setPlainText(text)`.

### `FoldController` Folding Methods

`FoldController` manages region scanning and block visibility on a `QPlainTextEdit`:

- **`fold_all()` / `collapse_all()`**:
  Forces an immediate scan if pending, marks every discovered region as collapsed, and updates
  viewport visibility.
- **`unfold_all()` / `expand_all()`**:
  Clears all collapsed regions, resets `QTextBlock.setVisible(True)` across all blocks, and
  refreshes the viewport.
- **`reveal_block(block_number: int)`**:
  Finds any currently collapsed fold region whose range (`start_block <= block_number <= end_block`)
  encloses `block_number`, removes them from `_collapsed_ids`, and updates block visibility.
- **`ensure_scanned()`**:
  Synchronously executes the structure scanner if the debounce timer is running or if regions have
  not yet been populated for non-empty text.

## Configuration and Behaviors

### Content-Type Inspection Rules

Format detection checks the `Content-Type` header (case-insensitively, ignoring parameters such
as `; charset=utf-8`):

| Target Format | Matching Content-Type MIME Patterns |
| --- | --- |
| `BodyFormat.JSON` | `application/json`, `text/json`, `application/*+json` |
| `BodyFormat.YAML` | `application/x-yaml`, `text/yaml`, `application/yaml`, `text/x-yaml` |
| `BodyFormat.XML` | `application/xml`, `text/xml`, `application/*+xml` |
| `BodyFormat.PLAIN` | All other MIME types (e.g. `text/plain`, `text/html`, `image/png`) |

### Fallback Sniffing Heuristics

When `Content-Type` is omitted or uninformative (`text/plain`, `application/octet-stream`), the
detector evaluates the trimmed body payload:

1. **JSON Sniffing**: If body starts and ends with `{}` or `[]`, verifies validity via
   `json.loads()`.
2. **XML Sniffing**: If body starts and ends with `<>`, parses via
   `xml.etree.ElementTree.fromstring()`.
3. **YAML Sniffing**: If body contains colons and newlines, parses via `yaml.safe_load()` and checks
   for top-level dictionary or list mappings.
4. **Plain Fallback**: If none match or parsing fails, defaults to `BodyFormat.PLAIN`.

### Large Document Threshold

In `ResponseView`, payloads exceeding `LARGE_DOC_CHAR_THRESHOLD` (100 KB / 102,400 characters)
skip JSON indentation and formatting to ensure UI responsiveness. Folding remains supported,
and search debouncing (`SEARCH_DEBOUNCE_MS = 250` ms) is enabled to avoid stutter on large bodies.

## Troubleshooting

### Non-Structured or Unformatted Payloads

- **Symptom**: Gutter shows line numbers but no fold chevrons (`▼` / `▶`) appear.
- **Cause**: The payload was classified as `BodyFormat.PLAIN` (either non-structured text, HTML, or
  syntax parsing failed due to invalid JSON/YAML/XML).
- **Resolution**: Check the server's `Content-Type` header or inspect the payload for syntax
  errors. Malformed syntax intentionally falls back to plain display without crashing.

### Search Match Inside Collapsed Region

- **Symptom**: Search highlights a match, but line numbers appear skipped or text is hidden.
- **Cause**: The match occurred inside a folded block that was not properly disclosed.
- **Resolution**: `ResponseView._find_next()` and `_find_previous()` automatically invoke
  `self.body_view.reveal_block(matched_block)`. If calling `find()` programmatically outside
  `ResponseView`, ensure you invoke `body_view.reveal_block(cursor.blockNumber())` to expand
  enclosing blocks.

### Chevrons Not Aligning with Line Numbers

- **Symptom**: Chevrons overlap line number digits or gutter margins appear clipped.
- **Cause**: Font changes or custom font metrics were applied without recalculating gutter margins.
- **Resolution**: `FoldableCodeView` handles `QEvent.Type.FontChange` in `changeEvent()`. For custom
  font alterations, call `view.update_indent_size()` or force margin updates via
  `view._update_line_number_area_width(0)`.
