# PYPOST-398: Technical Debt Analysis

## Shortcuts Taken

None. Defaults preserve prior hardcoded colors via `DEFAULT_JSON_SYNTAX_COLORS`.

## Code Quality Issues

- **Theme not wired to settings**: Colors live in code-level theme module only; no
  `AppSettings` field or settings UI yet. Acceptable — PYPOST-395 covers dark palette.

## Missing Tests

- No test for re-highlight after swapping colors on an existing highlighter instance
  (not supported API; highlighter builds formats in `__init__` only).

## Performance Concerns

None introduced. Same number of `QColor` constructions as before.

## Follow-up Tasks

- Dark-theme JSON syntax palette and runtime theme switching —
  [PYPOST-395](https://pypost.atlassian.net/browse/PYPOST-395).
- Optional user-configurable colors in settings —
- Optional user-configurable colors in settings — [PYPOST-604](https://pypost.atlassian.net/browse/PYPOST-604)
