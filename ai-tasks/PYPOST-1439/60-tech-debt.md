# PYPOST-1439: Technical Debt Analysis

Step 7 technical debt analysis for PYPOST-1439 (*Isolated Execution for Standalone MCP
Servers*). Follow-ups are **UNTICKETED** (no Jira create in this run).

## Shortcuts Taken

1. **Detect + `failed` only — no auto-restart**
   - Architecture explicitly deferred configurable restart-with-backoff. Unexpected child exit
     maps to registry `failed` via `_on_worker_unexpected_exit`; operators must restart manually.
2. **Process-mode reconfigure deferred**
   - `MCPServerRegistry.reconfigure` still builds an `MCPServerManager` candidate and
     `_start_manager` (thread path). Process-mode running instances have no candidate-then-commit
     supervised-child flow. Same-host/port and neighbor-safe reconfigure in process mode is debt.
3. **Proxy servers not started in process workers**
   - `ProcessServerRunner` / `McpProcessSupervisor.spawn_worker` / `mcp_worker_process` always
     construct `MCPServerImpl` from tools. Proxy fields (`upstream_url`, transport, headers,
     timeout) are not carried on START; `MCPProxyServerImpl` is unused in the child. Thread-mode
     proxy path is unchanged.
4. **Settings UI for `mcp_execution_mode` deferred (host wiring DONE)**
   - **DONE (was Step 7 review BLOCKER / FR1 DoD gap):**
     `AppSettings.mcp_execution_mode` is passed as
     `execution_mode=...` when constructing `MCPServerRegistry` in
     `pypost/ui/mcp_server_controller.py` and `pypost/core/qt/daemon_runtime.py`. Persisted
     settings now select thread vs process at host construction (no harness injection required).
   - **Remaining NON-BLOCKER:** Settings dialog still has no execution-mode control; operators
     change mode via persisted `AppSettings` / config until a UI control lands (TD-1).
5. **IPC `v: 1` stamped but not negotiated**
   - `mcp_worker_ipc.make_message` sets `MSG_V = 1`; receivers ignore `v` and do not reject
     mismatched versions.
6. **Active HEARTBEAT unused**
   - Worker answers `HEARTBEAT` → `HEARTBEAT_PONG`, but the supervisor never sends heartbeats;
     liveness is `Process.is_alive()` / `exitcode` polling only.
7. **No per-worker memory ceiling**
   - Evaluation accepts ~30–50 MB RSS per child and 4–5× aggregate cost; no soft/hard RSS cap,
     spawn admission control, or OOM operator messaging beyond OS behavior.

## Code Quality Issues

1. **`refresh_collection` ignores process runners**
   - Iterates `_managers` only; process-mode instances never receive tool list updates after
     start (no `UPDATE_TOOLS` / worker restart path).
2. **`manager_for` / dual tables**
   - Process mode populates `_runners` and skips `_managers`. Callers that still use
     `manager_for` will `KeyError` for process instances; registry surface is asymmetric.
3. **`MCPServerRunnerProtocol` omits `update_tools`**
   - Architecture sketch included tool updates (possibly via worker restart); protocol and
     `ProcessServerRunner` only implement `update_variables`.
4. **Mode change while servers run**
   - Registry fixes mode at construction. No apply-on-next-start messaging, stop-all gate, or
     per-instance mode flip when settings change at runtime.
5. **uvicorn signal setattr dual-path**
   - Worker still `setattr`s both `install_signal_handlers` and `startup` for older stubs vs
     uvicorn 0.54 `capture_signals` (documented in cleanup); keep until uvicorn API stabilizes.

## Missing Tests

1. **No process-mode proxy acceptance** — proxy START / upstream forwarding under spawn.
2. **No process-mode reconfigure / candidate rollback** tests.
3. **No process-mode `refresh_collection` / tool hot-update** tests.
4. **Settings UI control still untested** — host wiring covered
   (`test_app_settings_mcp_execution_mode_reaches_controller_registry`,
   `test_runtime_applies_mcp_execution_mode_from_settings`); no Settings dialog widget test yet.
5. **No IPC version mismatch** test (unknown `v` rejected).
6. **No active HEARTBEAT timeout → failed** test (only crash via DEBUG_ABORT / natural exit).
7. **No Windows-specific SIGTERM/TerminateProcess escalation** CI coverage (POSIX exercised).
8. **No process-mode 10x stress parity** suite (`test_mcp_multiserver_stress_10x.py` remains
   thread-oriented; isolation repro covers 10 servers for variables only).
9. **Timeouts**: isolation repro has module/per-test `pytest.mark.timeout` — **not** a blocker.

Covered by this task’s acceptance suite (`tests/test_mcp_process_isolation_repro.py`):
setting validation, host registry wiring from AppSettings, crash isolation, concurrent variable
isolation (10 servers), bounded STOP→SIGTERM→SIGKILL, thread-mode regression control.

## Performance Concerns

1. **Spawn RSS × N** — each child is a full interpreter (~30–50 MB baseline). Dense process-mode
   desks need operator guidance and eventual admission/memory ceilings (see TD-8).
2. **Spawn latency** — ~150–350 ms per child (evaluation); 10-server cold start is slower than
   thread barrier; acceptable for FR1 trade-off, not tuned further here.
3. **IPC snapshot churn** — every `refresh_environment` sends full variable maps; fine for
   typical env sizes, not incremental diffs.
4. **Reader + monitor threads per supervisor** — one demux reader per worker plus a shared
   monitor loop; fine at 10–20 instances, revisit if density grows much higher.

## Follow-up Tasks

All items below are **NON-BLOCKER** relative to the implemented process-path DoD (crash
isolation, variable isolation, bounded stop, thread regression, FR1 durable setting → registry).
Product Settings UI and several parity paths remain incomplete and should be ticketed separately.
**Jira: ticketed** (PYPOST-1462 … PYPOST-1470).

| ID | Priority | Class | Jira | SP | Summary |
| --- | --- | --- | --- | --- | --- |
| TD-1 | Medium | NON-BLOCKER | [PYPOST-1462](https://pypost.atlassian.net/browse/PYPOST-1462) | 2 | Settings UI control for `mcp_execution_mode` |
| TD-2 | High | NON-BLOCKER | [PYPOST-1463](https://pypost.atlassian.net/browse/PYPOST-1463) | 5 | Process-mode reconfigure (supervised candidate + rollback) |
| TD-3 | High | NON-BLOCKER | [PYPOST-1464](https://pypost.atlassian.net/browse/PYPOST-1464) | 5 | Proxy server parity in process workers |
| TD-4 | Medium | NON-BLOCKER | [PYPOST-1465](https://pypost.atlassian.net/browse/PYPOST-1465) | 3 | Process-mode tool refresh (`UPDATE_TOOLS` / restart) |
| TD-5 | Medium | NON-BLOCKER | [PYPOST-1466](https://pypost.atlassian.net/browse/PYPOST-1466) | 5 | Auto-restart policy with exponential backoff |
| TD-6 | Low | NON-BLOCKER | [PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467) | 2 | IPC protocol version negotiation / reject mismatch |
| TD-7 | Low | NON-BLOCKER | [PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468) | 2 | Active HEARTBEAT watchdog → `failed` |
| TD-8 | Medium | NON-BLOCKER | [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469) | 5 | Per-worker memory ceilings / spawn admission |
| TD-9 | Low | NON-BLOCKER | [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470) | 3 | Process-mode 10x stress parity + Windows stop CI |

### Draft Field Specifications

#### 1. Settings UI for `mcp_execution_mode`
- **Summary**: `[PYPOST-1439] Expose MCP execution mode in Settings dialog`
- **Description**: Host constructors already pass
  `execution_mode=settings.mcp_execution_mode` into `MCPServerRegistry`
  (`mcp_server_controller`, `daemon_runtime`). Add a Settings dialog control
  (`thread` | `process`), document apply-on-next-start (or require stop-all), and cover with a
  UI wiring test so operators can opt into isolation without editing config by hand (NFR3 UX).
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Medium
- **Labels**: `["tech-debt", "mcp", "ui", "settings"]`
- **Story Points**: 2
- **Jira**: UNTICKETED

#### 2. Process-mode reconfigure with supervised candidate + rollback
- **Summary**: `[PYPOST-1439] Process-mode MCP reconfigure (candidate child + commit)`
- **Description**: Today `reconfigure` always uses `MCPServerManager` candidates. Implement
  process-mode parity: spawn a candidate supervised worker, keep neighbors serving, commit or
  roll back without leaving orphan PIDs, and add acceptance tests for same-endpoint and
  port-change paths (architecture deferred item).
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: High
- **Labels**: `["tech-debt", "mcp", "lifecycle"]`
- **Story Points**: 5
- **Jira**: UNTICKETED

#### 3. Proxy MCP servers in process-mode workers
- **Summary**: `[PYPOST-1439] Process-mode proxy MCP server parity`
- **Description**: Extend START IPC and `mcp_worker_process` to construct `MCPProxyServerImpl`
  from upstream URL/transport/headers/timeout. Keep thread-mode proxy behavior unchanged. Add
  process-mode proxy smoke / isolation coverage (architecture Q&A debt).
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: High
- **Labels**: `["tech-debt", "mcp", "proxy"]`
- **Story Points**: 5
- **Jira**: UNTICKETED

#### 4. Process-mode tool refresh / `UPDATE_TOOLS`
- **Summary**: `[PYPOST-1439] Hot tool refresh for process-mode MCP workers`
- **Description**: `refresh_collection` only updates `_managers`. Add IPC `UPDATE_TOOLS` (or
  bounded worker restart) on `ProcessServerRunner`, wire registry refresh paths, and test that
  collection edits reach process-mode servers without host restart.
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Medium
- **Labels**: `["tech-debt", "mcp", "ipc"]`
- **Story Points**: 3
- **Jira**: UNTICKETED

#### 5. Auto-restart with exponential backoff
- **Summary**: `[PYPOST-1439] Optional MCP worker auto-restart with backoff`
- **Description**: Evaluation § lifecycle lists configurable auto-restart. Implement opt-in
  policy (max attempts, exponential backoff, reset on healthy window), emit structured logs /
  status transitions, and avoid tight crash loops. Default remains detect + `failed` (current
  DoD).
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Medium
- **Labels**: `["tech-debt", "mcp", "supervisor"]`
- **Story Points**: 5
- **Jira**: UNTICKETED

#### 6. IPC protocol version negotiation
- **Summary**: `[PYPOST-1439] Enforce MCP worker IPC message version`
- **Description**: `MSG_V = 1` is written but never checked. Validate `v` on receive in
  supervisor and worker; reject/log incompatible envelopes; document upgrade rules for future
  opcodes (e.g. `UPDATE_TOOLS`, proxy START fields).
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Low
- **Labels**: `["tech-debt", "mcp", "ipc"]`
- **Story Points**: 2
- **Jira**: UNTICKETED

#### 7. Active HEARTBEAT watchdog
- **Summary**: `[PYPOST-1439] MCP supervisor HEARTBEAT liveness watchdog`
- **Description**: Worker already handles HEARTBEAT/PONG. Have the supervisor periodically ping
  running children and mark `failed` (and escalate stop) when pongs miss, covering hung-but-alive
  workers that `is_alive()` alone cannot detect.
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Low
- **Labels**: `["tech-debt", "mcp", "supervisor"]`
- **Story Points**: 2
- **Jira**: UNTICKETED

#### 8. Per-worker memory ceilings / spawn admission
- **Summary**: `[PYPOST-1439] MCP process-mode memory ceilings and admission control`
- **Description**: Operators accept higher memory for isolation, but dense desks can OOM the
  host. Add optional soft/hard RSS guidance or spawn admission (max concurrent process workers /
  estimated budget), surface clear operator errors when refused, and document expected per-child
  footprint in `doc/dev/`.
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Medium
- **Labels**: `["tech-debt", "mcp", "performance"]`
- **Story Points**: 5
- **Jira**: UNTICKETED

#### 9. Process-mode 10x stress parity and Windows stop CI
- **Summary**: `[PYPOST-1439] Process-mode 10x stress + Windows stop escalation CI`
- **Description**: Extend or mirror `test_mcp_multiserver_stress_10x` under
  `mcp_execution_mode=process` (barrier start, RST, teardown/rebind). Add Windows CI coverage for
  terminate/kill escalation so NFR4 stop behavior is proven beyond POSIX.
- **Classification**: NON-BLOCKER
- **Issue Type**: Debt
- **Priority**: Low
- **Labels**: `["tech-debt", "mcp", "testing"]`
- **Story Points**: 3
- **Jira**: UNTICKETED

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| **Pytest Timeouts** | Explicit timeout marker | PASS | Isolation repro module + per-test timeouts |
| **Acceptance path** | Crash / vars / bounded stop | PASS | `tests/test_mcp_process_isolation_repro.py` |
| **Thread regression** | NFR5 lightweight mode | PASS | Thread control + 10x stress still green (Step 4) |
| **Architecture debt called out** | Auto-restart, reconfigure, proxy, IPC v, memory | PASS | Documented as NON-BLOCKER follow-ups |
| **FR1 durable setting → registry** | Persisted mode applied at construction | PASS | Wired in controller + daemon; covered by wiring tests (was review FAIL) |
| **FR1 Settings UI** | Operator-selectable control | GAP → TD-1 | NON-BLOCKER; config/persist path works without dialog |
| **Unticketed Debt** | Follow-ups documented | PASS | TD-1…TD-9 UNTICKETED with Fibonacci SP |

**Zero BLOCKERs** after FR1 host-wiring fix. Safe to proceed to Step 8 (Dev Docs) after
acceptance gate on this artifact.

**SAFE TO PROCEED TO REVIEW**
