# PYPOST-1261: Pre-existing full-suite failures: parser alignment, Qt SIGSEGV, audit snapshot

## Goals

Automated testing and continuous integration (CI) quality gates are fundamental to development
velocity, code reliability, and release stability in PyPost. When pre-existing test failures
exist in the repository test suite, they undermine the trustworthiness of `make test` and `make
check`, block pull requests, and mask newly introduced bugs.

From a user and product perspective, template expression validation is a core capability.
PyPost users construct dynamic request headers, URLs, payloads, and environment configurations
using template expressions with embedded variables and function calls (such as `{{
md5(urlencode(db)) }}`). When users inadvertently make syntax mistakes—such as missing or
mismatched parentheses in nested expressions or trailing parentheses—the system must deliver
accurate, deterministic, and helpful feedback:
- The error must clearly communicate that an argument expression is syntactically invalid
  (`invalid_argument`), rather than misleading the user into believing they passed the wrong
  number of arguments (`invalid_arity`).
- Observability and telemetry must record the true nature of validation failures during runtime
  and UI hover checks so team metrics reliably distinguish argument syntax errors from function
  signature arity mismatches.
- The test suite must execute cleanly, predictably, and without crashes under parallel
  execution, ensuring that developer quality gates and CI pipelines remain dependable.
- Repository architectural health metrics (SOLID audit baselines) must remain consistent with
  the repository state to prevent false regression alerts.

## Programming Language

- **Implementation language**: Python (per `ai-tasks/PYPOST-1261/00-roadmap.md`). PyPost is
  built with Python and PySide6/Qt.

## Business Entities

- **Template Expression**: An expression enclosed within `{{ ... }}` delimiters used by API
  designers and testers to inject dynamic values, variables, and transformed outputs into
  requests.
- **Function Call Expression**: An operation within a template expression that invokes an
  allow-listed catalog function with an input argument (for example, `md5(...)`,
  `urlencode(...)`, or `base64(...)`).
- **Nested Expression**: A hierarchical function invocation where the argument to an outer
  function call is itself another function call expression (for example, `{{ md5(urlencode(db))
  }}`).
- **Validation Outcome**: The diagnostic assessment of a template expression, communicating
  whether the expression is syntactically sound and valid, or indicating a specific failure
  category (`invalid_argument`, `invalid_arity`, `unknown_function`, `invalid_syntax`).
- **Telemetry & Observability Channel**: Diagnostic event logging and metric tracking that
  records validation failure counts, error codes, and associated function names during
  interactive editor hover states and execution stages.
- **Continuous Integration Quality Gate**: The repository verification mechanism (running
  through Make targets) that validates static analysis, test suite health, and architectural
  integrity before changes are integrated.

## User Stories

- As an API developer authoring request templates, I want clear and accurate error feedback
  when I write malformed nested function calls (such as missing a closing parenthesis in an
  inner call), so that I understand my argument syntax is invalid rather than being falsely
  told that the function was called with an incorrect number of arguments.
- As an API developer composing template functions, I want standalone function calls with
  extraneous closing parentheses (such as `{{ urlencode(db)) }}`) to be reported as invalid
  argument syntax, so that I can quickly spot and correct the syntax mistake.
- As a site reliability or observability engineer monitoring template execution, I want hover
  and runtime validation telemetry to record `invalid_argument` for malformed argument syntax,
  so that error metrics dashboards reflect actual user authoring errors without distortion.
- As a software engineer maintaining PyPost, I want `make test` to execute completely green
  without pre-existing test failures, so that I can trust test results and maintain continuous
  integration health.
- As an engineering team lead, I want parallel test execution to be stable against worker
  crashes or unhandled process termination signals (such as SIGSEGV or SIGBUS in Qt widgets),
  so that automated pipelines are robust and reproducible.
- As a software quality auditor, I want SOLID audit baseline metrics and documentation
  snapshots to match actual codebase measurements, preventing spurious gate failures.

## Definition of Done

### Functional Requirements & Error Classification
1. **Malformed Nested Expression Classification**: When a template expression contains a
   malformed nested function call (such as unclosed parentheses in an inner expression, or
   extra inner grouping parentheses), the validation error code must be `invalid_argument`
   (identifying the outer or failing function as expected by the domain contract), rather than
   `invalid_arity`.
2. **Standalone Malformed Closing Parentheses**: When a single function call contains an
   extraneous closing parenthesis within its argument list (for example, `{{ urlencode(db))
   }}`), the validation error code must be `invalid_argument`, identifying the targeted
   function.
3. **Template Service Validation Parity**: Template service validation outcomes for malformed
   nested expressions must match the expression resolver's classification, consistently
   returning `invalid_argument`.
4. **Hover Observability Metrics Alignment**: When rendering or hovering over template content
   containing malformed nested expressions, the recorded telemetry event
   (`track_template_expression_validation_failure`) must report the error code
   `invalid_argument` and the appropriate function name.
5. **Legitimate Arity Error Preservation**: Legitimate arity errors (such as providing multiple
   comma-separated arguments to single-argument functions like `{{ urlencode(a, b) }}`) must
   continue to report `invalid_arity`.

### Suite Stability & Quality Gate
6. **Parallel Test Suite Cleanliness**: Running `make test` must pass all test files without
   failures, skips from crashes, or test error regressions across the repository.
7. **Qt Worker Process Stability**: UI widget tests (including environment list widget,
   environment dialog, and export UI tests) must execute cleanly without process-level crashes
   (such as SIGSEGV exit -11 or SIGBUS exit -7) during parallel worker execution or widget
   teardown.
8. **Audit Baseline Integrity**: The SOLID audit baseline snapshot test
   (`tests/test_solid_audit_baseline.py`) must pass, with the checked-in metrics snapshot
   accurately matching measured codebase lines of code.
9. **Full Verification**: The combined repository quality gate `make check` (incorporating
   lint, test, and AI task verification) must succeed with an exit code of 0.

## Task Description

### Problem
During sprint regression testing (discovered initially during PYPOST-1236 triage), a cluster of
pre-existing full-suite test failures was cataloged:
1. **Expression Parser Classification Drift**: Mismatched parentheses in nested function
   arguments (`{{ md5(urlencode(db) }}`) and extra closing parentheses (`{{ urlencode(db)) }}`)
   were being classified by the resolver as `invalid_arity` instead of `invalid_argument`.
2. **Template Service & Telemetry Alignment**: The mismatch propagated to
   `TestTemplateServiceValidationOutcomes` and `TestTemplateServiceObservability`, causing
   validation outcome tests and hover metric tracking assertions to fail.
3. **Worker Signal Crashes in UI Tests**: Intermittent worker process termination with exit
   signals (-11 SIGSEGV, -7 SIGBUS) was reported under parallel test execution in Qt UI tests
   (`test_environment_list_widget.py`, `test_env_dialog.py`, `test_environment_export_ui.py`).
4. **SOLID Audit Snapshot Drift**: Discrepancies between recorded baseline line-of-code metrics
   and current repository metrics in `ai-tasks/PYPOST-376/baseline-metrics.md`.

### Scope: in
- Establishing clear functional specifications for error classification on malformed argument
  expressions and parentheses syntax across function expression resolver, template service, and
  observability tracking.
- Ensuring consistency between resolver outcomes, template service validation, and telemetry
  tracking.
- Verifying the stability of Qt UI tests during parallel execution and ensuring proper process
  exit.
- Verifying alignment of SOLID audit metrics baseline.
- Achieving a 100% green pass on the full test suite (`make test`).

### Scope: out
- Adding new template expression syntax features or new functions to the catalog.
- Modifying business features or visual layout of UI widgets unrelated to execution stability
  or teardown safety.
- Relaxing or modifying architectural caps in the SOLID audit baseline.

### Constraints and Assumptions
- All repository commands must be run through `make` targets (`make test`, `make check`, etc.).
  Raw CLI tool invocations (`pytest`, `flake8`, etc.) are forbidden.
- Error codes must conform to the established standard vocabulary: `invalid_argument`,
  `invalid_arity`, `unknown_function`, `invalid_syntax`.
- Backward compatibility for valid template expressions (including nested function calls and
  dotted variable paths) must be maintained.

### Non-functional Requirements
- **Diagnostic Accuracy**: Error codes must precisely reflect the nature of authoring errors to
  prevent user confusion.
- **Determinism**: Parallel test runs must produce reproducible results without
  non-deterministic worker terminations.
- **Maintainability**: Clear error classification boundaries prevent subtle regression drifts
  across parsing, validation, and rendering stages.

## Q&A

- **Q: Why should a malformed nested expression like `{{ md5(urlencode(db) }}` produce
  `invalid_argument` rather than `invalid_arity`?**
  A: The function `md5` expects a single valid expression argument. The inner expression
  `urlencode(db` is syntactically invalid (missing closing parenthesis). It does not represent
  multiple comma-separated arguments, nor does it represent zero arguments; it is an invalid
  argument. Reporting `invalid_arity` wrongly tells the user that the function accepts a
  different count of arguments, whereas reporting `invalid_argument` correctly directs the user
  to fix the argument expression itself.

- **Q: Why is `invalid_arity` appropriate for `{{ urlencode(a, b) }}` but not `{{
  md5(urlencode(db) }}`?**
  A: `{{ urlencode(a, b) }}` contains two distinct top-level arguments separated by a comma,
  which violates the single-argument signature of `urlencode`. In contrast, `{{
  md5(urlencode(db) }}` has an unclosed parenthesis in its argument, which is a structural
  argument syntax error.

- **Q: What is the status of the SOLID audit baseline failure noted in the original ticket?**
  A: The baseline metrics snapshot drift was addressed by the tooling improvements in
  PYPOST-1295 (`make baseline-metrics`), and `test_solid_audit_baseline.py` currently passes.
  Step 1 requirements include ensuring this alignment remains satisfied.

- **Q: How will the Qt worker crashes (SIGSEGV / SIGBUS) be handled?**
  A: Current full-suite runs on this branch show passing results for
  `test_environment_list_widget.py`, `test_env_dialog.py`, and `test_environment_export_ui.py`.
  The requirements mandate that full-suite and parallel runs continue to pass reliably without
  worker crashes.
