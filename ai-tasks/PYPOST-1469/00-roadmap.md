# Roadmap: PYPOST-1469

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business purpose established from approved sprint goals and originating tech debt PYPOST-1439
    (TD-8) for MCP process-mode memory ceilings and spawn admission control.
  - Requirements documented in `ai-tasks/PYPOST-1469/10-requirements.md` covering configurable spawn
    admission limits, actionable admission rejection without disrupting active servers,
    configurable per-worker memory ceilings (soft warning and hard termination thresholds),
    periodic memory monitoring and runaway process containment, interaction with automatic restart
    recovery, shared-mode compatibility, and secret-safe operational diagnostics.
- [x] **STEP 2: High-Level Architecture Design**
  - Policy configuration model designed for `pypost/models/settings.py`:
    `McpResourceLimitsPolicy` embedded on `AppSettings.mcp_resource_limits`.
  - Spawn admission control designed for `McpProcessSupervisor.spawn_worker`:
    enforces `max_process_workers` and `max_total_rss_mb` boundaries with `McpAdmissionError`
    without impacting running workers, and halts auto-restart backoff if admission is refused.
  - Periodic memory sampling and dual-threshold ceiling enforcement designed for
    `McpProcessSupervisor._monitor_loop`: soft warnings on threshold crossing and controlled
    `SIGTERM` -> `SIGKILL` termination on hard threshold crossing with status `failed`.
  - Registry and runner integration designed for graceful start/reconfigure error handling,
    secret-safe logging, and shared-mode compatibility.
  - Step 3 failing repro test suite specified in `20-architecture.md` targeting
    `tests/test_mcp_process_resource_limits_repro.py`.
- [x] **STEP 3: Failing Repro Test**
  - Created red acceptance test suite in `tests/test_mcp_process_resource_limits_repro.py`
    covering all 7 architectural acceptance checks from `ai-tasks/PYPOST-1469/20-architecture.md`
    with explicit per-test `@pytest.mark.timeout` markers, module-level timeout, bounded polling
    helpers, and full process/registry teardown.
  - Verified red failure output via `make test WORKERS=1` with
    `PYTEST_ARGS='tests/test_mcp_process_resource_limits_repro.py -q'` (7 collected, 7 failed in
    `/tmp/PYPOST-1469-step3-red.log`):
    - `test_resource_limits_policy_settings_defaults_and_validation`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_default_policy_unlimited_allows_spawns_without_rejection`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_spawn_admission_worker_count_limit_rejects_excess_spawns`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_spawn_admission_total_rss_budget_rejects_excess_spawns`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_soft_memory_limit_emits_warning_without_killing_worker`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_hard_memory_limit_escalates_and_terminates_runaway_worker`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
    - `test_admission_exhaustion_halts_autorestart_backoff_cycle`: `FAILED` (`AssertionError`:
      `McpResourceLimitsPolicy is not defined in pypost.models.settings`)
- [x] **STEP 4: Development**
  - [x] Defined `McpResourceLimitsPolicy` model on `AppSettings` with defaults, bounds validation,
    and cross-field validation (`hard_memory_limit_mb >= soft_memory_limit_mb`) in
    `pypost/models/settings.py`.
  - [x] Implemented `McpAdmissionError` and spawn admission gate in
    `pypost/core/mcp_process_supervisor.py` enforcing `max_process_workers` and `max_total_rss_mb`
    boundaries before process creation.
  - [x] Implemented `/proc/{pid}/status` `VmRSS` memory sampling with fallback and background
    dual-threshold monitoring in `McpProcessSupervisor._monitor_loop`: soft limit emits structured
    warning `mcp_worker_memory_warning` and hard limit triggers `SIGTERM` -> `SIGKILL` escalation,
    marking state `failed` with reason `memory_limit_exceeded`.
  - [x] Harmonized admission checks with auto-restart recovery in `_attempt_restart`: admission
    rejection halts backoff loops, marks worker `failed`, logs rejection diagnostic, and notifies
    unexpected exit.
  - [x] Wired `resource_limits` through `MCPServerRegistry`, `McpServerSettingsController`, and
    `DaemonRuntime`, ensuring graceful error propagation and backward compatibility with shared
    thread mode.
  - [x] Verified all 7 acceptance tests in `tests/test_mcp_process_resource_limits_repro.py` pass,
    along with regression suites (`test_mcp_process_autorestart_repro.py`,
    `test_mcp_process_tool_refresh_repro.py`, `test_mcp_process_proxy_repro.py`).
- [x] **STEP 5: Code Cleanup**
  - Formatted and verified code across modified modules and test suites per `lsr-python` and
    `lsr-requirements` (all lines <= 100 characters, clean imports, zero debug prints).
  - Verified explicit per-test `@pytest.mark.timeout(...)` markers on all test methods in
    `tests/test_mcp_process_resource_limits_repro.py`.
  - Created cleanup report in `ai-tasks/PYPOST-1469/40-code-cleanup.md`.
  - Verified clean quality gates via Makefile: `make -o lint-tests lint`, `make typecheck`,
    `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_resource_limits_repro.py -q'`,
    and `make verify-ai-tasks`.
- [x] **STEP 6: Observability**
  - Reviewed logging in `pypost/core/mcp_process_supervisor.py`: added warning log
    `mcp_worker_spawn_admission_rejected` on spawn capacity/budget violations, updated
    `mcp_worker_restart_admission_rejected` to error severity, and verified memory ceiling logs
    `mcp_worker_memory_warning` and `mcp_worker_memory_exceeded`.
  - Added explicit caplog assertions across `tests/test_mcp_process_resource_limits_repro.py`
    for all 4 structured event types.
  - Documented logging taxonomy, memory metrics via `/proc/{pid}/status`, and validation in
    `ai-tasks/PYPOST-1469/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts taken: Linux procfs `/proc/{pid}/status` used for resident set size
    sampling; non-Linux fallback returns safe `None` (0.0 MB); baseline heuristic RSS estimate
    used for unsampled workers; Settings dialog UI controls tracked under PYPOST-1462.
  - Assessed code quality: clean Pydantic model validation on `McpResourceLimitsPolicy`, stateful
    soft limit hysteresis flag, typed error hierarchy (`McpAdmissionError`), zero type or lint
    regressions.
  - Verified test coverage: all 7 acceptance tests in `test_mcp_process_resource_limits_repro.py`
    pass with explicit per-test timeout markers per `do-testing`.
  - Analyzed performance: procfs sampling overhead < 60 us, per-worker sample interval throttling,
    sub-millisecond admission evaluation.
  - Follow-up tracking: pre-existing line-length failure in `test_mcp_server_registry.py:308`
    recorded as NON-BLOCKER under PYPOST-1509; non-Linux native sampling and per-server overrides
    recorded as non-blocking follow-up opportunities; zero blocker tech debt items.
  - Technical debt documented in `ai-tasks/PYPOST-1469/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` to document the resource limits and spawn admission
    system introduced in PYPOST-1469.
  - Documented `mcp_resource_limits` configuration fields, types, defaults, and bounds on
    `AppSettings` with clean Python wiring snippet.
  - Documented `McpAdmissionError` and spawn admission gate (`_check_admission`) in
    `McpProcessSupervisor.spawn_worker`.
  - Documented periodic Linux procfs memory sampling (`/proc/{pid}/status` `VmRSS`), soft warning
    hysteresis (`mcp_worker_memory_warning`), and hard ceiling escalation (`SIGTERM` -> `SIGKILL`,
    state `failed`, reason `memory_limit_exceeded`).
  - Documented auto-restart recovery interplay halting backoff loops upon admission exhaustion.
  - Updated architecture overview table, troubleshooting matrix, and automated test commands.
  - Verified every line added/updated is <= 100 characters, Markdown lint passes, and artifact
    integrity passes via `make verify-ai-tasks`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1469/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1469/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_process_resource_limits_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1469/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1469/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1469/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
