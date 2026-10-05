# PYPOST-1294: Platform-neutral Help-row snapshot; NativeText for all displayed keys

## Goals

Ensure cross-platform UI consistency and robust test suites across Linux, Windows, and macOS:
1. **Consistent shortcut display across platforms**: Ensure all shortcut keys displayed in
   the Help dialog (whether primary shortcuts, alternative shortcuts, group shortcuts, or
   documentation-only shortcuts) are formatted using platform-native text (`NativeText`) so that
   macOS users see appropriate native symbols (e.g. `⌘`, `⌥`, `⇧`, `↩`) rather than a mix of
   raw strings and native text.
2. **Platform-neutral test suite snapshot**: Ensure `_EXPECTED_OTHER_HELP_ROWS` in
   `tests/test_main_window_hotkeys.py` does not hardcode Linux/Windows-specific shortcut string
   literals, allowing the test suite to pass on macOS and other platforms without platform-specific
   failures.

## User Stories

- As a macOS user of PyPost, I want all keyboard shortcuts in Help → Hotkeys to be rendered
  consistently in native macOS symbols and formatting, so that I can easily understand and use
  the key combinations.
- As a developer running tests on macOS or Linux, I want `test_other_help_rows_unchanged` to pass
  reliably on my platform by dynamically converting expected specifications through `NativeText`,
  so that CI and local environments behave predictably.

## Definition of Done

- In `pypost/ui/hotkeys.py`, all displayed keys extracted from actions for the Help dialog are
  normalized to `QKeySequence.SequenceFormat.NativeText`.
- In `tests/test_main_window_hotkeys.py`, `_EXPECTED_OTHER_HELP_ROWS` is converted to native text
  representation dynamically or rendered platform-neutral, so the snapshot comparison succeeds on
  all supported operating systems.
- New unit tests verify that actions with alternative keys, groups, and documentation rows all
  render native text correctly when collected.
- Quality gates pass: `make lint`, `make typecheck`, and `make test`.

## Task Description

During PYPOST-1285, `register_hotkey_documentation` was modified to store native text
(`QKeySequence(key).toString(NativeText)`). However, `register_hotkey_group` and `tag_action`
stored raw key strings in `ALT_KEYS_PROPERTY`, and `_keys_from_action` only converted the primary
action shortcut to `NativeText`. Consequently, on macOS, certain rows (like `Send Request`) mixed
raw text (`Ctrl+Return`) with native text elsewhere, and `_EXPECTED_OTHER_HELP_ROWS` failed because
it was a static literal snapshot.

Constraints:
- Implementation language: Python.
- Lines must not exceed 100 characters.
- Must execute all checks through `make`.

## Q&A

- Q: Where should the native text conversion happen?
  A: In `_keys_from_action` (and/or `tag_action`/`register_hotkey_group`), ensuring that any key
  string retrieved from `ALT_KEYS_PROPERTY` is transformed via
  `QKeySequence(k).toString(QKeySequence.SequenceFormat.NativeText)`.
- Q: How should `_EXPECTED_OTHER_HELP_ROWS` be constructed?
  A: By storing portable key specifications (e.g., `"Ctrl+Q"`, `"F5 / Ctrl+Return"`,
  `"Alt+1 ... Alt+9"`) and transforming each component via `NativeText` at runtime.
