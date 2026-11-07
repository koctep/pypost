# Roadmap: PYPOST-1464

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business purpose established by approved isolated proxy parity sprint scope.
  - Requirements cover forwarding, saved settings, secret safety, lifecycle, and compatibility.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture carries existing proxy settings through copied START data to the child.
  - Focused red plan covers local upstream forwarding, settings, and lifecycle compatibility.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_process_proxy_repro.py`: real proxy forwarding and START settings.
  - Four intended red cases: local child returns no upstream tools; START lacks proxy selection.
  - Direct upstream discovery and calls pass; owned worker ports release after each case.
  - Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_proxy_repro.py -q'`.
  - Evidence: `/tmp/PYPOST-1464-step3-red.log` (4 failures, 3.83 seconds).
- [x] **STEP 4: Development**
  - [x] Forwarded copied proxy settings through runner and supervisor START data.
  - [x] Child selects the existing proxy engine with its owned variable/key suppliers.
  - [x] Four reviewed red cases now pass (5.70 seconds); local behavior remains separate.
- [x] **STEP 5: Code Cleanup**
  - Sorted worker imports, verified PEP 8 formatting (<= 100 chars), timeout markers, and no dead code.
  - `make -o lint-tests lint`, `make typecheck`, and `tests/test_mcp_process_proxy_repro.py` pass; known `lint-tests` E501 is PYPOST-1509.
  - Cleanup report: `ai-tasks/PYPOST-1464/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Verified secret-safe structured lifecycle logging across runner, supervisor, registry, and worker proxy paths (`START` payloads, upstream URLs, header values, and variable snapshots are never logged).
  - Added `caplog` verification in `tests/test_mcp_process_proxy_repro.py` for `mcp_worker_spawned`, `mcp_worker_started`, `mcp_registry_process_reconfigured`, and absence of upstream URLs and secret token values.
  - Observability report: `ai-tasks/PYPOST-1464/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Reviewed `pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_runner.py`, `pypost/core/mcp_worker_process.py`, and `tests/test_mcp_process_proxy_repro.py` against `10-requirements.md` and `20-architecture.md`.
  - Confirmed 0 blockers, explicit `pytestmark = pytest.mark.timeout(60)` coverage, and linked existing sprint follow-ups (`PYPOST-1465`..`PYPOST-1470`, `PYPOST-1509`) without duplicates.
  - Technical debt report: `ai-tasks/PYPOST-1464/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` and `doc/dev/mcp_proxy.md` to document isolated proxy startup parity (`server_type`, `upstream_url`, `upstream_transport`, copied `headers`, and `timeout` in `START` IPC and child `MCPProxyServerImpl` selection).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1464/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1464/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_process_proxy_repro.py`
- Red output recorded at `/tmp/PYPOST-1464-step3-red.log`

### STEP 4: Development

- `pypost/core/mcp_process_supervisor.py`
- `pypost/core/mcp_server_runner.py`
- `pypost/core/mcp_worker_process.py`
- `tests/test_mcp_process_proxy_repro.py` (4 green acceptance cases)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1464/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1464/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1464/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_process_isolation.md`
- `doc/dev/mcp_proxy.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
