# PYPOST-1104: Technical Debt Analysis

## Shortcuts Taken

1. **Custom `QListWidget` Popup Window vs. Full `QCompleter` Architecture**:
   - In `pypost/ui/widgets/mcp_server_headers_table.py`, `VariableAutocompleteLineEdit` manages candidate suggestions using a frameless, tool-popup `QListWidget` (`Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint`) with manual coordinate translation via `mapToGlobal` and explicit key filtering (`keyPressEvent`), rather than implementing a full `QCompleter` backed by `QAbstractItemModel`.
   - *Rationale*: A lightweight custom popup directly handles multi-character trigger delimiters (`{{`), variable token extraction, cursor positioning, and insertion formatting (`{{ VARIABLE_NAME }}`) without fighting `QCompleter`'s single-prefix prefix-matching assumptions or overriding default completer selection mechanisms.
   - *Compromise*: Standard OS accessibility properties (e.g. screen reader announcements via MSAA/AT-SPI) and platform-specific window styling/theming are not automatically inherited; popup positioning and dismissal must be manually handled across `focusOutEvent` and `hideEvent`.

2. **Synchronous Full-Table Regex Validation on Key Events**:
   - Every cell edit in `McpServerHeadersTable` invokes `validate_rows()`, which re-evaluates all rows synchronously on the main Qt thread using compiled regexes (`RFC_7230_TOKEN_RE`, unclosed brace matching, variable existence checking).
   - *Rationale*: For typical proxy server configurations containing 1–20 custom headers, synchronous regex validation executes in under 0.5 milliseconds, providing instantaneous tactile feedback with zero debouncing latency or asynchronous state complexity.
   - *Compromise*: No asynchronous or worker-thread offload or debounce timer is employed. While ideal for small sets, editing extremely large header lists (e.g. hundreds of rows) could introduce minor frame drops on lower-spec hardware.

3. **Advisory Warning vs. Structural Blocker Separation**:
   - Header key errors (RFC 7230 token violations, empty keys when values exist) are treated as structural errors that block configuration saving in `_McpServerEditor._accept_if_complete()`. In contrast, undefined variable references (`{{ UNKNOWN }}`) and unclosed braces in values are treated as advisory warnings (highlighted with orange color and tooltips) rather than hard blockers.
   - *Rationale*: Allows developers to stage header configurations referencing environment variables that will be created or imported subsequently, or use literal double-braces if required by specific upstream protocols.
   - *Compromise*: A user who makes a typo in an environment variable name can still save the configuration, discovering the unresolved variable error at proxy connection time rather than being forced to correct it during editing.

## Code Quality Issues

1. **Coupling of `VariableAutocompleteLineEdit` to the Headers Table Module**:
   - `VariableAutocompleteLineEdit` and `VariableAutocompleteDelegate` are implemented inside `pypost/ui/widgets/mcp_server_headers_table.py`.
   - Other tabular or text input editors across PyPost (e.g., URL query parameters table, request headers table, auth bearer token fields) would benefit from the same inline `{{ VAR }}` autocompletion functionality.
   - *Improvement*: Extract `VariableAutocompleteLineEdit` and its delegate into a standalone reusable module `pypost.ui.widgets.variable_autocomplete_line_edit` to eliminate code duplication across the UI layer.

2. **Hardcoded Styling & Palette Constants**:
   - Visual feedback colors (`#b00020` for structural errors, `#e65100` for advisory warnings) and popup dimensions (`180px` minimum width, `160px` maximum height, `24px` row item height) are hardcoded directly in Python widget methods.
   - *Improvement*: Centralize color constants into PyPost's UI theme/palette tokens or QSS stylesheets to ensure proper contrast adjustments across future dark/light theme switching and high-DPI scaling.

3. **Hardcoded Column Index in `VariableAutocompleteDelegate`**:
   - `VariableAutocompleteDelegate` hardcodes column 1 (`index.column() == 1`) as the only column receiving variable autocompletion.
   - *Improvement*: Make the target variable column(s) configurable via a constructor argument (e.g. `columns: tuple[int, ...] = (1,)`) to facilitate reuse across tables with different schema layouts.

## Missing Tests

1. **Rapid Focus Changes and Window Deactivation During Active Autocomplete**:
   - Current tests in `tests/test_mcp_server_headers_table.py` cover popup triggering, candidate filtering, keyboard navigation (Up, Down, Enter, Tab, Escape), and item selection.
   - Additional edge-case unit tests could be added to simulate rapid focus switching across table cells (Tab / Shift-Tab) and OS-level window deactivation / Alt-Tab while the autocomplete popup is displayed to verify clean dismissal under all windowing states.

2. **Cross-Platform Window Manager & International IME Keystroke Handling**:
   - Autocomplete navigation is tested with standard Qt Key events. Testing under international IME (Input Method Editor) composition (where keystrokes are composed before being committed) and platform-specific window manager grabs (e.g., Wayland / X11 grab semantics) could be added to an extended integration suite.

3. **Table Navigation via Keyboard (Cell Traversal & F2 Inline Editing)**:
   - Tests assert row addition, row removal, and data round-tripping. Specialized tests verifying arrow-key table cell traversal and F2 / double-click edit activation would further safeguard keyboard accessibility.

4. **Test Timeout Declarations (Verification)**:
   - Both test modules touched by this task declare explicit module-level timeouts adhering to the `do-testing` standard:
     - `tests/test_mcp_server_headers_table.py`: `pytestmark = pytest.mark.timeout(60)`
     - `tests/test_mcp_servers_dialog.py`: `pytestmark = pytest.mark.timeout(60)`
   - No tests are missing timeout markers (**ZERO BLOCKERS**).

## Performance Concerns

1. **Large Environment Variable Sets (> 1,000 Variables)**:
   - When an environment contains an exceptionally large number of variables (> 1,000 keys), candidate filtering via case-insensitive list comprehension (`[v for v in self._variables if v.upper().startswith(token.upper())]`) and populating `QListWidget` synchronously on each keystroke could cause minor typing latency.
   - *Mitigation for future*: Introduce a result limit (e.g., display top 30 matching candidates) and utilize a prefix trie or virtualized list model for environments with thousands of entries.

2. **Validation on Bulk Row Updates**:
   - In `set_data()`, every row change emits events that trigger row validation. While imperceptible for typical header configurations (< 20 entries), bulk importing of very large header payloads should batch or temporarily suppress intermediate validation calls.

## Follow-up Tasks

1. **PYPOST-1243** (Priority: Medium, 3 SP): Extract `VariableAutocompleteLineEdit` and `VariableAutocompleteDelegate` into a standalone, reusable UI component in `pypost/ui/widgets/variable_autocomplete_line_edit.py` for shared use in query parameters, headers, and request body editors.
   - Jira: [PYPOST-1243](https://pypost.atlassian.net/browse/PYPOST-1243)
2. **PYPOST-1244** (Priority: Low, 2 SP): Add candidate display limit (e.g. top 30 matches) and prefix trie indexing to `VariableAutocompleteLineEdit` to optimize autocompletion responsiveness for environments with > 1,000 variables.
   - Jira: [PYPOST-1244](https://pypost.atlassian.net/browse/PYPOST-1244)
3. **PYPOST-1245** (Priority: Low, 2 SP): Centralize validation palette colors and popup geometry constants into shared UI theme tokens and QSS stylesheets to support custom theme styling and high-DPI scaling.
   - Jira: [PYPOST-1245](https://pypost.atlassian.net/browse/PYPOST-1245)
4. **PYPOST-1246** (Priority: Low, 2 SP): Add headless Qt integration tests simulating rapid cell focus shifts, IME input composition, and OS window deactivation while the autocomplete popup is open.
   - Jira: [PYPOST-1246](https://pypost.atlassian.net/browse/PYPOST-1246)

### Pre-existing Failures Found During Full-Suite Run

The following failures occur in the broad test suite and static type analysis but are unrelated to this task's changes (`pypost/ui/widgets/mcp_server_headers_table.py`, `pypost/ui/dialogs/mcp_servers_dialog.py`, and `tests/test_mcp_server_headers_table.py`). All are tracked under existing Jira issues:

| Verdict | Test / Gate | Cause | Jira |
| --- | --- | --- | --- |
| NON-BLOCKER — pre-existing | `tests/test_environment_export.py::test_write_encrypted_export_file_round_trips_through_import` | Encrypted export round-trip failure | [PYPOST-1232](https://pypost.atlassian.net/browse/PYPOST-1232) |
| NON-BLOCKER — pre-existing | `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir` | E402 findings in untouched tests (`test_examples_modernization*.py`, `test_ui_library_manager.py`) | [PYPOST-1233](https://pypost.atlassian.net/browse/PYPOST-1233) |
| NON-BLOCKER — pre-existing | `tests/test_main_window_alert_reload.py` | Qt worker thread teardown failure under parallel execution | [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) |
| NON-BLOCKER — pre-existing | `make typecheck` gate | Mypy baseline drift (201 baseline vs 240 current) across untouched modules | [PYPOST-1241](https://pypost.atlassian.net/browse/PYPOST-1241) |


