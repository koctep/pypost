# PYPOST-718: Fix Makefile test Python version coupling

## Goals

Ensure that automated tests for workspace workflows (`test_makefile.py`) are robust,
deterministic, and decoupled from system-level environment differences. When a developer or CI
runner executes tests using a specific Python environment, the Makefile test suite must use
that same Python environment, preventing test failures caused by Python version mismatches and
incorrect initialization markers.

From a business and developer productivity perspective, this task aims to:
- Prevent false-negative test failures in both local development and CI/CD environments.
- Save engineering time that would otherwise be wasted troubleshooting environment discrepancies.
- Improve trust in the workspace test suite and development automation.

## User Stories

- **As a Developer**, I want the workspace integration tests to run successfully using my active
  Python interpreter and configuration, so that I can reliably verify Makefile workflows without
  manual environment tweaking.
- **As a CI/CD Engineer**, I want the automated pipeline to execute the test suite without
  failing due to discrepancy between the test runner's Python version and the default system
  `python3` command, ensuring continuous delivery runs smoothly.

## Definition of Done

1. **Environmental Decoupling**: The automated integration tests for Makefile commands run
   reliably, regardless of whether the default `python3` on the system path matches the active
   Python interpreter executing the tests.
2. **Consistency**: The virtual environments and initialization markers created during Makefile
   test execution always match the Python version/interpreter that is currently running the
   test suite.
3. **No Regressions**: All integration tests in `test_makefile.py` pass cleanly when running
   the standard test targets.

## Task Description

### Context and Problem
The workspace uses a `Makefile` to manage virtual environments, dependencies, and testing. It
defines a variable `PYTHON := python3` by default.

When `test_makefile.py` runs, it simulates Makefile target executions in temporary directories.
If the Python interpreter running `pytest` differs from the default `python3` on the shell path
(for example, if running inside a specific virtual environment or with a specific Python
version), the following discrepancy occurs:
1. `test_makefile.py` determines the Python version using its own active runtime.
2. The Makefile commands executed in the test run use the default system `python3`.
3. This creates a mismatch in the initialization marker names (e.g., `.initialized-3.11` vs
   `.initialized-3.12`), leading to assertion failures in tests like
   `test_venv_creates_version_marker`.

### Main Business Entities

- **Active Python Interpreter**: The Python executable/runtime currently executing the test suite.
- **Makefile Execution Sandbox**: The isolated temporary directory where Makefile targets are
  executed during test runs.
- **Initialization Marker**: The sentinel marker file (e.g. .initialized-x.y) representing that
  a virtual environment has completed dependencies setup.

### Requirements
- Provide a mechanism within the test execution framework to enforce that the Makefile processes
  use the exact same Python interpreter that is running the test suite.
- Keep the system platform-agnostic, working across various Unix-like operating systems (macOS,
  Linux).
- Ensure no hardcoding of specific Python paths or system-specific dependencies.

## Q&A

**Q: Which programming language is targeted for this task?**
A: **Python** is the target programming language for the test suite implementation.

**Q: Does this change affect how normal developers run `make` targets?**
A: No, normal developer usage of `make` targets remains unchanged. The changes only affect the
   internal test environment setup during test execution.
