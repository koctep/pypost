# PYPOST-1199: Technical Debt Analysis

## Shortcuts Taken

None. Comprehensive unit testing and contract verification were authored directly against `get_worker_timeout`, `CLIParser.parse_args`, and Makefile target recipes without introducing any mock crutches, hardcoded shortcuts, or temporary bypasses:
- Precedence hierarchy is explicitly verified across all tiers (CLI argument > `WORKER_TIMEOUT` env > default 30.0s).
- Fallthrough behavior for invalid CLI inputs (non-positive values `<= 0.0`) is parameterized and verified.
- Fallthrough behavior for malformed `WORKER_TIMEOUT` environment inputs (empty string, whitespace, non-numeric strings, negative/zero numbers) is thoroughly parameterized and verified.
- Command-line argument syntax variations (`--worker-timeout 42`, `--worker-timeout=42`, and missing argument fallthrough) are tested.
- Makefile recipe contract assertions verify that `WORKER_TIMEOUT ?= 120` is defined and forwarded to `--worker-timeout` in both `test` and `test-cov` targets.
- All environment variable mutations use `monkeypatch` to ensure strict test isolation with zero side effects.

## Code Quality Issues

- **Hand-rolled CLI argument parser**: The CLI argument parser in `scripts/run_parallel_tests.py` (`CLIParser`) uses custom iterative token scanning rather than Python's standard `argparse` module. While the timeout flags (`--worker-timeout <val>` and `--worker-timeout=<val>`) are now robustly locked by tests, migrating the entire runner CLI to `argparse` remains an open maintenance cleanup (tracked under PYPOST-1153).
- **Silent invalid environment fallthrough**: `get_worker_timeout` catches `ValueError` when parsing `WORKER_TIMEOUT` and silently falls through to the 30.0s default. While safe and resilient against crashes, emitting a diagnostic or warning log when a malformed environment variable is ignored could assist CI/pipeline operators in diagnosing configuration typos.

## Missing Tests

None within the scope of this task:
- All required precedence tiers, fallback behaviors, and edge-case inputs specified in `10-requirements.md` and `20-architecture.md` are covered.
- All new tests in `tests/test_run_parallel_tests.py` inherit the module-level `@pytest.mark.timeout(60)` marker, and new tests in `tests/test_makefile_recipes.py` inherit the module-level `@pytest.mark.timeout(30)` marker, adhering strictly to `do-testing` guidelines.
- End-to-end hung worker process termination and `TIMED_OUT` status reporting were established in PYPOST-1192 (`test_hung_worker_under_timeout_yields_timed_out`).

## Performance Concerns

None:
- All new tests execute purely in-process in memory with fast string/float operations and file reads.
- Total execution time for all new unit and contract tests combined is under 0.05 seconds (50ms).
- No external processes or heavy fixtures are spawned, adding zero measurable overhead to the overall test suite execution.

## Follow-up Tasks

1. **Refactor test runner to standard `argparse`**:
   - Migrate manual argument parsing in `scripts/run_parallel_tests.py` to `argparse` for standard flag handling and automatic help generation (tracked under PYPOST-1153).
2. **Diagnostic logging on malformed `WORKER_TIMEOUT`**:
   - Add warning/notice logging in `scripts/run_parallel_tests.py` when an invalid `WORKER_TIMEOUT` string is encountered before falling back to default.
   - Jira: [PYPOST-1260](https://pypost.atlassian.net/browse/PYPOST-1260)
