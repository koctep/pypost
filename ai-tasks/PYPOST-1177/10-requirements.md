# PYPOST-1177: Fix parallel Qt crash in test_main_window_curl_copied_status_bar

## Goals

PyPost’s default quality gate runs the full test suite in parallel (`make test`). A test that
terminates the Python process with a fatal error (Bus error or segmentation fault) under that
runner blocks CI, hides real regressions behind infrastructure noise, and erodes maintainer trust
in automated checks.

During [PYPOST-1176](https://pypost.atlassian.net/browse/PYPOST-1176) (restore green test suite
on `dev`), `tests/test_main_window.py::TestMainWindow::test_main_window_curl_copied_status_bar`
was recorded as a **NON-BLOCKER** parallel Qt crash: it passes when the file is run alone but
reliably kills the worker under the parallel runner. PYPOST-1177 closes that debt so the parallel
suite is stable and the copy-to-clipboard status-bar behavior stays covered by automated tests.

The business goal is **reliable parallel CI** plus **preserved regression coverage** for the
user-visible feedback when a curl command is copied from the History panel — not a redesign of
MainWindow or History persistence.

## User Stories

- As a **maintainer**, I want `make test` to finish without fatal process crashes from
  `test_main_window_curl_copied_status_bar`, so that parallel CI remains a trustworthy quality
  gate.
- As a **maintainer**, I want the curl-copy status-bar behavior to remain covered by automated
  tests after the fix, so that regressions in that user feedback path are still caught.
- As a **maintainer**, I want MainWindow integration tests in `tests/test_main_window.py` to
  follow the same isolation conventions as sibling tests in that module, so that future tests do
  not reintroduce parallel instability.
- As a **developer running tests locally**, I want the same test to pass both in isolation and as
  part of the full parallel suite, so that local and CI results agree.

## Definition of Done

PYPOST-1177 is done when:

1. `make test` completes with exit code 0 under the parallel test runner — no Bus error
   (exit code −7) or segmentation fault (exit code −11) attributable to
   `test_main_window_curl_copied_status_bar`.
2. `tests/test_main_window.py::TestMainWindow::test_main_window_curl_copied_status_bar` passes
   when run alone **and** when run as part of the full suite.
3. `make check` passes.
4. The test still verifies that emitting the History panel **curl copied** action results in the
   status bar showing **"Copied to clipboard"** for 3000 ms (same product assertion as today).
5. Existing unit coverage in `tests/test_main_window_signals.py` for curl-copy signal wiring
   continues to pass without regression.
6. No intentional change to production MainWindow or History panel user-facing behavior beyond
   what is required to satisfy the acceptance criteria above.

## Task Description

### Programming Language

Python — PyPost application code and pytest test suite (PySide6/Qt offscreen GUI tests).

### Problem

The integration test `test_main_window_curl_copied_status_bar` constructs a real `MainWindow`
with heavier initialization than sibling tests in the same file. Under the parallel test runner
(`scripts/run_parallel_tests.py`), that setup interacts with real asynchronous history loading
and Qt offscreen rendering across worker processes, producing fatal process errors. The failure
does not reproduce when the test file is executed in isolation.

Observed failure modes (from Jira):

- Fatal Python error: Bus error (exit code −7) or Segmentation fault (exit code −11)
- Background activity during crash: history load on a worker thread while the main thread
  initializes UI theme/settings during `MainWindow` construction

Reproduction commands documented in Jira:

- Fails under parallel gate: `make test`
- Passes in isolation:
  `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_main_window.py -v`

### Business Need

Maintainers and CI depend on a green parallel suite. A single crashing test forces investigation
of infrastructure failures instead of product regressions, delays merges, and leaves a documented
debt item from PYPOST-1176 unresolved. The product behavior under test — status bar confirmation
after copying curl from History — is a small but real UX signal; coverage must not be dropped
silently when stabilizing the test.

### Scope (this task)

- Stabilize `test_main_window_curl_copied_status_bar` for parallel execution.
- Preserve the status-bar assertion for the curl-copy feedback path.
- Align test boundaries with established patterns in the same test module where applicable.

### Out of Scope

- Fixing other NON-BLOCKER parallel failures noted in
  `ai-tasks/PYPOST-1176/60-tech-debt.md` (MCP registry / WebSocket lifecycle flakiness) —
  separate follow-ups.
- New end-to-end GUI automation beyond existing unit and integration tests.
- Feature changes to History persistence, curl copy behavior, or status bar messaging in
  production code unless strictly required to meet acceptance (expected to be test-only).
- Broad refactors of `MainWindow` construction or the parallel test runner infrastructure.

### Relationship to Existing Coverage

| Test | Location | Focus |
| --- | --- | --- |
| `test_wire_presenter_signals_connects_curl_copied_status_bar` | `tests/test_main_window_signals.py` | Signal wiring unit test (`wire_presenter_signals`) |
| `test_main_window_curl_copied_status_bar` | `tests/test_main_window.py` | Integration: real `MainWindow` emits `curl_copied` → status bar message |

Project testability docs (`doc/dev/testability.md`) list both. The unit test already locks
signal wiring; the integration test adds a full-construction path. PYPOST-1177 must not remove
meaningful coverage — it must make the integration path safe under parallel CI.

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Parallel test runner** | CI/local gate that executes test files in isolated worker processes |
| **MainWindow integration test** | Automated check that constructs the main application window in tests |
| **History panel curl copy action** | User action that copies a curl command from request history |
| **Status bar feedback** | Transient message confirming clipboard copy ("Copied to clipboard") |
| **Maintainer / CI pipeline** | Consumer of a stable `make test` / `make check` outcome |

Interaction overview:

1. Maintainer or CI runs the full parallel test suite.
2. The integration test builds a MainWindow test fixture and simulates the curl-copy signal.
3. The test expects the status bar to show the copy confirmation message.
4. Today, step 2 can crash the worker under parallel load; after PYPOST-1177, the suite completes
   and the assertion still holds.

## Functional Requirements

- **FR-1:** The parallel test suite (`make test`) must not crash due to
  `test_main_window_curl_copied_status_bar`.
- **FR-2:** The integration test must continue to assert that the curl-copy action surfaces
  **"Copied to clipboard"** on the status bar (3000 ms duration).
- **FR-3:** MainWindow tests in `tests/test_main_window.py` that construct `MainWindow` must
  respect the module’s established test-isolation boundaries so unrelated subsystems (e.g. real
  history file loading during window construction) do not run unless the test explicitly targets
  them.
- **FR-4:** Unit tests in `tests/test_main_window_signals.py` for curl-copy wiring must remain
  passing.

## Non-Functional Requirements

- **NFR-1 Reliability:** The fix must hold under the default parallel runner used by `make test`,
  not only under single-process pytest invocation.
- **NFR-2 Minimal scope:** Prefer the smallest change that restores parallel stability; avoid
  unrelated MainWindow or History refactors.
- **NFR-3 Test hygiene:** Tests must comply with project timeout rules (`pytest.mark.timeout` at
  module, class, or test level — already present on `TestMainWindow`).
- **NFR-4 Gate parity:** Local `make check` and CI must agree after the fix.

## Constraints and Assumptions

- Issue type: **Debt**; labels: `failing-test`, `tech-debt`; priority: **High**; estimate: **2 SP**.
- Active sprint: **MainWindow Test Fix** (board 34).
- Discovered during PYPOST-1176 parallel `make test` on `dev`; base commit context:
  `494eb857` (PYPOST-1176 green suite restore).
- Sibling tests in `tests/test_main_window.py` already inject a stand-in history manager and
  patch heavy initialization paths — the failing test is the outlier in that module.
- Signal wiring for `curl_copied` → status bar is explicitly covered in
  `tests/test_main_window_signals.py`; integration test scope can be narrowed to what full
  construction adds beyond that unit test, but the status-bar assertion must remain.
- Approval for Step 1 artifacts is deferred to the orchestrator review gate (autonomous run).

## Q&A

| Question | Answer |
| --- | --- |
| Why fix if the test passes in isolation? | `make test` uses the parallel runner; that is the authoritative CI gate. Isolation-only green is insufficient. |
| Is signal wiring still tested elsewhere? | Yes — `test_wire_presenter_signals_connects_curl_copied_status_bar` in `tests/test_main_window_signals.py`. |
| Can the integration test be deleted? | Only if equivalent coverage remains. Prefer stabilizing it; deletion requires explicit acceptance that integration-level assertion is redundant. |
| Does this change user-visible behavior? | Not expected. Scope is test reliability and preserved regression coverage. |
| What about other parallel Qt crashes from PYPOST-1176? | Out of scope for PYPOST-1177; tracked separately as NON-BLOCKER debt in `ai-tasks/PYPOST-1176/60-tech-debt.md`. |

## References

- [PYPOST-1177](https://pypost.atlassian.net/browse/PYPOST-1177) — this debt issue
- [PYPOST-1176](https://pypost.atlassian.net/browse/PYPOST-1176) — parent context; NON-BLOCKER discovery
- `tests/test_main_window.py` — failing integration test and sibling patterns
- `tests/test_main_window_signals.py` — curl-copy signal wiring unit test
- `doc/dev/testability.md` — coverage table for MainWindow signal tests
- `ai-tasks/PYPOST-1176/60-tech-debt.md` — original NON-BLOCKER entry
