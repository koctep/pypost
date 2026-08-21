# PYPOST-1046: Technical Debt Analysis

## Shortcuts Taken

1. **Process-wide `sys.exit` interception for worker threads (`server_bind.py`)**:
   - *Description*: Uvicorn internally calls `sys.exit(1)` when socket binding fails on background
     worker threads. To prevent process abort and capture typed bind errors without patching
     uvicorn internals, `pypost/core/server_bind.py` uses a process-level `sys.exit` wrapper with
     thread-local dispatch and reference counting (`install_thread_exit`/`uninstall_thread_exit`).
   - *Compromise*: While thread-safe and isolated via thread-local state, monkey-patching `sys.exit`
     is a runtime interception compromise. A cleaner long-term design would use custom ASGI server
     bindings or upstream uvicorn server hooks when available.

2. **Qt Core signal wakeup heartbeat timer (`daemon.py`)**:
   - *Description*: Python signal handlers are only processed when the interpreter runs bytecode.
     Because `QCoreApplication.exec()` blocks in native C++ event loops, a 500ms recurring `QTimer`
     heartbeat was installed in `pypost/daemon.py` to yield execution back to Python periodically.
   - *Compromise*: A 500ms timer induces two wakeups per second. A fully idle event loop could
     instead integrate POSIX `signal.set_wakeup_fd` with `QSocketNotifier`.

3. **Hardcoded default startup timeout (`daemon_runtime.py`)**:
   - *Description*: `DaemonRuntime` defaults to a 10-second startup deadline (`startup_timeout_ms`).
   - *Compromise*: This value is configurable via code injection but not currently exposed as a
     dedicated CLI argument (e.g. `--startup-timeout-ms`) or environment variable.

4. **Count-only logging for unreferenced corrupt records (`daemon_storage.py`)**:
   - *Description*: To protect against accidental leakage of sensitive filenames or paths in
     shared log aggregators, unreferenced invalid/corrupt records in collection or environment
     directories are aggregated and logged as count-only warnings
     (`daemon_storage_records_skipped`).
   - *Compromise*: Operators cannot determine which specific unreferenced files were corrupt from
     the logs alone without manually inspecting the directory.

## Code Quality Issues

1. **`StorageManager` coupling to legacy single-root layout (`storage.py`)**:
   - *Description*: `StorageManager` now supports independent `collections_dir` and
     `environments_dir`, delegating strict loading to `pypost/core/daemon_storage.py`. However,
     `StorageManager` still retains legacy methods (`_ensure_paths`, `_read_environment_records`)
     that assume a single `data_dir` parent root.
   - *Improvement*: Decompose `StorageManager` into dedicated `CollectionsRepository` and
     `EnvironmentsRepository` classes with clean interface boundaries.

2. **Inline import for storage path initialization (`storage.py`)**:
   - *Description*: `StorageManager.__init__` performs a delayed import of
     `initialize_selected_paths` from `pypost.core.daemon_storage` to decouple
     default-initialization rules from legacy construction.
   - *Improvement*: Refactor module dependency structure and constructor injection to avoid late
     imports in `__init__`.

3. **In-memory model deep copying (`daemon_storage.py`)**:
   - *Description*: `load_collections_snapshot_strict` and `load_environments_snapshot_strict`
     return deep copies of models wrapped in `MappingProxyType`.
   - *Improvement*: For large datasets, investigate read-only frozen Pydantic models or persistent
     immutable views to avoid duplicate deep copying on startup.

## Missing Tests

1. **Long-running daemon soak test**:
   - *Description*: Existing automated suites thoroughly test startup, signal handling, graceful
     shutdown, and failure paths. However, there is no multi-hour soak test verifying memory
     stability under continuous MCP request processing in headless mode.
   - *Coverage*: Dedicated soak tests belong in periodic nightly/extended test workflows.

2. **Windows console control signal coverage**:
   - *Description*: Signal handling tests verify POSIX `SIGINT` and `SIGTERM`. Windows-specific
     console events (`CTRL_C_EVENT`, `CTRL_CLOSE_EVENT`) are not exercised in the current Linux CI.

3. **Stress benchmark for directory scanning with massive file counts**:
   - *Description*: `load_collections_snapshot_strict` scans directory entries matching `*.json`.
     No automated benchmark exists for directories containing >10,000 JSON collection files.

4. **Explicit timeout marker compliance**:
   - *Status*: Complete. All test items declare explicit `@pytest.mark.timeout` or module-level
     `pytestmark = pytest.mark.timeout(...)` in accordance with `do-testing` guidelines.

## Performance Concerns

1. **Startup I/O scaling with collections directory file count**:
   - *Concern*: `load_collections_snapshot_strict` evaluates all `*.json` candidates in the
     configured directory to match required IDs. If an operator provides a directory containing
     tens of thousands of JSON files, startup I/O will scale with directory file count rather than
     the number of enabled MCP servers.
   - *Mitigation*: Collection files typically follow `{id}.json` naming; a fallback to fast
     direct file lookups before broad globbing could optimize startup for huge directories.

2. **Periodic timer wakeups during idle daemon execution**:
   - *Concern*: The 500ms heartbeat timer wakes the event loop twice per second.
   - *Impact*: CPU utilization remains <0.01%, but true zero-wake sleep would reduce energy
     consumption on resource-constrained embedded systems.

## Follow-up Tasks

### Planned Improvements

1. **PYPOST-DAEMON-TIMEOUT**: Add `--startup-timeout-ms` CLI flag and
   `PYPOST_DAEMON_STARTUP_TIMEOUT_MS` environment variable to configure startup timeout.
2. **PYPOST-STORAGE-DECOUPLE**: Refactor `StorageManager` into decoupled `CollectionsRepository`
   and `EnvironmentsRepository` components.
3. **PYPOST-DAEMON-WAKEUP**: Migrate `daemon.py` signal heartbeat from `QTimer` to
   `signal.set_wakeup_fd` with `QSocketNotifier`.
4. **PYPOST-STORAGE-INDEX**: Implement direct `{id}.json` probe optimization in strict collection
   loading to minimize directory globbing I/O on large datasets.

### NON-BLOCKER — pre-existing full-suite failures

The following failures reproduce at the task base commit
`082ff6aab23f0a9e3ba34c284c9e7f2b72ea21da`. They are unrelated to the daemon-mode
implementation and are already tracked in Jira.

Repro command in the PYPOST-1046 working tree:

```sh
make test PYTEST_ARGS="\
tests/test_pypost_1077_verification_artifacts.py\
::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates \
tests/test_solid_audit_baseline.py\
::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics \
tests/test_suite_qapp_alignment.py\
::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication \
-q"
```

Baseline evidence command:

```sh
make -C /tmp/baseline-PYPOST-1046 test PYTEST_ARGS="\
tests/test_pypost_1077_verification_artifacts.py\
::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates \
tests/test_solid_audit_baseline.py\
::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics \
tests/test_suite_qapp_alignment.py\
::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication \
-q"
```

1. Audit discovery and inventory snapshots are stale.
   - Node:
     `tests/test_pypost_1077_verification_artifacts.py`
     `::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
   - Failure: expected eight dialog modules totaling 1,030 LOC and
     `mcp_servers_dialog.py` at 333 LOC; the discovered inventory differs.
   - Suspected cause: audit artifacts were not regenerated after earlier dialog refactors.
   - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)
2. The committed SOLID metrics snapshot is stale.
   - Node:
     `tests/test_solid_audit_baseline.py`
     `::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
   - Failure: the committed `main_window.py` snapshot records 433 LOC while the base commit
     measures 443 LOC.
   - Suspected cause: the metrics snapshot was not regenerated after earlier refactors.
   - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111)
3. A test module still owns a local Qt application fixture.
   - Node:
     `tests/test_suite_qapp_alignment.py`
     `::test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
   - Failure: `test_mcp_controls_presenter.py` defines local `qapp()` instead of using the
     shared fixture.
   - Suspected cause: the test predates the shared-fixture guardrail migration.
   - Jira: [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110)

Classification for PYPOST-1046: **NON-BLOCKER — pre-existing**. The baseline worktree was
removed after reproduction.
