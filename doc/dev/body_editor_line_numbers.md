# Body Editor Line Numbers

## Overview

The request Body tab uses `CodeEditor`, which displays a read-only line-number gutter alongside
the editable text. Numbers start at 1, update on every edit, stay aligned while scrolling, and
adapt gutter width as line counts cross digit boundaries (9→10, 99→100).

## Architecture

- **`LineNumberArea` (`pypost/ui/widgets/line_number_area.py`)** — Thin child widget over the
  editor's left viewport margin. Delegates painting to the host editor; does not accept focus or
  keyboard input.
- **`CodeEditor` (`pypost/ui/widgets/code_editor.py`)** — Owns gutter lifecycle: viewport
  margins, width calculation, scroll sync (`blockCountChanged`, `updateRequest`), resize geometry,
  and number painting via `firstVisibleBlock()`.
- **`RequestWidget` (`pypost/ui/widgets/request_editor.py`)** — Body tab already instantiates
  `CodeEditor`; no changes required for line numbers to appear.

Pattern follows the [Qt Code Editor example](https://doc.qt.io/qt-6/qtwidgets-widgets-codeeditor-example.html).

## API / Usage

### `CodeEditor.line_number_area_width() -> int`

Returns gutter width in pixels based on current `blockCount()` and document font metrics.

### `CodeEditor.line_number_area_paint_event(event: QPaintEvent)`

Paints right-aligned, palette-derived line numbers for visible blocks. Called by
`LineNumberArea.paintEvent`.

### Integration

Any widget that uses `CodeEditor` for multi-line text automatically gets line numbers. The Script
tab uses a plain `QPlainTextEdit` and is out of scope (see `doc/dev/tech-debt/PYPOST-10.md`).

## Configuration

No user setting or environment variable. Line numbers are always shown on `CodeEditor` instances.

## Troubleshooting

### Line numbers do not appear

Confirm the widget is `CodeEditor`, not `QPlainTextEdit`. Only `CodeEditor` wires the gutter.

### Numbers clipped at high line counts

Gutter width recalculates on `blockCountChanged`. If numbers clip after bulk paste, check that
`blockCount` reflects the new line count (empty documents still have one block).

### Clicking the gutter changes the cursor

Expected: the gutter is read-only. Clicks should not modify text; focus remains on the editor
viewport.
