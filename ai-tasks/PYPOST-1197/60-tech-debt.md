# PYPOST-1197: Technical Debt Analysis

## Shortcuts Taken

None. A robust and self-contained process group termination utility `kill_process_group(pid: int)` was implemented in `scripts/run_parallel_tests.py`:
- Configured `subprocess.Popen(..., start_new_session=True)` on POSIX systems so worker test processes and any spawned children belong to their own process group session (`setsid()`).
- On POSIX, `kill_process_group` resolves the process group id using `os.getpgid(pid)` (with graceful fallback to `pgid = pid` if lookup fails) and issues `os.killpg(pgid, signal.SIGKILL)`.
- On Windows, `kill_process_group` issues `os.kill(pid, signal.SIGTERM)` as a cross-platform fallback without external dependencies.
- Full exception suppression (`ProcessLookupError`, `PermissionError`, `OSError`) is implemented with debug-level logging to ensure race conditions or already-reaped processes never crash the test runner.
- Enriched stderr message and `TestStatus.TIMED_OUT` exit code `-9` are cleanly recorded.

## Code Quality Issues

| Item | Priority | Notes |
| ---- | -------- | ----- |
| `kill_process_group` co-location in `scripts/run_parallel_tests.py` | Low | Kept co-located to avoid creating cross-module dependencies or coupling test runner scripts to core application packages. Could be moved to a shared CLI/process utility if needed elsewhere in the future. |
| Windows fallback uses `os.kill(pid, SIGTERM)` | Low | On Windows, process groups are not supported natively without Win32 Job Objects. Direct `os.kill` is sufficient for current requirements since the primary runtime and CI environments are POSIX (Linux). |

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| Repro test: worker timeout terminates grandchild process group | Covered | `tests/test_run_parallel_tests.py::test_worker_timeout_terminates_grandchild_process_group` |
| Mock test: worker timeout yields `TIMED_OUT` and calls `kill_process_group` | Covered | `tests/test_run_parallel_tests.py::test_hung_worker_under_timeout_yields_timed_out` |
| Unit test: POSIX process group kill with `os.killpg` | Covered | `tests/test_run_parallel_tests.py::test_kill_process_group_posix` |
| Unit test: POSIX fallback when `os.getpgid` fails | Covered | `tests/test_run_parallel_tests.py::test_kill_process_group_posix_fallback_on_lookup_error` |
| Unit test: exception suppression and debug logging | Covered | `tests/test_run_parallel_tests.py::test_kill_process_group_posix_suppresses_exceptions` |
| Unit test: Windows fallback path | Covered | `tests/test_run_parallel_tests.py::test_kill_process_group_win32` |
| Test timeouts | Covered | All test cases have explicit `@pytest.mark.timeout(...)` markers and module-level `pytestmark = pytest.mark.timeout(60)` per `do-testing` requirements. **NO BLOCKER**. |

## Performance Concerns

- **Negligible overhead**: `start_new_session=True` performs a `setsid()` syscall during child process fork/exec, adding sub-microsecond overhead.
- **Zero steady-state cost**: `kill_process_group` is only invoked when `subprocess.TimeoutExpired` is caught, so passing and normally failing tests experience no performance overhead.
- **Suite throughput**: Parallel test runner completed the 318-file test suite in 161.64s wall-clock time (1185.61s cumulative CPU duration, achieving a 7.3x speedup).

## Follow-up Tasks

| Item | Priority / Classification | Notes / Jira Key |
| ---- | ------------------------- | ---------------- |
| `tests/test_main_window_alert_reload.py` crashes with SIGSEGV under full-suite run | NON-BLOCKER — pre-existing | [PYPOST-1251](https://pypost.atlassian.net/browse/PYPOST-1251) — Pre-existing Qt theme teardown native crash (`apply_theme` in `apply_appearance` / `MainWindow.open_settings`), unrelated to process group runner changes. |
| Extract `kill_process_group` into shared utility | Low / Non-blocker | Optional future refactor if other scripts require process group signaling. No ticket needed at this time. |
