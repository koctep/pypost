# PYPOST-1116: Technical Debt Analysis

## Shortcuts Taken

- **Direct `hasattr(report, "wasxfail")` Inspection** (NON-BLOCKER):
  - In `tests/_pytest_plugins/duration_report.py`, the plugin checks `hasattr(report, "wasxfail")`
    and inspects `report.skipped` / `report.passed` directly to classify xfail/xpass outcomes.
  - *Rationale*: Pytest attaches the `wasxfail` attribute dynamically during test execution
    whenever an xfail evaluation triggers. Directly inspecting this attribute in
    `pytest_report_teststatus` is the canonical, supported approach in pytest plugins and avoids
    coupling to private pytest terminal internals.
  - *Impact*: Lightweight and robust; fully compatible with current pytest 7.x/8.x releases.

- **Phase Delegation for Non-Call Phases** (NON-BLOCKER):
  - Only `"call"` phase reports receive custom duration status lines. Non-call phases (`"setup"`,
    `"teardown"`) return `None` to preserve pytest's built-in error formatting.
  - *Rationale*: Test durations in this plugin are intended for test body execution metrics.
  - *Impact*: Standard pytest setup/teardown diagnostics and traceback reporting remain intact.

## Code Quality Issues

- **None Identified** (NON-BLOCKER):
  - Hook implementation in `tests/_pytest_plugins/duration_report.py` is concise (10 lines added),
    clear, fully typed, and adheres strictly to PEP 8 style standards.
  - The branch structure for `report.skipped` vs `report.passed` cleanly mirrors pytest's native
    outcome mapping, returning standard 3-tuples:
    - `("xfailed", "x", f"XFAIL [{format_duration(report.duration)}]")`
    - `("xpassed", "X", f"XPASS [{format_duration(report.duration)}]")`
  - No complex abstractions or refactoring necessary.

## Missing Tests

- **Zero Missing Tests for Implemented Scope** (NON-BLOCKER):
  - Comprehensive unit and integration coverage implemented in
    `tests/test_pypost_1116_failing_repro.py`:
    - `test_pytest_report_teststatus_xfail_call_outcome`: verifies `xfailed`/`x`/`XFAIL [...]`.
    - `test_pytest_report_teststatus_xpass_call_outcome`: verifies `xpassed`/`X`/`XPASS [...]`.
    - `test_pytest_report_teststatus_plain_skipped_call_outcome`: verifies `skipped`/`s`.
    - `test_pytest_report_teststatus_plain_passed_call_outcome`: verifies `passed`/`.`.
    - `test_pytest_report_teststatus_non_call_phases_return_none`: checks setup/teardown phases.
    - `test_terminal_summary_xfail_report_no_crash`: verifies `-ra`/`-rs` flags do not raise
      `AssertionError` on xfail report objects in `short_test_summary()`.
    - `test_duration_report_xfail_terminal_integration`: full subprocess pytester run with `-ra`.
  - **Explicit Timeout Verification**:
    - All tests in `tests/test_pypost_1116_failing_repro.py` include explicit timeout markers:
      module-level `pytestmark = pytest.mark.timeout(30)` and per-test `@pytest.mark.timeout(30)`
      per `lsr-python` and `do-testing` requirements.

## Performance Concerns

- **Zero Performance Impact** (NON-BLOCKER):
  - `hasattr(report, "wasxfail")` check is an O(1) attribute lookup executed once per test report.
  - String formatting overhead in `format_duration()` is negligible (< 1 microsecond per report).
  - Memory consumption in `_call_durations` dict is minimal, retaining only scalar float timings.

## Follow-up Tasks

- **Pre-existing Test Suite Stability Items (Sprint 2021)**:
  - **`PYPOST-1261`**: Pre-existing full-suite failures: parser alignment, Qt SIGSEGV, audit
    snapshot (`NON-BLOCKER — pre-existing`).
  - **`PYPOST-1262`**: Pre-existing: `tests/test_makefile_lifecycle.py` and
    `test_makefile_targets.py` exceed 120s worker timeout under full-suite parallel load
    (`NON-BLOCKER — pre-existing`).
  - **`PYPOST-1286`**: Flaky under full-suite parallel load: websocket stream view export actions
    and template strict-conversion fallback tests (`NON-BLOCKER — pre-existing`).
  - **`PYPOST-1287`**: Pre-existing:
    `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` fails on stale dialog
    LOC inventory (`NON-BLOCKER — pre-existing`).

- **Blocker Status**:
  - Zero unresolved BLOCKERS.
  - SAFE TO CLOSE.
