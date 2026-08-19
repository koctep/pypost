# PYPOST-1081: Restore Log File Capture for CI Error Guardrail Protection

## Programming Language

Python is the implementation language for the application, testing infrastructure, and verification tooling. English Markdown records the requirements and workflow artifacts.

## Goals

The continuous integration (CI) test workflow includes a log guardrail verification gate designed to protect release stability by auditing runtime ERROR logs and ensuring total error counts stay within approved baseline margins.

Currently, during full-suite test execution, test log file capture is silenced, producing an empty (0-byte) log file. Consequently, the downstream log guardrail verification step inspects an empty log, reports zero errors, and passes vacuously regardless of how many unexpected errors were actually emitted during test runs.

**Business goal:** Restore reliable test log capture across all test suite executions so that the CI error guardrail operates as an active, trustworthy release gate that accurately detects unapproved runtime errors, while establishing an accurate, curated baseline of expected error emissions.

## User Stories

- As a **release steward**, I want the CI log guardrail to actively verify all emitted error logs during automated test runs, so that unintended runtime regressions prevent release instead of passing silently.
- As a **maintainer**, I want test log capture to remain reliably active regardless of test suite collection order or module composition, so that individual test files cannot inadvertently blind CI observability gates.
- As a **developer**, I want intentional error emissions triggered by error-handling or negative tests to be documented in a curated allowlist with a clear margin, so valid negative tests pass without false alarms.
- As a **quality engineer**, I want confidence that test log capture functions identically in both isolated test slices and full test suite executions, ensuring robust regression protection.

## Definition of Done

- [ ] Test log capture reliably captures runtime warning and error events across all test suites without being silenced or truncated by test collection or module imports.
- [ ] The CI test log guardrail verification actively evaluates the captured log file against the error allowlist and enforces the baseline error count and margin.
- [ ] Any previously masked runtime ERROR logs uncovered by restoring capture are triaged, curated into the expected log allowlist with clear rationale, or resolved.
- [ ] Full test suite execution and test log guardrail verification pass deterministically in both local environments and CI pipelines without vacuous passes.
- [ ] Automated regression tests verify that log capture remains active regardless of test collection sequence.
- [ ] No protective guardrail or verification check is removed, skipped, or disabled to achieve a passing state.

## Task Description

**Problem:** The CI test workflow executes the test suite with log file capture enabled (`--log-file=pytest.log`) and runs `scripts/verify_test_log_guardrails.py` to inspect the log. On full-suite runs, collecting certain test modules silences log capture for the remainder of the session. As a result, `pytest.log` is empty (0 bytes), and the verification script reports `ERROR count: 0 (max allowed: 77)` and exits 0, providing zero protection against runtime errors.

**Scope (in):**
- Restoring reliable log file capture during test execution across all test suites and collection orders.
- Ensuring test execution logging captures runtime warning and error events without session-level silencing.
- Auditing and curating the expected error allowlist (`tests/expected_log_allowlist.yaml`) to account for genuine, expected errors that become visible once capture is restored.
- Adding automated verification tests to ensure test log capture remains active and cannot be silenced by test ordering.
- Verifying that CI workflow and local verification commands pass with active error auditing.

**Scope (out):**
- Redesigning the core application logging architecture or changing user-facing log formats.
- Removing or weakening valid error-handling and negative test cases.
- Modifying unrelated CI workflow jobs (such as dependency audits, license checks, or live smoke tests).

**Constraints and assumptions:**
- The solution must be implemented in Python and remain compatible with the project's supported Python versions (3.11 and 3.13).
- Must operate within pytest and GitHub Actions CI environments without requiring external runtime dependencies.
- Changes to the error allowlist and baseline count must reflect verified, legitimate error emissions with documented rationale.

## Main Entities and Interactions

- **CI Test Workflow**: The automated build pipeline that runs test suites and executes quality gates before accepting changes.
- **Test Log Capture**: The logging capture mechanism that records runtime logs emitted during test execution into a designated log file.
- **Log Guardrail Verifier**: The verification tool that inspects captured test logs, validates emitted errors against an approved allowlist, and enforces baseline limits.
- **Error Allowlist and Baseline**: The configuration defining approved error message patterns, loggers, and allowed error margin thresholds.
- **Test Suite**: The collection of automated tests that exercises application functionality, including positive and negative scenarios.

The CI Test Workflow invokes the Test Suite with Test Log Capture active. Emitted runtime events are written to the log file. Upon test completion, the Log Guardrail Verifier evaluates the log file against the Error Allowlist and Baseline. If unlisted errors occur or the error count exceeds the allowed threshold, the gate fails, preventing unvetted regressions from reaching release.

## Functional Requirements

1. **Deterministic Log Capture**: The test execution runner must consistently write all emitted log events at or above the configured log level to the target log file, regardless of which test modules are loaded, collected, or executed.
2. **Session Persistence**: Initializing or importing any test module must not reset, detach, or disable the root logger's active file capture handlers for subsequent tests.
3. **Active Guardrail Verification**: The log guardrail verification script must fail when unlisted ERROR events are present in the log or when the total ERROR count exceeds the baseline plus allowed margin.
4. **Baseline & Allowlist Curation**: The expected log allowlist and baseline error count must accurately reflect all legitimate, approved ERROR emissions from the full test suite.
5. **Regression Verification**: An automated test must verify that log capture functions correctly and cannot be muted by test collection order.

## Non-Functional Requirements

- **Reliability**: Test log capture and guardrail verification must yield deterministic results across repeated runs and differing test orders.
- **Transparency**: All allowed error events must have identifiable sources and clear documentation in the allowlist.
- **Performance**: Restoring complete log capture must not introduce noticeable execution overhead or increase test suite run times beyond normal duration budgets.
- **Safety**: No error check may be silenced, ignored, or bypassed.

## Q&A

**Q:** Why is this task needed if CI is currently passing?
**A:** The CI pass is vacuous because the log file being inspected is empty (0 bytes). The guardrail currently protects against zero errors, allowing arbitrary runtime ERRORs to enter the codebase unnoticed.

**Q:** What happens when log capture is restored?
**A:** Emitted ERROR logs from negative tests and real runtime events will now appear in `pytest.log`. These errors will be evaluated against the allowlist. Legitimate expected errors will be curated into `tests/expected_log_allowlist.yaml` with appropriate baseline counts, while any unintended errors can be identified and remediated.

**Q:** Does this require changing how the application itself logs events?
**A:** No. The task focuses on ensuring the test runner's log capture mechanism reliably persists emitted logs during test execution and that CI properly enforces the guardrail.

**Q:** Why was this defect classified as pre-existing in PYPOST-1071?
**A:** Investigation during PYPOST-1071 identified that `tests/test_agent_lifecycle_smoke.py` silences `--log-file` capture when collected. This behavior existed prior to PYPOST-1071 changes and was logged as technical debt follow-up F5 (item D11) for dedicated remediation.
