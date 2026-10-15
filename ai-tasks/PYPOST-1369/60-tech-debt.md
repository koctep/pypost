# PYPOST-1369: Technical Debt Analysis

## Shortcuts Taken

- **Synchronous Viewport Gutter Rendering and Block Lookup**:
  `FoldablePlainTextEdit.line_number_area_paint_event` and `_toggle_fold_at_y` perform synchronous block traversal (`firstVisibleBlock()`, `blockBoundingGeometry()`, and `fold_header_at_block()`) directly on the Qt main GUI thread. While viewport iteration is bounded by visible block count on screen, AST and fold-header lookup occurs synchronously during UI paint and mouse interaction events. Background scanning offloading is deferred to upcoming issue PYPOST-1370.
- **Unicode Glyph Rendering for Chevrons**:
  Fold indicators are painted using literal unicode string characters (`"\u25b6"` for collapsed and `"\u25bc"` for expanded) via `painter.drawText(...)` instead of dedicated vector paths or theme-aware SVG icon assets.
- **Fixed Metric Constants**:
  Gutter chevron width and padding are configured as module constants (`_CHEVRON_WIDTH = 14`, `_CHEVRON_PADDING = 2`, and fixed `3` px spacing) rather than dynamic DPI-scaled or theme-configurable metrics.
- **Dynamic Method Fallback on Gutter Area**:
  `LineNumberArea.mouseDoubleClickEvent` checks for `line_number_area_mouse_double_click` via `getattr(..., None)` with callable fallback to preserve backwards compatibility across custom editor implementations rather than enforcing an abstract interface method.

## Code Quality Issues

- **Block Traversal Logic Duplication**:
  The visible block coordinate traversal loop in `FoldablePlainTextEdit._toggle_fold_at_y` mirrors the iteration loop structure in `FoldablePlainTextEdit.line_number_area_paint_event`. Extracting a shared coordinate-to-block helper (e.g., `_block_at_y(y: float) -> tuple[QTextBlock, int] | None`) would reduce code duplication.
- **Multiple Inheritance Initialization in CodeEditor**:
  `CodeEditor` subclasses `VariableHoverMixin` and `FoldablePlainTextEdit`. To avoid Qt `QObject` multiple inheritance diamond issues, initializers are called explicitly (`FoldablePlainTextEdit.__init__(self, ...)` and `VariableHoverMixin.__init__(self)`). While clean and reliable, standardizing mixin initialization conventions across PyPost UI widgets would enhance long-term maintainability.
- **Viewer-Specific Mask Controller Decoupling**:
  `FoldableCodeView` retains `_mask_controller` (`ResponseMaskController`) specific to response viewers. A more generalized gutter/editor annotation hook or extension protocol could unify masking and annotation capabilities across all editor surfaces in the future.

## Missing Tests

- **High-DPI and Device Pixel Ratio Scaling**:
  Test coverage currently exercises standard coordinate geometry. Dedicated tests for gutter layout and chevron hitboxes under fractional and integer High-DPI scaling factors (`devicePixelRatio` >= 2.0) are not present.
- **Word Wrap Gutter Alignment**:
  `FoldablePlainTextEdit` enforces `QPlainTextEdit.LineWrapMode.NoWrap`. If soft word wrapping is enabled in future editor modes, block height vs multi-line wrapped layout in the gutter will need explicit test coverage.
- **Stress & Edge-Case Test Suites**:
  Stress testing on extreme file sizes (100k+ lines) and deeply nested structural hierarchies (> 50 nesting levels) is not part of the standard unit suite. This is intentionally deferred to upcoming sprint issue PYPOST-1371.

## Performance Concerns

- **Synchronous AST & Document Scanning**:
  For multi-megabyte payloads, running the fold scanner synchronously on the main GUI thread upon document changes can cause frame drops and noticeable input latency. Upcoming sprint issue PYPOST-1370 directly addresses this concern by introducing a background folding scanner worker thread.
- **Visible Block Lookups on Rapid Scroll**:
  During high-frequency vertical scrolling, `line_number_area_paint_event` repeatedly queries `self._fold_controller.fold_header_at_block(block_number)`. While O(log N) or O(1) in the region index, keeping region lookup overhead minimal is critical for 60/120 FPS scrolling smoothness.

## Follow-up Tasks

- **[PYPOST-1370](https://pypost.atlassian.net/browse/PYPOST-1370): Background Folding Scanner**:
  Offload document AST analysis and fold region scanning to a dedicated background QThread/worker to eliminate main UI thread stalls on large payloads.
- **[PYPOST-1371](https://pypost.atlassian.net/browse/PYPOST-1371): Stress and Edge-Case Test Suite**:
  Add high-volume stress tests (large documents > 100k lines, deep hierarchy nesting, rapid burst edits) to validate editor memory stability and gutter rendering performance.
- **[PYPOST-1398](https://pypost.atlassian.net/browse/PYPOST-1398): Refactor Coordinate Traversal Helper**:
  Consolidate `_toggle_fold_at_y` and `line_number_area_paint_event` block coordinate lookup loops into a shared helper method on `FoldablePlainTextEdit`.
- **[PYPOST-1399](https://pypost.atlassian.net/browse/PYPOST-1399): Vector & Theme-Aware Gutter Chevrons**:
  Replace unicode chevron glyphs with scalable SVG or QPainterPath vector drawings supporting dynamic theme palette colors.
- **NON-BLOCKER — pre-existing**:
  - `tests/test_check_lock.py::test_repro_check_lock_dev_detects_no_drift` under Jira issue **[PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)** (Dev lock drift detection pre-existing failure in repository tooling suite).
