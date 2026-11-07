# Roadmap: PYPOST-1466

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business purpose established by the approved MCP Process Reliability sprint and deferred
    isolated-server auto-restart recovery policy from PYPOST-1439 (TD-5).
  - Requirements documented in `ai-tasks/PYPOST-1466/10-requirements.md` covering opt-in
    automatic restart with progressive backoff versus default immediate failure, configurable
    retry limits, recovery counter reset after sustained healthy uptime, cancellation on
    operator stop/reconfigure/shutdown, state preservation across restarts, and operator
    visibility.
- [x] **STEP 2: High-Level Architecture Design**
  - Designed `McpWorkerRestartPolicy` (`enabled=False`, `max_retries=3`, `initial_backoff_s=0.5`,
    `max_backoff_s=8.0`, `backoff_multiplier=2.0`, `healthy_reset_window_s=30.0`) on `AppSettings`
    with wiring through `McpServerSettingsController`, `DaemonRuntime`, `MCPServerRegistry`, and
    `McpProcessSupervisor`.
  - Designed non-blocking deadline-driven exponential backoff scheduling, healthy uptime counter
    reset, `_WorkerSpawnSpec` snapshot preservation across live tool/variable updates, immediate
    cancellation via `cancel_event` on `stop_worker`/`reconfigure`/`shutdown`, and recovery status
    transitions (`starting` -> `running` or terminal `failed`) in
    `ai-tasks/PYPOST-1466/20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - Created red acceptance test suite in `tests/test_mcp_process_autorestart_repro.py` covering all
    7 architectural acceptance checks from `ai-tasks/PYPOST-1466/20-architecture.md` with explicit
    per-test `@pytest.mark.timeout` markers, bounded polling helpers, and full process teardown.
  - Verified red failure output via `make test WORKERS=1` with
    `PYTEST_ARGS='tests/test_mcp_process_autorestart_repro.py -q'` (7 collected, 7 failed in
    `/tmp/PYPOST-1466-step3-red.log`):
    - `test_restart_policy_settings_defaults_and_validation`: `FAILED` (`AssertionError`:
      `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_default_policy_disabled_fails_immediately_without_retry`: `FAILED` (`AssertionError`:
      `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_auto_restart_recovers_crashed_worker_with_exponential_backoff_and_latest_state`:
      `FAILED` (`AssertionError`: `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_auto_restart_exhaustion_transitions_to_failed_after_max_retries`: `FAILED`
      (`AssertionError`: `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_healthy_reset_window_resets_retry_counter_for_later_crash`: `FAILED`
      (`AssertionError`: `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_operator_stop_and_shutdown_cancel_pending_backoff_immediately`: `FAILED`
      (`AssertionError`: `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
    - `test_initial_start_failure_does_not_trigger_auto_restart`: `FAILED` (`AssertionError`:
      `McpWorkerRestartPolicy is not defined in pypost.models.settings`)
- [x] **STEP 4: Development**
  - [x] Implemented `McpWorkerRestartPolicy` configuration model on `AppSettings` with defaults
    (`enabled=False`, `max_retries=3`, `initial_backoff_s=0.5`, `max_backoff_s=8.0`,
    `backoff_multiplier=2.0`, `healthy_reset_window_s=30.0`), Pydantic bounds validation, and
    `backoff_for_attempt(attempt)` exponential calculation in `pypost/models/settings.py`.
  - [x] Implemented supervisor auto-restart lifecycle in `pypost/core/mcp_process_supervisor.py`:
    retained `_WorkerSpawnSpec` snapshot on `_WorkerRecord`, synchronized snapshot during live
    `update_tools`/`update_variables`, scheduled non-blocking monotonic backoff deadlines, reset
    consecutive retry counters after sustained healthy uptime window, dispatched asynchronous
    retry respawn attempts, and enforced immediate cancellation via `cancel_event` on `stop_worker`
    and `shutdown`.
  - [x] Updated `ProcessServerRunner` in `pypost/core/mcp_server_runner.py` with `is_restarting()`
    and `retry_count()` methods and preserved tool and variable snapshot mutations during in-flight
    backoff windows.
  - [x] Wired `restart_policy` through `MCPServerRegistry` (`pypost/core/mcp_server_registry.py`),
    `McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`), and `DaemonRuntime`
    (`pypost/core/qt/daemon_runtime.py`), handling `on_worker_restarting` (transitional `starting`
    state with progress message) and `on_worker_restarted` (`running` state), ensuring
    `reconfigure`, `stop`, `stop_all`, `remove`, and `clear` cancel pending backoff retries.
  - [x] Enhanced `mcp_worker_process.py` and `spawn_worker` startup failure handling to notify
    `START_FAILED` immediately on initial bind failures and clean up failed child processes,
    preventing initial start failures from entering the auto-restart loop (`FR7`).
  - [x] Verified all 7 acceptance tests in `tests/test_mcp_process_autorestart_repro.py` pass and
    all regression suites (`test_mcp_process_tool_refresh_repro.py`,
    `test_mcp_process_proxy_repro.py`, `test_mcp_process_reconfigure_repro.py`,
    `test_mcp_process_isolation_repro.py`) pass without error.
  - [x] Validated static analysis and type checks: `make -o lint-tests lint` passed and
    `make typecheck` passed with 0 baseline regressions.
- [x] **STEP 5: Code Cleanup**
  - Verified all modified files (`pypost/models/settings.py`,
    `pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_runner.py`,
    `pypost/core/mcp_server_registry.py`, `pypost/core/mcp_worker_process.py`,
    `pypost/ui/mcp_server_controller.py`, `pypost/core/qt/daemon_runtime.py`,
    `tests/test_mcp_process_autorestart_repro.py`) adhere to PEP 8 / `lsr-python` import
    ordering, `<= 100` char line lengths, single trailing newlines, no trailing whitespace,
    and zero debug prints or dead code.
  - Confirmed all 7 acceptance tests in `tests/test_mcp_process_autorestart_repro.py` have explicit
    `@pytest.mark.timeout` markers (20s, 30s, or 60s) and bounded polling loops.
  - Documented cleanup actions and verification results in
    `ai-tasks/PYPOST-1466/40-code-cleanup.md`.
  - Verified quality gates: `make -o lint-tests lint` passed, `make typecheck` passed, `make test
    WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_autorestart_repro.py -q'` passed (7 passed in
    24s), and `make verify-ai-tasks` passed.
- [x] **STEP 6: Observability**
  - Verified structured key-value log formatting across `pypost/core/mcp_process_supervisor.py`
    and `pypost/core/mcp_server_registry.py`: `mcp_worker_restart_scheduled`,
    `mcp_worker_restarted`,
    `mcp_worker_restart_exhausted`, `mcp_worker_restart_counter_reset`, and
    `mcp_worker_restart_cancelled` (`reason=operator_stop` and `reason=supervisor_shutdown`).
  - Verified strict secret safety (`FR8`): variables maps, secret tokens, headers, upstream URLs,
    and tool payloads are excluded from logs.
  - Added automated `caplog` test assertions in `tests/test_mcp_process_autorestart_repro.py`
    verifying structured event emission, parameters, and secret absence.
  - Documented logging schemas, secret safety, metrics, and test assertions in
    `ai-tasks/PYPOST-1466/50-observability.md`.
  - Verified quality gates: `make -o lint-tests lint` passed, `make typecheck` passed,
    `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_autorestart_repro.py -q'` passed (7
    passed in 24s), and `make verify-ai-tasks` passed.
- [x] **STEP 7: Technical Debt Analysis**
  - Analyzed shortcuts taken, code quality issues, missing test coverage, and performance
    characteristics in `ai-tasks/PYPOST-1466/60-tech-debt.md`.
  - Evaluated pre-existing test lint in `tests/test_mcp_server_registry.py:308:101` (PYPOST-1509),
    Settings UI dialog controls (deferred under PYPOST-1462), IPC version negotiation (PYPOST-1467),
    active HEARTBEAT watchdog (PYPOST-1468), memory limits/spawn admission (PYPOST-1469), and
    process-mode 10x stress parity + Windows stop CI (PYPOST-1470).
  - Executed blocker review across all 7 mandatory gates: confirmed 0 blockers exist (all tests
    marked with explicit pytest timeouts, acceptance path green, thread mode regression passing,
    and all follow-ups ticketed in Jira).
- [x] **STEP 8: Dev Docs**
  - Updated developer documentation in `doc/dev/mcp_process_isolation.md`:
    - Documented `McpWorkerRestartPolicy` configuration on `AppSettings.mcp_restart_policy`
      with defaults (`enabled=False`, `max_retries=3`, `initial_backoff_s=0.5`,
      `max_backoff_s=8.0`, `backoff_multiplier=2.0`, `healthy_reset_window_s=30.0`), Pydantic
      bounds validation, and example configuration snippet.
    - Documented supervisor non-blocking deadline scheduling, monotonic timers, and exponential
      backoff delay formula.
    - Documented consecutive failure counter reset after sustained healthy operation
      (`healthy_reset_window_s=30.0`).
    - Documented immediate cancellation on explicit operator stop, reconfigure, or supervisor
      shutdown via `cancel_event`.
    - Documented state snapshot preservation across restarts (`_WorkerSpawnSpec` on
      `_WorkerRecord`) during live tool and variable updates.
    - Documented fast startup failure distinction (`FR7`) bypassing retry loop on initial
      bind or worker spawn errors.
    - Documented structured observability log events (`mcp_worker_restart_scheduled`,
      `mcp_worker_restarted`, `mcp_worker_restart_exhausted`, `mcp_worker_restart_counter_reset`,
      `mcp_worker_restart_cancelled`) and secret safety (`FR8`).
    - Added troubleshooting guide rows for restart exhaustion, startup bypass, and pending backoff.
    - Added automated test reference for `tests/test_mcp_process_autorestart_repro.py`.
  - Verified quality gates: `make -o lint-tests lint` passed (flake8, markdown lint, link check)
    and `make verify-ai-tasks` passed.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1466/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1466/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_process_autorestart_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1466/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1466/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1466/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
