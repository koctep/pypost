# PYPOST-1149: Implement Parallel Test Runner Orchestrator for make test and make test-cov

## Goals

The PyPost test suite has grown to 268+ test files. Running them sequentially under `make test`
wastes developer and CI time because each test file's suite is independent. This task aims to
substantially reduce overall test cycle time — targeting at least a 50% reduction in wall-clock
time on a multi-core machine — by running all test files concurrently in isolation, while
preserving the existing developer UX: progress feedback, failure reporting, and coverage output
are all retained.

**Business goal**: Cut `make test` and `make test-cov` wall-clock execution time so that the
development feedback loop is materially faster — especially in CI where machine cores are
available and currently under-utilised.

## User Stories

**As a developer**, I want `make test` to run all test files in parallel so that I get a
pass/fail result faster without changing any existing pytest flags or workflow.

**As a developer running a filtered test**, I want my pytest filter to be
transparently applied to every test file's execution so that I can narrow the test scope the
same way I do today.

**As a developer**, I want to see a consolidated failure report at the end of the run — with
full tracebacks grouped by file — so that I can identify which tests failed without searching
through interleaved subprocess output.

**As a developer or CI operator**, I want to know which test files take longest so that I can
prioritise optimisation efforts (top 5 slowest files reported in the summary).

**As a developer running `make test-cov`**, I want coverage data from all parallel subprocesses
to be automatically aggregated and reported, so I get the same coverage output I expect from a
sequential run.

**As a CI operator**, I want to optionally emit a machine-readable JSON report
summarising pass/fail counts, slowest files, and per-file outcomes.

**As a developer**, I want to control the number of parallel workers so I can tune
parallelism for my machine.

## Definition of Done

- `make test` invokes the parallel runner and completes with exit code 0 when all tests
  pass, non-zero when any test fails.
- `make test-cov` invokes the parallel runner with coverage enabled; a combined coverage report
  is produced at the end.
- Test files are executed in isolation so that Qt/QApp state from one test file cannot affect
  another.
- Default worker count is derived from available CPU cores; it is configurable by the operator.
- Work is distributed dynamically across workers so no worker idles waiting for a slow file.
- Standard pytest filters and flags are forwarded transparently to each test file's execution.
- Real-time single-line progress is printed for each completed test file.
- Final consolidated report groups all failure tracebacks by file.
- The top 5 slowest test files are listed in the summary.
- A machine-readable JSON report can optionally be generated for CI consumption.
- `make test` and `make test-cov` invoke the parallel runner without additional arguments.
- The overall exit code reflects the combined pass/fail result across all files.

## Task Description

### Problem

The current `Makefile` invokes pytest once over the entire `tests/` directory sequentially.
With 268+ test files, this is slow. Each test file is independently executable in an isolated
environment, which makes per-file parallelism viable and safe.

### Scope

- **In scope**:
  - A new parallel runner script.
  - Updates to `make test` and `make test-cov` targets to invoke the new script.
  - Automatic coverage aggregation when `--cov` is active.
  - JSON report output via `--report-json`.
  - Progress display and consolidated failure reporting.
  - `WORKERS` variable support in Makefile and CLI.

- **Out of scope**:
  - Changes to test files themselves.
  - Introducing new pytest plugins or third-party parallel test tools (e.g., `pytest-xdist`).
  - Changing the CI workflow YAML (covered separately if needed).
  - Running test files across multiple machines or distributed workers.

### Constraints and Assumptions

- **Language**: Python 3 (consistent with the rest of the `scripts/` directory).
- **No new production dependencies**: No new third-party runtime dependencies are introduced. The existing
  `coverage` package already in `requirements-dev.txt` continues to be used.
- **Qt isolation**: Each test file runs in an isolated environment to prevent Qt/QApp state
  leakage between test files.
- **Coverage isolation**: Coverage data from all test files is aggregated automatically into
  a single combined report.
- **Sequential fallback**: When configured to use a single worker, behaviour is equivalent to
  a sequential run with the same reporting.
- **Exit code**: The exit code reflects the overall pass/fail outcome of the test run.
- **Test discovery**: When no specific files are specified, the runner discovers all test files
  automatically; explicit file paths are passed through unchanged.
- **Existing slow/integration targets unchanged**: `make test-slow`, `make test-mcp-collection-e2e`,
  and other specialised targets remain unaffected.

## Main Entities

| Entity | Description |
|--------|-------------|
| **Orchestrator** | The top-level component that discovers test files, launches parallel execution, collects results, and prints the final report. |
| **Test Execution** | The act of running a single test file, producing a pass/fail outcome and timing data. |
| **Test File Backlog** | The set of test files scheduled for execution in the current run. |
| **Test File** | One test file in the test suite; the unit of parallelism. |
| **Result** | The outcome of running one test file: pass/fail, elapsed time, and captured output. |
| **Coverage Report** | The aggregated coverage data from all test files' runs, combined into a single output. |
| **Final Report** | A human-readable summary printed to stdout: overall pass/fail, failure tracebacks grouped by file, top 5 slowest files. |
| **JSON Report** | An optional machine-readable report; contains per-file outcomes and aggregate stats. |

## User Scenarios

### UC-1: Normal developer test run

1. Developer runs `make test`.
2. The parallel runner executes all discovered test files in parallel in isolated execution environments.
3. Progress is displayed per completed test file, including pass/fail and duration.
4. After all files complete, the runner prints: pass count, fail count, top 5 slowest files.
5. If any file failed, full tracebacks are printed grouped by file.
6. Make exits with 0 (all pass) or non-zero (any fail).

### UC-2: Filtered run

1. Developer runs `make test` with a keyword filter.
2. The filter is applied to each test file's execution.
3. Files where no test matches the filter exit cleanly (no-tests-collected is not a failure).
4. Matching tests run in parallel; report is produced as usual.

### UC-3: Coverage run

1. Developer runs `make test-cov`.
2. The parallel runner executes all test files with coverage enabled.
3. Coverage data from all test files is aggregated automatically.
4. Developer sees the same combined coverage output as with the sequential run.

### UC-4: CI JSON report

1. CI invokes `make test` requesting a machine-readable JSON report.
2. After completion, the report file contains per-file outcomes and aggregate stats.
3. CI tooling can parse the JSON to annotate PRs or track trends.

### UC-5: Worker count tuning

1. Developer on a 4-core laptop configures the runner to use 4 workers.
2. The runner respects the configured limit, reducing resource contention.
3. Run completes correctly with the same report.

## Q&A

**Q: Why not use `pytest-xdist` instead of a custom orchestrator?**
A: `pytest-xdist` does not support per-file QApp isolation cleanly (it runs workers in-process).
The custom orchestrator ensures each test file runs in its own OS-level process, which is the
only robust approach for the Qt-heavy test suite.

**Q: Will explicit file paths in the filter break discovery?**
A: When explicit file or directory paths are specified, the runner narrows execution to that
subset and does not run discovery, preserving existing behaviour.

**Q: Does the orchestrator need to handle `tests/` subdirectories?**
A: Initial scope covers flat test files only. Subdirectory support is out of scope;
those directories are not direct test modules.

**Q: What happens when a test file hangs?**
A: Out of scope for this ticket. Workers rely on pytest's own timeout mechanisms.
A future follow-up ticket can add a per-file wall-clock timeout.
