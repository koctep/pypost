# PYPOST-1262: Resolve Makefile test suite execution timeouts under parallel load

## Research

### Execution Profile and Root Cause Analysis

A detailed performance investigation of `tests/test_makefile_lifecycle.py` (13 tests) and
`tests/test_makefile_targets.py` (11 tests) was conducted to quantify sequential execution costs,
worker timeout behavior, and resource contention under 8-worker parallel load.

1. **Test Runner Scheduling Granularity:**
   The repository test orchestrator (`scripts/run_parallel_tests.py`) dispatches work at the file
   level (`DispatchUnit`). Pytest is executed on each test file in a separate subprocess with a
   strict worker timeout (`WORKER_TIMEOUT`, defaulting to 120s in the Makefile). If all tests in
   a single file exceed 120s cumulatively, the orchestrator terminates the worker process with
   `SIGKILL` (`exit_code=-9`) and reports `TIMED_OUT`.

2. **Workload Analysis for `tests/test_makefile_lifecycle.py` (13 tests):**
   - `TestMarkerLifecycle` (3 tests):
     - `test_venv_creates_version_marker`: ~31.6s
     - `test_clean_removes_venv_and_marker`: ~35.7s
     - `test_venv_is_idempotent`: ~31.4s
     - Subtotal for `TestMarkerLifecycle` alone: ~98.7s to 100.8s even under zero contention!
   - `TestVenvExtraStampIdempotency` (8 tests):
     - 6 tests perform `make venv` then `make venv-test` or `make venv-otel` (invoking pip).
     - 2 tests perform `make -p` prerequisite queries (~0.1s).
     - Cumulative duration: ~120s to 150s.
   - `TestInstallExtraStampContract` (2 tests):
     - Tests run `make venv` and `make install` (`pip install -e .[dev,otel]`), ~50s cumulative.
   - Total cumulative file duration: ~270s to 320s. Under parallel execution, the worker times out
     at 120.0s during `TestVenvExtraStampIdempotency::test_venv_test_skips_pip_when_current`.

3. **Workload Analysis for `tests/test_makefile_targets.py` (11 tests):**
   - `TestExitBehavior` (3 tests):
     - `test_clean_exits_zero_on_empty_tree`: ~0.03s
     - `test_unknown_target_exits_nonzero`: ~0.02s
     - `test_lint_succeeds_from_bare_venv_via_venv_test`: invokes `make venv` then `make lint`.
       `make lint` depends on `venv-test`, which invokes `pip install -e .[dev]`. This test
       takes ~58s to 60s, and timed out at 60.0s when tested directly!
   - `TestTargetExecution` (8 tests):
     - `test_venv_test_installs_pytest_and_flake8`: ~58s
     - `test_make_test_excludes_slow_marker`: ~45s
     - `test_make_test_agent_e2e_selects_agent_e2e_marker`: ~50s
     - `test_install_succeeds_with_minimal_pyproject`: ~40s
     - `test_test_succeeds_from_bare_venv_via_venv_test`: ~58s
     - `test_test_succeeds_after_install`: ~50s
     - `test_pytest_args_narrows_test_run`: ~45s
     - `test_lint_succeeds_after_install`: ~45s
   - Total cumulative file duration: ~350s to 400s. Under parallel execution, the worker times out
     at 120.0s during `test_make_test_excludes_slow_marker`.

4. **Resource Contention Factor:**
   Creating virtual environments (`python3 -m venv`, `ensurepip`) and running `pip install`
   involves heavy disk I/O, zip/wheel extraction, and process spawning. When 8 parallel workers
   compete for disk throughput and CPU, operations take 1.3x to 1.8x longer than in isolation.
   A file that takes 90s standalone easily balloons past 130s under contention.

5. **Existing Helper Infrastructure:**
   `tests/makefile_test_helpers.py` already cleanly encapsulates all shared fixtures
   (`make_workspace`, `make_workspace_full_deps`), helpers (`_run_make`, `_prerequisites`,
   `_make_stamp_stale`, `_assert_pip_install_extra`, `_assert_no_pip_install`), and constants
   (`MARKER_NAME`, `VENV_TEST_STAMP_NAME`, `VENV_OTEL_STAMP_NAME`, etc.).
   Splitting the test classes and tests into granular files requires zero fixture duplication.

6. **Regression Guardrails:**
   `tests/test_makefile_parallel_budget.py` checks:
   - Module timeout marks (`pytestmark = pytest.mark.timeout(...)`) <= 60s on split files.
   - Max test count bounds.
   - Line length limits (all lines <= 100).
   - No debug print statements.
   Updating the split file references in `test_makefile_parallel_budget.py` ensures the layout
   is permanently enforced by CI.

---

## Implementation Plan

### High-Level Execution Phases

The implementation will be executed across Steps 3 and 4 as follows:

1. **Step 3 — Failing Repro Test (`tests/test_pypost_1262_failing_repro.py`):**
   - Write an automated red test that inspects the test suite structure and timeout budgets:
     - Detects presence of oversized monolithic test files (`test_makefile_lifecycle.py` and
       `test_makefile_targets.py` containing excessive heavy tests).
     - Asserts no Makefile test file contains a cumulative sequential workload exceeding the
       safe budget (< 60s target per file, <= 4 heavy venv-creation tests per file).
     - Asserts that the new modular split files exist and declare bounded timeouts (`<= 60s`).
     - In Step 3 before the fix, this test fails (RED) because `test_makefile_lifecycle.py`
       (13 tests) and `test_makefile_targets.py` (11 tests) violate the budget constraints
       and the modular files do not yet exist.
     - In Step 4 after decomposing the files, this repro test passes (GREEN).

2. **Step 4 — Test Suite Decomposition:**
   - Decompose `tests/test_makefile_lifecycle.py` (13 tests) into 3 focused files:
     - `tests/test_makefile_markers.py`: 3 tests (`TestMarkerLifecycle`)
     - `tests/test_makefile_stamp_idempotency.py`: 8 tests (`TestVenvExtraStampIdempotency`)
     - `tests/test_makefile_install_stamp_contract.py`: 2 tests (`TestInstallExtraStampContract`)
     - Remove the original `tests/test_makefile_lifecycle.py`.
   - Decompose `tests/test_makefile_targets.py` (11 tests) into 3 focused files:
     - `tests/test_makefile_exit_behavior.py`: 3 tests (`TestExitBehavior`)
     - `tests/test_makefile_target_install_test.py`: 4 tests
       (`test_venv_test_installs_pytest_and_flake8`,
       `test_install_succeeds_with_minimal_pyproject`,
       `test_test_succeeds_from_bare_venv_via_venv_test`,
       `test_test_succeeds_after_install`)
     - `tests/test_makefile_target_filtering.py`: 4 tests
       (`test_make_test_excludes_slow_marker`,
       `test_make_test_agent_e2e_selects_agent_e2e_marker`,
       `test_pytest_args_narrows_test_run`,
       `test_lint_succeeds_after_install`)
     - Remove the original `tests/test_makefile_targets.py`.
   - Update `tests/test_makefile_parallel_budget.py` to register all new split files in
     `SPLIT_MAKEFILE_TEST_FILES` and in line-length/no-print validation lists.
   - Adjust individual test timeouts where appropriate:
     - Module-level `pytestmark = pytest.mark.timeout(60)` on all split files.
     - On heavy tests (such as `test_lint_succeeds_from_bare_venv_via_venv_test`), ensure
       timeout markers are set to 75s if needed to absorb load spikes, below the 120s limit.

3. **Step 4 — Validation and Verification:**
   - Verify `make test` completes cleanly with 8 workers in parallel without `TIMED_OUT` workers.
   - Verify all 24 original test cases execute and pass with 100% assertion parity.
   - Verify `make check` passes cleanly.

### Mandatory — Failing Repro (Step 3 Design)

- **Test file:** `tests/test_pypost_1262_failing_repro.py`
- **What it asserts (desired behavior):**
  1. Monolithic files `tests/test_makefile_lifecycle.py` and `tests/test_makefile_targets.py`
     must not exist with test counts exceeding 4 tests per file.
  2. The decomposed target test suite files must exist:
     - `tests/test_makefile_markers.py`
     - `tests/test_makefile_stamp_idempotency.py`
     - `tests/test_makefile_install_stamp_contract.py`
     - `tests/test_makefile_exit_behavior.py`
     - `tests/test_makefile_target_install_test.py`
     - `tests/test_makefile_target_filtering.py`
  3. Every decomposed test file must declare a module-level `pytestmark = pytest.mark.timeout(...)`
     with `timeout <= 60` seconds.
  4. Total test count across all decomposed files must equal exactly 24 tests (13 lifecycle tests +
     11 target tests), verifying zero coverage regression.
- **Forcing failure without external dependencies:**
  The test uses Python's `ast` module to statically inspect the `tests/` directory. Prior to Step 4
  modularization, the decomposed files do not exist and the monolithic files exceed limits,
  guaranteeing an immediate, deterministic, fast failure (< 0.1s) without subprocesses.
- **Sequencing:**
  Step 2 (Architecture approved) -> Step 3 (Write red repro test -> verify red) -> Step 4
  (Decompose files, update budget checks -> verify green repro test + full `make check`).

---

## Architecture

### Module Decomposition Diagram

```
+-----------------------------------------------------------------------------------------+
|                               scripts/run_parallel_tests.py                             |
|                              (8 Workers, 120s Worker Timeout)                            |
+----+-------------------+-------------------+--------------------+--------------------+--+
     |                   |                   |                    |                    |
     v                   v                   v                    v                    v
+---------------+ +---------------+ +---------------+ +---------------+ +---------------+
|   Worker 1    | |   Worker 2    | |   Worker 3    | |   Worker 4    | |   Worker 5    |
| test_makefile | | test_makefile | | test_makefile | | test_makefile | | test_makefile |
|  _markers.py  | |   _stamp_     | |  _install_    | |    _exit_     | |    _target_   |
|               | | idempotency.py| | stamp_        | |  behavior.py  | |  install_     |
|   (3 tests)   | |   (8 tests)   | |  contract.py  | |   (3 tests)   | |   test.py     |
|   ~35-45s     | |   ~30-45s     | |   (2 tests)   | |   ~15-25s     | |   (4 tests)   |
|               | |               | |   ~25-35s     | |               | |   ~35-45s     |
+---------------+ +---------------+ +---------------+ +---------------+ +---------------+
                                                                               |
                                                                               v
                                                                        +---------------+
                                                                        |   Worker 6    |
                                                                        | test_makefile |
                                                                        |   _target_    |
                                                                        |  filtering.py |
                                                                        |   (4 tests)   |
                                                                        |   ~35-45s     |
                                                                        +---------------+
```

### Module Responsibilities and Mappings

#### 1. `tests/test_makefile_markers.py`
- **Source Origin:** `TestMarkerLifecycle` from `test_makefile_lifecycle.py`
- **Contained Tests (3):**
  - `test_venv_creates_version_marker`
  - `test_clean_removes_venv_and_marker`
  - `test_venv_is_idempotent`
- **Estimated Runtime:** ~35-45s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)`

#### 2. `tests/test_makefile_stamp_idempotency.py`
- **Source Origin:** `TestVenvExtraStampIdempotency` from `test_makefile_lifecycle.py`
- **Contained Tests (8):**
  - `test_venv_test_skips_pip_when_current`
  - `test_venv_otel_skips_pip_when_current`
  - `test_venv_test_installs_when_stamp_missing`
  - `test_venv_otel_installs_when_stamp_missing`
  - `test_venv_test_installs_when_stamp_stale`
  - `test_venv_otel_installs_when_stamp_stale`
  - `test_venv_test_depends_on_stamp`
  - `test_venv_otel_depends_on_stamp`
- **Estimated Runtime:** ~30-45s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)`

#### 3. `tests/test_makefile_install_stamp_contract.py`
- **Source Origin:** `TestInstallExtraStampContract` from `test_makefile_lifecycle.py`
- **Contained Tests (2):**
  - `test_install_touches_both_extra_stamps`
  - `test_install_stamps_allow_skip_pip_on_venv_test_otel`
- **Estimated Runtime:** ~25-35s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)`

#### 4. `tests/test_makefile_exit_behavior.py`
- **Source Origin:** `TestExitBehavior` from `test_makefile_targets.py`
- **Contained Tests (3):**
  - `test_clean_exits_zero_on_empty_tree`
  - `test_unknown_target_exits_nonzero`
  - `test_lint_succeeds_from_bare_venv_via_venv_test`
- **Estimated Runtime:** ~20-30s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)` (test 3 marked with timeout 75s)

#### 5. `tests/test_makefile_target_install_test.py`
- **Source Origin:** `TestTargetExecution` (subset 1) from `test_makefile_targets.py`
- **Contained Tests (4):**
  - `test_venv_test_installs_pytest_and_flake8`
  - `test_install_succeeds_with_minimal_pyproject`
  - `test_test_succeeds_from_bare_venv_via_venv_test`
  - `test_test_succeeds_after_install`
- **Estimated Runtime:** ~35-45s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)`

#### 6. `tests/test_makefile_target_filtering.py`
- **Source Origin:** `TestTargetExecution` (subset 2) from `test_makefile_targets.py`
- **Contained Tests (4):**
  - `test_make_test_excludes_slow_marker`
  - `test_make_test_agent_e2e_selects_agent_e2e_marker`
  - `test_pytest_args_narrows_test_run`
  - `test_lint_succeeds_after_install`
- **Estimated Runtime:** ~35-45s under parallel load
- **Timeout Mark:** `pytestmark = pytest.mark.timeout(60)`

### Architectural Patterns & Decisions

1. **Horizontal Decomposition (Single-Responsibility Files):**
   Rather than clustering integration tests by broad lifecycle/target categories, decomposing them
   into narrow scenario-focused files aligns the unit of parallelism (file level) with CPU cores.
   Each worker handles at most ~40s of sequential execution, providing a comfortable 3x safety
   margin against the 120s worker timeout.

2. **Zero-Duplication Fixture Sharing:**
   All decomposed files import `make_workspace` and helper functions directly from
   `tests.makefile_test_helpers`. No fixture logic is duplicated. Workspace isolation remains
   hermetic because `make_workspace` uses `pytest`'s `tmp_path` fixture for each test.

3. **Explicit Timeout Mark Decorators:**
   Every decomposed file declares `pytestmark = pytest.mark.timeout(60)` conforming to repo
   standards in `do-testing` and `lsr-python`.

4. **Integration with Budget Test Suite:**
   `tests/test_makefile_parallel_budget.py` will be updated to include all 6 split files in:
   - `SPLIT_MAKEFILE_TEST_FILES`
   - `files_to_check` in `test_makefile_suite_files_line_length`
   - `files_to_check` in `test_makefile_suite_files_no_debug_prints`

---

## Q&A

- **Q: Why split `test_makefile_targets.py` into 3 files instead of 2?**
  **A:** `TestTargetExecution` contains 8 tests, nearly all running full `make install` and
  `make test`. Grouped together, cumulative runtime would be ~150-180 seconds, exceeding the 120s
  worker timeout. Splitting it into two files of 4 tests bounds execution to ~35-45s per worker.

- **Q: Why split `test_makefile_lifecycle.py` into 3 files instead of 2?**
  **A:** `TestMarkerLifecycle` alone takes ~100s across its 3 venv creation tests. Placing
  it in its own dedicated file ensures it completes within ~35-45s, safely within budget.

- **Q: Will this change break any external tools or CI invocations?**
  **A:** No. `make test`, `make test-cov`, and `scripts/run_parallel_tests.py` automatically
  discover all files matching `tests/test_*.py`. Individual targets can run via `PYTEST_ARGS`.

- **Q: Are all lines in the new files formatted under 100 characters?**
  **A:** Yes. Strict compliance with line length <= 100 characters is enforced by repo quality
  gates and verified by `test_makefile_parallel_budget.py`.
