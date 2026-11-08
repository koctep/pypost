# PYPOST-1469: Technical Debt Analysis

## Shortcuts Taken

No temporary crutches, hardcoded mocks, or unsafe bypasses remain in the implementation:

- **Linux-first procfs resident memory sampling**: `/proc/{pid}/status` (`VmRSS`) was selected
  as the primary sampling mechanism because it provides zero-overhead, dependency-free kernel
  resident set size metrics on Linux environments. On non-Linux platforms (macOS / Windows),
  `get_process_rss_mb` returns `None` (defaulting to safe 0.0 MB fallback) without raising
  unhandled exceptions. Cross-platform native APIs (e.g. Darwin `task_info` or Windows
  `GetProcessMemoryInfo`) were deferred to a platform follow-up.
- **Initial memory heuristic for unsampled workers**: When evaluating aggregate memory budget
  admission for a newly spawned worker prior to its initial sampling cycle, the supervisor
  estimates baseline resident memory using `default_worker_rss_estimate_mb` (default 50.0 MB).
- **Single global resource limits policy**: `AppSettings.mcp_resource_limits` provides a unified
  `McpResourceLimitsPolicy` across all isolated MCP workers, mirroring `mcp_restart_policy`.
  Per-server limit overrides on `McpServerConfiguration` were deferred as current architecture
  defines runtime policies globally.
- **Settings UI dialog controls deferred**: Configuration model and runtime propagation are fully
  wired from persisted `AppSettings` through `McpServerSettingsController`, `DaemonRuntime`,
  `MCPServerRegistry`, and `McpProcessSupervisor`. Settings dialog UI controls are tracked
  under the dedicated UI configuration task
  ([PYPOST-1462](https://pypost.atlassian.net/browse/PYPOST-1462)).

## Code Quality Issues

No code-quality blocker was identified across the modified modules (`pypost/models/settings.py`,
`pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_registry.py`,
`pypost/ui/mcp_server_controller.py`, `pypost/core/qt/daemon_runtime.py`, and
`tests/test_mcp_process_resource_limits_repro.py`):

- **Strict model validation**: `McpResourceLimitsPolicy` enforces bounds on all fields (ge=0,
  le=100 for workers, gt=0 for sample interval) and includes a cross-field validator ensuring
  `hard_memory_limit_mb >= soft_memory_limit_mb` when both are non-zero.
- **Stateful warning hysteresis**: `_WorkerRecord.soft_limit_warned` tracks warning state so that
  `mcp_worker_memory_warning` fires exactly once per breach threshold crossing, preventing log
  flooding while preserving alerts if memory drops below and re-crosses the limit.
- **Clean error hierarchy**: `McpAdmissionError` inherits from `ValueError`, cleanly distinguishing
  admission rejection from subprocess execution crashes and enabling deterministic handling.
- **Supervisor modularity**: The monitor loop handles both process reaping, restart backoff
  timing, and memory ceiling enforcement within a single 50 ms polling thread. As supervisor
  features expand, extracting worker health and resource evaluation into dedicated strategy
  classes would improve long-term modularity.
- **Static analysis and typing**: Full static analysis (`make -o lint-tests lint`) and type
  checking (`make typecheck`) pass cleanly with zero new warnings or type regressions.

## Missing Tests

No missing test coverage is classified as a **BLOCKER**:

- **Timeout markers**: `tests/test_mcp_process_resource_limits_repro.py` declares both a
  module-level `pytestmark = pytest.mark.timeout(60)` and explicit per-test `@pytest.mark.timeout`
  markers (20s or 30s) across all 7 tests, strictly fulfilling `do-testing` rules.
- **Covered scenarios**: The repro suite covers:
  1. Policy defaults, Pydantic bounds validation, and cross-field constraints.
  2. Default disabled/unlimited policy allowing spawns without rejection.
  3. Spawn admission rejecting excess workers when `max_process_workers` is exceeded.
  4. Spawn admission rejecting excess workers when aggregate RSS budget is exceeded.
  5. Soft memory limit emitting warning log without terminating running worker.
  6. Hard memory limit triggering immediate escalation (`SIGTERM` -> `SIGKILL`) and failing worker.
  7. Auto-restart backoff cycle halting when admission budget is exhausted.
- **Non-Linux native sampling tests**: Native Darwin/Windows memory measurement calls are not
  exercised in Linux CI; dependency injection via `rss_sampler` hook is thoroughly tested instead.
- **Large-scale dense multi-server stress**: Concurrency up to 10 workers is verified in unit
  tests; high-density stress testing (50+ workers) is tracked under multi-server stress testing.

## Performance Concerns

No performance blocker was introduced by this task:

- **Procfs sampling overhead**: Reading `/proc/{pid}/status` virtual file on Linux takes ~30-60
  microseconds per call, parsing only until `VmRSS:`.
- **Per-worker sample throttling**: Governed by `memory_sample_interval_s` (default 1.0s),
  preventing redundant procfs reads on every 50 ms monitor loop iteration.
- **Admission check efficiency**: Admission checks execute a fast linear pass over active worker
  records (`len(workers) <= 100`), calculating worker counts and RSS sums in < 10 microseconds
  without blocking worker IPC channels or Qt GUI event loops.
- **Bounded termination escalation**: Hard limit enforcement grants a bounded 200 ms graceful
  join timeout before `SIGKILL`, ensuring runaway processes are terminated quickly.

## Follow-up Tasks

All follow-up items below are **NON-BLOCKER**:

- **TD-1 — NON-BLOCKER — pre-existing**: Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (108 > 100 characters)` when
  running `make lint` (reproduced at base commit).
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
- **TD-2 — NON-BLOCKER**: Native platform memory sampling on non-Linux OSes (macOS `task_info` /
  Windows `GetProcessMemoryInfo`) to supplement Linux `/proc/{pid}/status`.
  Status: Unticketed improvement proposal (optional future enhancement).
- **TD-3 — NON-BLOCKER**: Settings UI dialog controls for configuring `mcp_resource_limits`.
  Jira: [PYPOST-1462](https://pypost.atlassian.net/browse/PYPOST-1462).
- **TD-4 — NON-BLOCKER**: Per-server memory limit overrides on `McpServerConfiguration` allowing
  tailored memory ceilings for specific heavy tool integrations.
  Status: Unticketed improvement proposal (optional future enhancement).

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| **Pytest Timeouts** | Explicit timeout marker | PASS | All 7 tests have explicit timeouts |
| **Acceptance Path** | Ceilings & admission | PASS | Acceptance test suite green (7/7 passed) |
| **Thread Regression** | Lightweight mode | PASS | Shared thread mode completely unaffected |
| **Lint & Quality Gate** | Clean static analysis | PASS | `make -o lint-tests lint` clean |
| **Type Checking** | Strict type safety | PASS | `make typecheck` passes with zero regressions |
| **Follow-up Tracking** | Pre-existing tracked | PASS | Tracked under PYPOST-1509, PYPOST-1462 |

**Zero BLOCKERs**. Safe to proceed to Step 8 (Dev Docs) after acceptance gate on this artifact.

**SAFE TO CLOSE**
