# PYPOST-510: Technical Debt Analysis

## Shortcuts Taken

No significant shortcuts. The implementation follows the official Qt Code Editor example pattern
(viewport margins + delegated painting).

## Code Quality Issues

- `LineNumberArea` duck-types the host editor (`line_number_area_width`,
  `line_number_area_paint_event`) instead of a shared protocol or mixin. Acceptable for a single
  consumer (`CodeEditor`); extract only if the Script tab adopts the same gutter (PYPOST-10).

## Missing Tests

- No automated UI test that opens `RequestWidget` and visually confirms the Body tab gutter in an
  integrated widget hierarchy (covered indirectly: `RequestWidget` uses `CodeEditor`, and gutter
  tests target `CodeEditor` directly).
- tests target `CodeEditor` directly). — [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516)
- No undo/redo-specific line-number test (block count updates are covered via typing, paste, and
  delete; undo/redo reuse the same `blockCountChanged` path).

## Performance Concerns

None for typical payload sizes. Painting is O(visible lines) per paint event, matching Qt guidance.

## Follow-up Tasks

- Reuse the line-number gutter on the Script tab editor (tracked in existing tech debt).
- Reuse the line-number gutter on the Script tab editor (tracked in existing tech debt). — [PYPOST-10](https://pypost.atlassian.net/browse/PYPOST-10)
- Add an integration test that loads `RequestWidget` and asserts the Body tab shows a gutter with
  correct width (non-blocker).
- correct width (non-blocker). — [PYPOST-516](https://pypost.atlassian.net/browse/PYPOST-516)
