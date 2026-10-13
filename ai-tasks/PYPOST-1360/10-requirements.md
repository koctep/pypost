# PYPOST-1360: Slow project installation smoke exceeds 180-second timeout at clean base commit

## Goals

Ensure the project installation quality gate remains reliable, hermetic, and predictable by allowing the slow project installation smoke test suite to consistently pass within its allocated 180-second timeout budget under standard execution conditions.

Developers and automated CI/verification pipelines require confidence that package installation workflows complete within established SLAs without failing spuriously due to unbounded waiting or unoptimized setup stages.

## User Stories

### US-1: Developer Fast and Reliable Quality Gates
As a software engineer running full repository test suites or slow verification gates (`make test-slow`),
I want the packaging installation smoke verification to complete reliably within the established 180-second execution budget,
So that development feedback loops are predictable, CI checks do not time out spuriously, and package installation integrity is consistently verified.

### US-2: Packaging and Environment Maintainer
As a repository maintainer responsible for build and packaging stability,
I want the slow installation verification to execute within its explicit time boundaries without removing test coverage or blindly increasing the timeout limit,
So that regressions in environment preparation, dependency resolution/installation, or sanity validation are surfaced accurately and prevented.

## Definition of Done

1. **Deterministic Execution within Budget**: The slow installation smoke test (`tests/test_makefile_slow_smoke.py::TestSlowInstallSmoke::test_install_succeeds_with_project_pyproject`) executes successfully and reliably within its 180-second timeout threshold.
2. **Preserved Coverage & Verification**: The test continues to verify full packaging installation and sanity checks without reducing test coverage or weakening assertions.
3. **Strict Timeout Integrity**: Explicit timeouts (180s test timeout budget, 170s nested make timeout) are maintained rather than inflated as a workaround.
4. **Make-Only Interface Compliance**: Reproduction, testing, and validation are driven strictly via supported Make targets (`make test-slow` and standard quality gates).
5. **Quality Gates Green**: Relevant Make quality targets pass cleanly.

## Task Description

- **Implementation Language**: Python

During execution of PYPOST-1348, the existing slow installation smoke test (`tests/test_makefile_slow_smoke.py::TestSlowInstallSmoke::test_install_succeeds_with_project_pyproject`) was found to exceed its explicit 180-second pytest timeout when run on a clean base commit (`1e64239fe804c53558d6ce323d39fa33657d017b`).

The failure is characterized by pytest terminating the test execution after 180s while the nested `make install` invocation is still waiting, with no packaging assertions failing prior to the timeout.

### Main Entities

- **Smoke Verification Quality Gate**:
  - *Attributes*: test identifier, execution target, pass/fail status, timeout threshold.
  - *Business Role*: Serves as the overarching verification check ensuring packaging and installation workflows work deterministically and meet the designated quality threshold without spurious timeouts.
- **Package Installation Workflow**:
  - *Attributes*: target recipe, build steps, dependencies resolved, sanity checks.
  - *Business Role*: Encapsulates the multi-step process of installing the package and its dependencies into a target environment and performing post-installation sanity assertions.
- **Sandboxed Test Environment**:
  - *Attributes*: workspace directory, virtual environment, isolation state.
  - *Business Role*: Provides the hermetic, temporary execution context isolated from the host environment to guarantee repeatable testing conditions.
- **Execution Budget / SLA**:
  - *Attributes*: max elapsed time (180s), nested command budget (170s), deadline enforcement.
  - *Business Role*: Defines and enforces the bounded execution envelope that safeguards automated testing and CI pipelines from indefinite hangs.


### Functional Requirements
- The slow installation smoke test must execute end-to-end to completion and assert post-installation sanity.
- The installation process inside the test must succeed with return code 0 and pass post-install sanity checks.
- Any bottlenecks or blocking steps during test environment setup, dependency retrieval/installation, or post-install verification must be diagnosed and addressed so execution completes well within the 180-second limit.

### Non-Functional Requirements
- **Performance / SLA**: The entire test run must finish comfortably under 180 seconds.
- **Reliability & Hermeticity**: Test execution must be repeatable and stable across multiple consecutive executions without transient hanging or unbounded waits.
- **Maintainability**: Diagnostics and corrective actions must preserve existing isolation and reproducible packaging behavior.

### Constraints & Assumptions
- **Constraint**: All operations and test executions must use Make targets (`make test-slow`, `make check`, etc.). Raw CLI tool invocations (`pytest`, `pip`) are prohibited.
- **Constraint**: Blindly raising the 180-second timeout or the nested 170-second timeout is strictly forbidden.
- **Constraint**: Skipping or removing test coverage / packaging assertions is strictly forbidden.
- **Constraint**: Explicit timeouts must be preserved on all asynchronous/bounded operations per project testing standards.
- **Assumption**: The underlying Python environment and base package specifications are valid, and failure is due to performance or execution bottlenecks during preparation, installation, or validation stages.

## Q&A

- **Q: Why shouldn't the timeout simply be increased to 300 seconds?**
  **A**: The 180-second limit is an explicit performance and reliability boundary for smoke verification. Arbitrarily inflating timeouts masks underlying latency or blocking issues and degrades developer feedback cycles.

- **Q: Does this task modify the packaging contract itself?**
  **A**: No. The business goal is to guarantee the packaging installation verification runs within its intended SLA, without changing functional packaging commitments or removing sanity validations.

- **Q: What constitutes a successful verification?**
  **A**: A clean, bounded reproduction followed by reliable execution of `make test-slow PYTEST_ARGS='tests/test_makefile_slow_smoke.py -m slow'` within the 180s budget, passing all existing assertions.
