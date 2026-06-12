# PYPOST-395: Technical Debt Analysis

## Shortcuts Taken

- **Palette heuristic only**: Dark vs light is inferred from `QPalette.Window` lightness,
  not an explicit user setting. Sufficient until app-wide theme toggle exists.

## Code Quality Issues

None blocking. Colors are centralized in `json_syntax_theme.py`; widget has no literals.

## Missing Tests

- No integration test simulating a dark `QApplication` palette end-to-end (unit tests use
  explicit `DARK_JSON_SYNTAX_COLORS` injection).

## Performance Concerns

None. `set_colors` rebuilds five `QTextCharFormat` objects — negligible on settings apply.

## Follow-up Tasks

- Add `AppSettings.theme` and settings UI for explicit light/dark/system choice.
- Add `AppSettings.theme` and settings UI for explicit light/dark/system choice. — [PYPOST-603](https://pypost.atlassian.net/browse/PYPOST-603)
- Optional user-configurable JSON syntax colors in settings.
- Optional user-configurable JSON syntax colors in settings. — [PYPOST-604](https://pypost.atlassian.net/browse/PYPOST-604)

## Verdict

**SAFE TO CLOSE** — dark palette, resolver, runtime rebinding, and tests complete.
