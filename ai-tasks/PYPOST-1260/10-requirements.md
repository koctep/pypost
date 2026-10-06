# PYPOST-1260: Diagnostic Log for Malformed WORKER_TIMEOUT Environment Variable

## Goals

Predictable test execution bounds and transparent configuration diagnostics are essential
for developer productivity and CI pipeline reliability.

Historically:
1. In PYPOST-1199, worker timeout precedence was formalized, but an invalid `WORKER_TIMEOUT`
   environment variable silently fell through to the default 30.0s timeout without notifying
   operators.
2. In PYPOST-1249, fail-closed validation was strengthened so that an invalid `WORKER_TIMEOUT`
   raises `RunnerValidationError` when no CLI timeout is specified (`cli_timeout` is None).
   However, when a CLI argument (`--worker-timeout`) takes precedence, any malformed
   `WORKER_TIMEOUT` present in the environment is completely bypassed and ignored without any
   diagnostic log.

As a result, configuration typos or corrupted environment variable exports in CI matrices
(e.g., `WORKER_TIMEOUT="30s"`, `WORKER_TIMEOUT="abc"`, `WORKER_TIMEOUT=""`, or negative numbers)
remain hidden from operators whenever CLI arguments are supplied. Furthermore, even when
validation fails closed, operators benefit from an explicit, structured warning log identifying
the malformed environment input before or during failure handling.

The goal of this task is to ensure that whenever an invalid `WORKER_TIMEOUT` environment
variable is detected, a visible diagnostic warning log is emitted, making configuration typos
immediately obvious in CI output without breaking existing precedence contracts or causing
unexpected crashes when a valid CLI override is present.

**Business goal**: Enable immediate discovery and diagnosis of environment configuration typos
in CI/CD pipelines and developer environments by emitting a diagnostic warning log whenever
a malformed `WORKER_TIMEOUT` environment variable is detected, while preserving existing CLI
precedence and validation guarantees.

**Implementation language**: Python (the test runner orchestrator language).

## User Stories

- As a **CI/pipeline operator**, I want to see a clear warning in the CI build log whenever
  `WORKER_TIMEOUT` contains an invalid or malformed value, so that I can promptly detect and
  fix configuration typos in pipeline definitions.
- As a **developer running tests with a CLI timeout override**, I want my CLI argument to take
  effect even if an invalid `WORKER_TIMEOUT` is exported in my environment, while still receiving
  a diagnostic warning that my environment variable is malformed.
- As a **test tooling engineer**, I want malformed environment variables to be consistently
  validated and logged using standard logging facilities, ensuring seamless integration with
  log aggregation and monitoring systems.
- As a **repository maintainer**, I want backward compatibility preserved so that existing tests
  and valid timeout workflows continue to operate without regressions.

## Definition of Done

1. **Diagnostic Warning Logging**:
   - When `WORKER_TIMEOUT` is set in the environment to a malformed or invalid value (e.g. empty,
     whitespace, non-numeric string, zero, negative number, or non-finite float), a diagnostic
     warning log is emitted.
   - The diagnostic log clearly identifies the setting name (`WORKER_TIMEOUT`), the malformed
     value, and the validation issue.
   - Diagnostic logging occurs regardless of whether an explicit CLI `--worker-timeout` is
     provided.

2. **Precedence and Resilience Contract**:
   - If a valid CLI `--worker-timeout` is provided alongside a malformed `WORKER_TIMEOUT` in the
     environment, the runner logs the diagnostic warning and proceeds using the CLI timeout.
   - If no CLI `--worker-timeout` is provided (it is `None`) and `WORKER_TIMEOUT` is malformed,
     the runner logs the diagnostic warning and fails closed with `RunnerValidationError`,
     maintaining existing error behavior.
   - If `WORKER_TIMEOUT` is unset or valid (a positive finite number or the explicit string
     `"none"`), no diagnostic warning is logged.

3. **Backward Compatibility**:
   - All existing tests in `tests/test_run_parallel_tests.py` continue to pass without regression.
   - The precedence hierarchy (CLI argument > `WORKER_TIMEOUT` env > default 30.0s) remains intact.

4. **Quality Gates**:
   - Unit tests verify diagnostic warning log emission for malformed environment variables in both
     CLI-override and no-CLI scenarios.
   - Unit tests verify that valid or unset environment variables do not emit warning logs.
   - All repository quality checks pass via `make` targets.

## Task Description

### Problem

In `scripts/run_parallel_tests.py`, per-worker timeout resolution inspects CLI arguments first.
When `--worker-timeout` is supplied on the CLI, the orchestrator immediately returns the parsed
CLI value without inspecting the `WORKER_TIMEOUT` environment variable. Consequently, any typo
or invalid configuration in `WORKER_TIMEOUT` (e.g., `WORKER_TIMEOUT="120s"`, `WORKER_TIMEOUT="0"`,
`WORKER_TIMEOUT="invalid"`) is silently ignored.

When CLI arguments are not provided, an invalid `WORKER_TIMEOUT` raises `RunnerValidationError`.
However, operators analyzing CI logs have requested explicit diagnostic visibility into
malformed environment inputs. Emitting a diagnostic log at the point of detection allows
pipeline operators and automated log analyzers to flag configuration errors early.

### Scope

**In scope**:
- Inspecting `WORKER_TIMEOUT` environment variable for malformed values during timeout resolution.
- Emitting a diagnostic warning log when a malformed `WORKER_TIMEOUT` is detected.
- Preserving CLI timeout precedence when CLI override is present.
- Preserving fail-closed `RunnerValidationError` when CLI override is absent.
- Comprehensive unit tests covering warning log emission across invalid values and precedence
  permutations.

**Out of scope**:
- Modifying worker process termination mechanisms or subprocess signal handling.
- Changing `DEFAULT_WORKER_TIMEOUT` (30.0 seconds).
- Modifying CLI argument names or flags.
- Logging warnings for valid values (`positive numbers` or `"none"`).

### Constraints and Assumptions

- Diagnostic logging must use the standard runner logger (`logging.getLogger(__name__)`) at
  `WARNING` level.
- Log messages must follow repository logging conventions (key-value structured format or
  descriptive message).
- Existing test assertions must not be broken by the introduction of the warning log.
- Logging must execute safely without raising secondary exceptions if formatting strange inputs.

## Functional Requirements

1. **Environment Value Inspection**:
   - The timeout resolution logic must inspect `WORKER_TIMEOUT` when it is present in the
     environment.
   - Values considered malformed include:
     - Empty string (`""`) or whitespace-only strings (`"   "`).
     - Non-numeric strings (e.g., `"invalid"`, `"abc"`, `"30s"`).
     - Non-positive numbers (e.g., `"0"`, `"-1"`, `"-10.0"`).
     - Non-finite numeric strings (e.g., `"nan"`, `"inf"`, `"-inf"`).

2. **Diagnostic Warning Emission**:
   - Whenever `WORKER_TIMEOUT` contains a malformed value, a warning-level log record must be
     emitted.
   - The warning record must indicate that `WORKER_TIMEOUT` is invalid, include the raw invalid
     value, and indicate the nature of the error.
   - Valid values (positive numbers such as `"45.0"`, `"60"`, or `"none"`) and unset environment
     variables must not trigger warning logs.

3. **Behavior with CLI Override**:
   - When a valid CLI `--worker-timeout` is provided and `WORKER_TIMEOUT` is malformed:
     - The warning log is emitted.
     - Execution proceeds using the CLI timeout.
     - No exception is raised.

4. **Behavior without CLI Override**:
   - When no CLI `--worker-timeout` is provided (or is `None`) and `WORKER_TIMEOUT` is malformed:
     - The warning log is emitted.
     - `RunnerValidationError` is raised, adhering to fail-closed configuration policy.

## Non-Functional Requirements

- **Observability**: Diagnostic warning is emitted at `logging.WARNING` level with structured or
  consistent field tags suitable for CI log parsing.
- **Performance**: Environment inspection and log emission must have sub-millisecond overhead
  and zero impact on test execution throughput.
- **Robustness**: The diagnostic logging mechanism must be resilient; unparseable strings must
  never cause unexpected crashes during log formatting.
- **Maintainability**: Code changes must follow PEP 8 and repository standards, maintaining clean
  separation of concerns.

## Main Entities

- **Timeout Configuration Resolver**: Evaluates CLI arguments, environment variables, and
  defaults to determine the active worker execution timeout.
- **Environment Configuration Inspector**: Inspects the `WORKER_TIMEOUT` variable and validates
  its syntax and numeric bounds.
- **Diagnostic Logger**: Emits structured warning logs when configuration anomalies are detected.
- **Validation Gate**: Enforces fail-closed error handling when configuration resolution cannot
  proceed without a valid timeout.

## User Scenarios

1. **CI Pipeline with Configuration Typo and CLI Override**:
   In a CI job, a script runs `run_parallel_tests.py --worker-timeout 60`, but the environment
   contains `WORKER_TIMEOUT=invalid`. The resolver detects the malformed environment variable,
   logs a diagnostic warning `invalid_worker_timeout_env value='invalid'`, and runs tests with
   the requested 60-second CLI timeout. The operator sees the warning in CI logs and corrects
   the environment variable.

2. **CI Pipeline with Configuration Typo without CLI Override**:
   A CI job runs `run_parallel_tests.py` relying on environment settings, with `WORKER_TIMEOUT=0`.
   The resolver detects the invalid timeout, logs a diagnostic warning, and raises
   `RunnerValidationError`. The build fails closed with clear diagnostic context in logs.

3. **Normal Execution with Valid Environment Variable**:
   A CI job sets `WORKER_TIMEOUT=45.0` and runs without CLI flags. The resolver validates the
   environment variable, logs no warnings, and sets the worker timeout to 45.0 seconds.

4. **Normal Execution with Default Timeout**:
   A developer runs tests locally with no CLI flag and no `WORKER_TIMEOUT` environment variable.
   The resolver observes that `WORKER_TIMEOUT` is unset, logs no warnings, and applies the
   default 30.0-second timeout.

## Q&A

**Why log a warning instead of always failing when the environment variable is malformed?**
When a developer or CI script explicitly supplies `--worker-timeout` on the command line, the
explicit CLI parameter is the authoritative instruction. Failing the run because of an
extraneous environment variable typo would break valid runs where CLI arguments take precedence.
Logging a warning provides immediate visibility into the typo without causing unnecessary
breakage.

**Why is diagnostic logging needed if `RunnerValidationError` is already raised when CLI is None?**
`RunnerValidationError` terminates the runner, but in complex CI systems or when error messages
are summarized at higher layers, having a dedicated warning log event (e.g.
`invalid_worker_timeout_env`) in the runner output ensures log scrapers and operators can
pinpoint the root cause immediately.

**Does this change how valid "none" timeouts are handled?**
No. Explicitly passing `"none"` (disabling worker timeouts) remains fully supported as a valid
configuration and will not trigger any diagnostic warning.
