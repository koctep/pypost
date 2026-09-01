# PYPOST-1199: Unit tests for get_worker_timeout precedence

## Goals

Test orchestration reliability is fundamental to developer productivity and CI throughput. In PYPOST-1192, a configurable per-worker execution timeout was introduced to eliminate unbounded test hangs and ensure fast feedback when individual tests stall.

However, the configuration resolution order and input validation for worker timeouts were left without dedicated automated unit tests (noted as follow-up technical debt in PYPOST-1192). Operators configure test execution through multiple channels: command-line arguments, environment variables, and build automation defaults. If precedence rules or edge-case validation break:
1. Malformed or edge-case inputs (e.g., negative numbers, zeroes, whitespace, or invalid non-numeric strings) could cause unhandled exceptions or cause the test runner to stall indefinitely without a timeout.
2. Inverted or ambiguous precedence could cause environment variables to silently override explicit developer CLI intentions, or cause build tool defaults to override explicit environment settings.
3. Build system targets (`make test` and `make test-cov`) might drift from the orchestrator configuration contract, leading to false timeouts or unexpected timeouts across test environments.

This task delivers comprehensive automated test verification locking the resolution precedence, fallback behavior, invalid-input resilience, CLI parsing semantics, and build system contract for worker timeouts.

**Business goal**: Guarantee dependable, predictable test execution bounds across local development and CI by locking timeout configuration resolution, input validation fallthrough, and build automation wiring through automated tests.

**Implementation language**: Python (in accordance with the repository test suite and tooling standards).

## User Stories

- As a **developer running tests via CLI**, I want my explicit `--worker-timeout` parameter to take precedence over any environment variable or system default so that I have absolute control over worker timeouts when debugging slow tests.
- As a **CI pipeline administrator**, I want to set `WORKER_TIMEOUT` via environment variables and trust that all test runs without explicit CLI arguments adhere to this bound, even if individual test suites have different default expectations.
- As a **suite operator invoking `make test` or `make test-cov`**, I want the build system to forward the standard suite timeout budget (`WORKER_TIMEOUT ?= 120`) to the test runner orchestrator so that legitimate longer-running smoke and integration tests complete without false timeout failures.
- As a **software engineer maintaining test tooling**, I want invalid, zero, negative, or malformed timeout inputs from CLI or environment variables to safely fall back to bounded defaults rather than crashing or resulting in unbounded hangs.
- As a **repository maintainer**, I want regression-locking unit tests so that future refactoring of the test orchestrator or argument parser cannot inadvertently break timeout precedence or build contracts.

## Definition of Done

1. **Precedence Hierarchy Verification**:
   - Automated tests verify that an explicit, valid CLI worker timeout overrides both environment variable configuration and the default timeout.
   - Automated tests verify that when no CLI timeout is specified (or is `None`), a valid environment variable configuration overrides the default timeout.
   - Automated tests verify that when neither CLI timeout nor environment variable is provided, the resolution falls back to the default timeout (30.0 seconds).

2. **Invalid & Edge-Case Input Fallthrough Verification**:
   - Automated tests verify that non-positive CLI values (zero, negative numbers) do not override environment variables or safe defaults, correctly falling through.
   - Automated tests verify that empty, whitespace-only, non-numeric (e.g., strings like `"invalid"` or `"abc"`), zero, or negative environment variable values are gracefully discarded, falling through to the default timeout (30.0 seconds).
   - Verification ensures that malformed inputs never raise unhandled exceptions or produce an unbounded/zero timeout state.

3. **CLI Argument Parser Contract Verification**:
   - Automated tests verify that `--worker-timeout <value>` (separated by whitespace) correctly parses the value and supplies it to timeout resolution.
   - Automated tests verify that `--worker-timeout=<value>` (assigned via equals sign) correctly parses the value and supplies it to timeout resolution.

4. **Build System Contract Verification**:
   - Automated contract tests verify that the Makefile defines the suite default worker timeout (`WORKER_TIMEOUT ?= 120`).
   - Automated contract tests verify that the `test` and `test-cov` Makefile recipes forward `--worker-timeout $(WORKER_TIMEOUT)` to the test runner orchestrator.

5. **Quality Gates and Standards**:
   - All tests run and pass cleanly via repository Makefile targets (`make check` or focused `make test`).
   - All new test functions adhere to repository testing guidelines (declaring appropriate `@pytest.mark.timeout(...)` bounds and avoiding unbounded waits).

## Task Description

### Problem

The test orchestrator determines per-worker timeout using a multi-tiered resolution function (`get_worker_timeout`). While the basic timeout capability was implemented in PYPOST-1192, the isolation unit tests for its precedence rules and input edge cases were identified as missing in `ai-tasks/PYPOST-1192/60-tech-debt.md` (Follow-up 4). Additionally, the Makefile recipe contract ensuring proper forwarding of `WORKER_TIMEOUT` to `--worker-timeout` lacks explicit regression-prevention assertions in `tests/test_makefile_recipes.py`.

### Scope

**In scope**:
- Unit tests verifying `get_worker_timeout` resolution order: CLI argument → `WORKER_TIMEOUT` environment variable → default timeout (30.0s).
- Unit tests verifying edge-case handling for `get_worker_timeout`:
  - CLI values: positive floats, `None`, zero, negative values.
  - Environment values: positive numbers, zero, negative numbers, empty strings, whitespace, non-numeric strings, unset environment.
  - Simultaneous presence of CLI and environment configurations.
- CLI argument parsing tests for `--worker-timeout` (both space-separated and equals-separated forms).
- Makefile recipe contract assertions locking `WORKER_TIMEOUT ?= 120` definition and its forwarding in `test` and `test-cov` targets.

**Out of scope**:
- Modifying the core timeout execution logic or worker process termination (`subprocess.run` / `killpg`).
- Modifying `DEFAULT_WORKER_TIMEOUT` (remains 30.0s) or Makefile `WORKER_TIMEOUT` (remains 120s).
- Refactoring the entire CLI argument parser to `argparse` (tracked under PYPOST-1153).
- Adding or modifying timeout markers inside individual test files across the repository.
- Changes to coverage collection or reporting subprocess timeouts.

### Constraints and Assumptions

- Tests must integrate seamlessly with existing test suites (`tests/test_run_parallel_tests.py` and `tests/test_makefile_recipes.py` or dedicated focused test modules).
- No production behavior changes are required unless a bug in precedence resolution or parsing is exposed by the tests.
- All test executions must use Makefile targets in accordance with repository guidelines.
- Environment variables manipulated during tests must be strictly isolated (e.g. using `monkeypatch`) to prevent test pollution.

## Non-Functional Requirements

- **Determinism and Speed**: Tests must execute in milliseconds without external process spawns where unit isolation is feasible.
- **Strict Isolation**: Environment variable mutations must not leak between test cases.
- **Safety**: Tests must enforce that invalid configuration values never result in non-terminating (unbounded) worker execution.
- **Maintainability**: Test assertions must be self-describing and provide clear diagnostic messages upon failure.
- **Conformance**: Test files must adhere to PEP 8, flake8, and declare mandatory timeout markers per project rules.

## Main Entities

- **Timeout Configuration Resolver**: The component that evaluates available configuration inputs and selects the effective worker timeout according to strict precedence rules.
- **CLI Configuration Source**: Timeout values passed as command-line arguments to the test runner orchestrator (`--worker-timeout`).
- **Environment Configuration Source**: Timeout values provided via system or session environment (`WORKER_TIMEOUT`).
- **Default Timeout Policy**: The baseline fallback timeout value (30.0 seconds) applied when no valid overrides are present.
- **CLI Argument Parser**: The parser responsible for extracting orchestrator arguments, specifically `--worker-timeout` with either space or `=` delimiter.
- **Build System Recipe Contract**: The Makefile configuration declaring the default suite timeout (`WORKER_TIMEOUT ?= 120`) and wiring it into invocation recipes.

## User Scenarios

1. **Explicit CLI Override Over Environment**:
   A developer has `WORKER_TIMEOUT=60` exported in their shell environment, but runs the test orchestrator with `--worker-timeout 10`. The resolver prioritizes the CLI argument and assigns an effective timeout of 10.0 seconds.

2. **Environment Variable Configuration**:
   A CI job runs without CLI flags but sets `WORKER_TIMEOUT=90`. The resolver observes no CLI override, validates the environment variable, and assigns an effective timeout of 90.0 seconds.

3. **Fallback to Default Timeout**:
   A developer runs the orchestrator without any CLI timeout flags and with `WORKER_TIMEOUT` unset. The resolver defaults to 30.0 seconds.

4. **Resilience to Invalid Environment Values**:
   An operator inadvertently sets `WORKER_TIMEOUT="none"` or `WORKER_TIMEOUT="-15"`. The resolver detects the invalid/non-positive value, ignores it, and safely applies the default 30.0 seconds rather than failing or disabling timeouts.

5. **Resilience to Invalid CLI Values**:
   A user passes `--worker-timeout 0` or a negative value. The resolver treats non-positive CLI inputs as non-overrides and falls back to environment or default 30.0 seconds.

6. **Makefile Suite Execution**:
   A developer runs `make test`. The Makefile recipe supplies `--worker-timeout $(WORKER_TIMEOUT)` (default 120), ensuring that slower suite tests are given the intended 120-second budget rather than the standalone 30-second default.

## Q&A

**Why is this task needed if timeout execution was already implemented in PYPOST-1192?**
PYPOST-1192 focused on the execution mechanism (aborting hung workers and marking them timed out). The precedence resolution, invalid input handling, and Makefile contract wiring were identified as technical debt follow-up items that lacked dedicated automated unit tests to prevent regressions.

**Why is invalid input fallthrough critical from a business perspective?**
If invalid input (such as an empty string or negative number in an environment variable) caused an unhandled crash or resulted in a timeout of zero/infinite, CI builds and local developer runs would be disrupted or left vulnerable to hangs. Robust fallthrough ensures safe, bounded behavior at all times.

**Why verify both `--worker-timeout <val>` and `--worker-timeout=<val>`?**
Developers and automation scripts routinely use both flag styles interchangeably. Automated tests ensure the hand-rolled parser supports both conventions uniformly without regressions.

**Does this require modifying production code?**
The primary goal is comprehensive test coverage. Production code in `scripts/run_parallel_tests.py` already implements the precedence logic; changes are only expected if test coverage discovers unintended behavioral bugs.
