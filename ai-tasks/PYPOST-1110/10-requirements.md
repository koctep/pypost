# PYPOST-1110: Migrate test_mcp_controls_presenter.py off its local qapp() fixture onto shared conftest qapp

## Goals

The project test suite enforces a single, shared way of creating a `QApplication` instance for
Qt-based tests (the module-scoped `qapp` fixture in `tests/conftest.py`), instead of each test
module defining its own local `qapp()` fixture. Multiple local fixtures risk creating conflicting
or duplicate `QApplication` instances, which is a known source of flaky/undefined behavior in
PySide/PyQt test suites. Keeping every test module aligned on the shared fixture protects the
reliability of the whole automated test suite that the team depends on for confidence when
shipping changes.

This specific task exists because a guard test
(`tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`)
was observed failing during another task's (PYPOST-1083) full-suite run, at base commit
`2b770ada`, flagging `tests/test_mcp_controls_presenter.py` as still defining its own local
`qapp()` fixture. The business goal is to restore/keep that guard test green, i.e., ensure no test
module reintroduces a local `qapp()` fixture or `setUpClass`-based `QApplication`, keeping the
whole suite's Qt test setup consistent and trustworthy.

## User Stories

- As a developer running the automated test suite, I want every Qt-based test module to use the
  single shared `qapp` fixture, so that I don't hit flaky or inconsistent `QApplication` behavior
  across test files.
- As a developer reviewing test suite health, I want a guard test that fails loudly if a module
  reintroduces a local `qapp()` fixture, so that the shared-fixture convention doesn't silently
  regress.

## Definition of Done

- `tests/test_mcp_controls_presenter.py` does not define a local `qapp()` fixture; it relies on
  the shared `qapp` fixture from `tests/conftest.py`.
- `tests/test_mcp_controls_presenter.py` does not import unused symbols (`sys`, `QApplication`)
  that existed only to support the local fixture.
- The guard test
  `tests/test_suite_qapp_alignment.py::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  passes.
- No behavioral change to `McpControlsPresenter` or its production code — this is a test-suite
  consistency fix only.

## Task Description

**Problem**: A guard test asserts that no test module in the suite defines its own local `qapp()`
fixture or a `setUpClass`-based `QApplication`; all Qt tests must use the shared, module-scoped
`qapp` fixture defined once in `tests/conftest.py`. At base commit `2b770ada`, this guard test
failed because `tests/test_mcp_controls_presenter.py` still had its own local `qapp()` fixture
(with the accompanying `sys` and `QApplication` imports needed only for that fixture), diverging
from the precedent already established for other test modules (PYPOST-830/883/884/885/886, and
matching `tests/test_presenter_font_inheritance.py`'s pattern).

**Constraints**: This is a debt/consistency task (Type: Debt, Priority: Low, 1 story point) with
no intended change to application behavior — only test-file structure.

**Verification finding (already satisfied)**: Independent verification performed as part of this
task's own Step 1 shows the underlying business requirement is **already met on the current `dev`
HEAD**, via unrelated prior work:

- `git show 494eb857 -- tests/test_mcp_controls_presenter.py` shows commit `494eb857`
  ("fix(tests): PYPOST-1176 restore green test suite on dev") removed the local `qapp()` fixture
  and the now-unused `sys` and `QApplication` imports from `tests/test_mcp_controls_presenter.py`,
  performing the exact mechanical fix this ticket describes (as part of a broader, unrelated
  test-suite-greening task).
- Reading the current `tests/test_mcp_controls_presenter.py` on `dev` HEAD confirms: no local
  `qapp()` fixture is defined, and neither `sys` nor `QApplication` is imported; the module's
  tests take `qapp` as a fixture parameter, resolved from `tests/conftest.py`.
- Running `PYTEST_ARGS="tests/test_suite_qapp_alignment.py -v" make test` on `dev` HEAD produced:
  `[ 1/1 ] tests/test_suite_qapp_alignment.py ... PASSED (1.40s)` and summary
  `Total Files: 1 | Passed: 1 | Failed: 0 | Skipped: 0`.

**Conclusion**: The Definition of Done above is already satisfied on `dev` HEAD. No further
production or test code change is required for PYPOST-1110 itself. This document, together with
the verification evidence above, is the paper trail needed to close the Jira ticket as
already-resolved-by-prior-work, referencing commit `494eb857` (PYPOST-1176) as the commit that
fixed it.

## Q&A

- **Q: Is a code change still needed for this ticket?**
  A: No. Verification on `dev` HEAD shows the local `qapp()` fixture and its supporting imports
  were already removed by commit `494eb857` (PYPOST-1176), and the guard test
  (`tests/test_suite_qapp_alignment.py`) passes. See Task Description above for full evidence.
- **Q: Why keep going through the Top-Down steps if the fix is already applied?**
  A: To produce a verifiable, documented paper trail (this requirements doc plus the roadmap)
  confirming the guard test is green and referencing the commit that resolved it, so the Jira
  ticket can be closed with evidence rather than closed on assumption alone.
