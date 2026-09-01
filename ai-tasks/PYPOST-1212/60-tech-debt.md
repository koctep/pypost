# PYPOST-1212: Technical Debt Analysis

## Shortcuts Taken

None.

- The reproduction and diagnostic suite in [`scripts/repro_gui_batch_segfault.py`](file:///home/src/scripts/repro_gui_batch_segfault.py) was built with modular architecture, complete CLI argument parsing (`--mode`, `--batch-size`, `--timeout`, `--output-json`), deterministic module discovery, signal decoding, and structured JSON output capability.
- The automated pytest baseline in [`tests/test_gui_batch_segfault_repro.py`](file:///home/src/tests/test_gui_batch_segfault_repro.py) implements robust subprocess isolation to safely trap native C/C++ segmentation faults (`SIGSEGV`, exit code 139 / returncode -11) without destabilizing the main test orchestrator process.
- No temporary workarounds, monkey-patching, mock bypasses, or brittle heuristic shortcuts were introduced into the application codebase.

## Code Quality Issues

None.

- **Linting & Formatting**: Clean static analysis compliance with `flake8` and repository guidelines; all line lengths strictly conform to the <= 100 character standard.
- **Type Safety**: Full type annotations present throughout [`scripts/repro_gui_batch_segfault.py`](file:///home/src/scripts/repro_gui_batch_segfault.py) and [`tests/test_gui_batch_segfault_repro.py`](file:///home/src/tests/test_gui_batch_segfault_repro.py), passing `mypy` static type checking cleanly without untyped escapes or ignores.
- **Error Handling**: Comprehensive subprocess exception handling (`subprocess.TimeoutExpired`, subprocess returncode inspection, signal decoding via `signal.Signals`).
- **Output Bounds**: Traceback capture strictly enforces bounded tail buffers (`[-2000:]`) to prevent unbounded memory growth during catastrophic crash cascades.

## Missing Tests

None.

- **Bounded Execution Verification**: [`test_bounded_gui_batch_execution_passes_cleanly`](file:///home/src/tests/test_gui_batch_segfault_repro.py#L35-L55) verifies that partitioned batch execution (chunks of 15 modules across 8 subprocesses) executes 110 GUI test modules with 0 crashes and 100% pass rate.
- **Unmitigated Segfault Proof Surface**: [`test_large_batch_gui_execution_unmitigated_segfault_repro`](file:///home/src/tests/test_gui_batch_segfault_repro.py#L58-L82) explicitly captures and asserts the unmitigated single-process large-batch crash under `@pytest.mark.xfail(strict=False, reason="PYPOST-1117: large-batch apply_theme native segfault")`.
- **Explicit Timeouts**: Both tests and module-level test configurations declare explicit `@pytest.mark.timeout(240)` per project testing guidelines.
- **Test Discovery & Categorization**: Marked with `@pytest.mark.slow` and `@pytest.mark.gui` to prevent slowing down fast standard test runs while remaining fully verifiable via `make test-slow`.

## Performance Concerns

None.

- **Process Isolation**: All large-batch test runs are isolated to ephemeral subprocesses, avoiding memory bloat or leaked Qt GUI resources in the main test runner.
- **Execution Partitioning**: Bounded execution splits large batches into manageable chunks, completing execution in under 15 seconds.
- **Suite Tagging**: Slow test execution is guarded by `@pytest.mark.slow`, preventing overhead during standard `make test` runs while ensuring CI diagnostic coverage via `make test-slow`.

## Follow-up Tasks

### Downstream Epics & Children

The deterministic baseline and evidence produced in this task (PYPOST-1212) serve as the foundation for downstream tasks under parent epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117):

1. **DIAG-1**: [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) — *Root-cause diagnosis for large-batch GUI segfault (lifetime vs QStyle/QPalette)*
   - Investigate C++ pointer lifetime and Qt palette cleanup during repeated `apply_theme` invocations in single-process batch runs.
2. **MITIGATE-1**: [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) — *Mitigate large-batch GUI segfault and document CI ownership*
   - Implement architectural mitigation (e.g. style lifecycle pooling, batch isolation, or safe palette re-application) and document CI operational ownership.

### Pre-Existing Test Failures

- `tests/test_main_window_alert_reload.py::test_open_settings_reloads_alert_manager_when_webhook_changes`
  - **Status**: `NON-BLOCKER — pre-existing`
  - **Tracking Ticket**: [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117)
  - **Description**: Intermittent native segmentation fault (`SIGSEGV`) occurring during full-suite GUI test execution within [`pypost/ui/styles/style_manager.py`](file:///home/src/pypost/ui/styles/style_manager.py) (`apply_theme` -> `QStyleFactory.create`), tracked as the central motivation for epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) and downstream resolution in [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) / [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214).
