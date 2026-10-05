# PYPOST-1116: Fix xfail and XPASS outcome reporting in duration report pytest plugin

## Goals

Test reporting fidelity is a critical foundation for engineering velocity and software
quality. When tests are marked as expected failures (`xfail`), pytest distinguishes between
tests that fail as expected (`XFAIL`) and tests that unexpectedly pass (`XPASS`).

In this repository, the test duration reporting plugin
(`tests/_pytest_plugins/duration_report.py`) intercepts test reporting to format per-test
elapsed durations. However, it currently misclassifies `xfail` and `XPASS` test results as
ordinary skips and passes:
1. An `XPASS` (unexpected pass) is reported as a standard `PASSED` / `1 passed`. This
   masks the signal that an underlying bug has been resolved or that conditions changed,
   preventing engineers from updating test expectations or cleaning up obsolete annotations.
2. An `XFAIL` (expected failure) is reported as a standard `SKIPPED` / `1 skipped` with no
   reason text. This makes expected failures indistinguishable from unexecuted or
   conditionally skipped tests in test outputs and summaries.
3. Summary reporting options such as `-rA`, `-ra`, or `-rs` cause unhandled internal
   reporting crashes (`AssertionError`) because `xfail` report structures do not match the
   expected shape of standard skip reports.

The business goal is to restore accurate test outcome reporting across the test suite so
that expected failures and unexpected passes are properly reported, counted, and summarized,
without sacrificing the per-test execution duration visibility provided by the plugin.

## User Stories

- As a **developer**, I want tests marked with expected failures (`xfail`) that fail to be
  clearly reported as `XFAIL` rather than generic skips, so that I can see the reason for
  the expected failure and distinguish them from genuine skipped tests.
- As a **developer**, I want tests marked with expected failures (`xfail`) that pass (`XPASS`)
  to be reported as `XPASS` rather than regular passes, so that I am alerted when an
  underlying defect has been fixed and can remove or update obsolete `xfail` annotations.
- As a **CI engineer**, I want test status summaries and terminal flags (such as `-ra` or
  `-rA`) to execute cleanly without crashes or assertions, ensuring reliable CI test runs and
  failure triaging.
- As a **maintainer**, I want the per-test duration annotation (`[<duration>]`) to continue
  appearing for all test outcomes, preserving execution timing visibility without corrupting
  pytest's native test outcome taxonomy.

## Definition of Done

- [ ] Implementation language is recorded as Python.
- [ ] Expected failure tests (`xfail`) that fail during the call phase are reported as `XFAIL`
  (short letter `x`), categorized as `xfailed` in session statistics, and display their
  duration.
- [ ] Expected failure tests (`xfail`) that pass during the call phase under non-strict mode
  are reported as `XPASS` (short letter `X`), categorized as `xpassed` in session statistics,
  and display their duration.
- [ ] Genuine passed tests continue to be reported as `PASSED` (short letter `.`) with
  formatted call duration.
- [ ] Genuine failed tests continue to be reported as `FAILED` (short letter `F`) with
  formatted call duration.
- [ ] Genuine skipped tests continue to be reported as `SKIPPED` (short letter `s`).
- [ ] Test status reporting with summary flags (`-rA`, `-ra`, `-rs`, `-rx`, `-rX`) functions
  cleanly without raising `AssertionError` or unhandled exceptions.
- [ ] The post-session top-N slowest tests summary continues to function as expected.
- [ ] Automated regression tests verify accurate classification and formatting of `passed`,
  `failed`, `skipped`, `xfailed`, and `xpassed` outcomes.
- [ ] Existing repository test suite passes with `make check`.

## Task Description

### Background and Problem Statement

The repository utilizes an in-tree pytest plugin (`tests/_pytest_plugins/duration_report.py`)
to show human-readable test run durations in verbose terminal output and summarize the top
slowest tests at session completion.

When formatting status words during test reporting, the plugin inspects the outcome of the
test report. However, pytest's internal reporting protocol classifies both regular skips and
expected failures with the underlying outcome status of `skipped` (attaching `wasxfail`
metadata for expected failures), and non-strict expected failures that pass with the underlying
outcome status of `passed` (also attaching `wasxfail` metadata).

Because the plugin does not account for `wasxfail` metadata, it overrides pytest's native
classification, causing:
- Loss of `XPASS` visibility (coerced to plain `PASSED`).
- Loss of `XFAIL` visibility and reason text (coerced to plain `SKIPPED`).
- Terminal summary failures when pytest attempts to process expected failure reports using skip
  formatting logic.

### Scope

**In Scope:**
- Identifying all test outcome categories that need proper classification and duration
  formatting: `passed`, `failed`, `skipped`, `xfailed`, and `xpassed`.
- Supporting test reporting across standard and summary reporting modes (e.g., verbose mode,
  compact progress letters, and `-r` summary flags).
- Preserving the plugin's core value: per-test execution duration formatting and slowest tests
  session summary.
- Comprehensive test coverage for test reporting behaviors under all supported outcome
  categories.

**Out of Scope:**
- Modifying test assertion logic or markers in application test suites (e.g., altering tests in
  `tests/test_agent_dialog_settle_teardown_stress.py`).
- Changing the calculation or formatting rules of `format_duration`.
- Modifying duration audit scripts (`scripts/audit_test_durations.py`) or CI duration evidence
  scripts.

### Functional Requirements

1. **Outcome Differentiation**:
   - The test reporting system must distinguish between genuine skips and expected failures
     (`xfail`).
   - The test reporting system must distinguish between genuine passes and unexpected passes
     (`xpass`).
2. **Terminal Verbose Display**:
   - Tests resulting in `XFAIL` must display the word `XFAIL` followed by the duration tag
     (e.g., `XFAIL [12ms]`).
   - Tests resulting in `XPASS` must display the word `XPASS` followed by the duration tag
     (e.g., `XPASS [12ms]`).
   - Standard outcomes (`PASSED`, `FAILED`, `SKIPPED`, `ERROR`) must preserve their existing
     word and duration formats.
3. **Progress Letters**:
   - Progress indicators must show standard characters: `.` for pass, `F` for fail, `s` for
     skip, `x` for xfail, `X` for xpass, and `E` for error.
4. **Session Summary and Statistics**:
   - Pytest session summary lines must accurately aggregate counts for each category
     (e.g., `1 passed, 1 xfailed, 1 xpassed`).
   - Summary detail flags (such as `-ra`, `-rs`, `-rx`, `-rX`) must correctly display failure
     and skip reasons without runtime crashes.

### Non-Functional Requirements

- **Compatibility**: Must be compatible with pytest versions used across supported CI
  environments (Python 3.11 and Python 3.13).
- **Performance**: Test reporting hook overhead must remain negligible so as not to inflate
  suite execution duration.
- **Reliability**: Must not raise exceptions or interrupt test session execution under any
  valid combination of pytest CLI options.

### Main Entities

- **Test Report**: The record of a test execution phase (setup, call, teardown), containing
  status, duration, and outcome metadata (including `wasxfail` when an expected failure
  condition is met).
- **Test Outcome Category**: The classification used for reporting and aggregation (`passed`,
  `failed`, `skipped`, `xfailed`, `xpassed`, `error`).
- **Status Word**: The formatted human-readable string displayed in verbose mode, combining the
  capitalized outcome category and the elapsed duration.
- **Status Letter**: The single-character indicator printed in default (non-verbose) mode.
- **Duration Summary**: The end-of-session table reporting the top-N longest test executions.

## Q&A

- **Q: Why is Python designated as the implementation language?**
  A: The target plugin `tests/_pytest_plugins/duration_report.py`, the test configuration
  `tests/conftest.py`, and the entire test harness are written in Python.
- **Q: Does this issue affect all tests in the repository?**
  A: The plugin is loaded repo-wide via `tests/conftest.py`. It affects any test that uses
  `@pytest.mark.xfail` or any test run invoked with `-r` reporting flags.
- **Q: Why was this issue not caught earlier?**
  A: Most repository tests are standard pass/fail tests. The issue became evident during
  PYPOST-1040 when an explicit `xfail(strict=False)` marker was added for diagnosis, and was
  documented as tech debt in `ai-tasks/PYPOST-1040/60-tech-debt.md`.
- **Q: Should the plugin format durations during setup or teardown phases?**
  A: No. Duration tracking and verbose status words are specifically targeted at the `call`
  phase, matching pytest `--durations` semantics and existing plugin behavior. Non-call phases
  should continue standard pytest handling.
