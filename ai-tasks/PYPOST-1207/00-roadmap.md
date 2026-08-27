# Roadmap: PYPOST-1207

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1207/10-requirements.md`
  - Soft contract from PYPOST-1206 (`doc/dev/agent_ui_actions_mcp.md`)
  - Prior decompose: `ai-tasks/PYPOST-1202/` (ATTACH-2)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1207/20-architecture.md`
  - Decision: cooperative local IPC host in desktop + attach-mode
    sidecar; spawn-session default preserved; UI tools stay off
    product MCP
  - Failing-repro plan: `tests/test_agent_ui_attach.py` (CLI `--attach`,
    no spawn on attach, attach-fail without host)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_ui_attach.py`
    (`test_cli_accepts_attach_mode`,
    `test_attach_mode_does_not_call_agent_app_session_start`,
    `test_attach_without_host_fails_unbound_not_silent_spawn`)
- [x] **STEP 4: Development**
  - [x] Iter 1: `--attach` / `--attach-endpoint` CLI; attach path skips
    `AgentAppSession.start`; unbound → nonzero exit (`ui_actions_mcp.py`)
  - [x] Iter 2: `UiDriveSession` + `MainWindowUiDrive`
    (`pypost/agent/ui_drive.py`); AF_UNIX host/client
    (`pypost/agent/attach_ipc.py`); same `ui_*` catalog via duck typing
  - [x] Iter 3: Interactive `main.py` starts/stops `AgentUiAttachHost`
    around `app.exec()`; detach/rebind lifecycle covered by tests
  - [x] Iter 4: Capability note + config in `doc/dev/agent_ui_actions_mcp.md`
    (and lifecycle cross-link); attach + spawn MCP tests green
  - First priority green: `tests/test_agent_ui_attach.py` (CLI + host
    round-trip + detach)
  - Spawn regression: `tests/test_agent_ui_actions_mcp.py` still passes
  - UI tools remain off product MCP (existing packaging gates unchanged)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1207/40-code-cleanup.md`
  - `make lint` PASS; `make typecheck` FAIL (out-of-scope baseline drift)
  - Attach tests green; timeout markers present
  - Minor cleanup: `attach_ipc.py` typing; doc line wraps
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1207/50-observability.md`
  - Host/client lifecycle logs in `attach_ipc.py` (start/stop, bind fail,
    accept/close, handshake, detach, UI dispatch/fail/timeout)
  - Sidecar attach path logs in `ui_actions_mcp.py` (starting/ready/failed/ended)
  - Composition-root host start/stop logs in `main.py`
  - Prometheus metrics N/A (PYPOST-952 agent-UI policy)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1207/60-tech-debt.md`
  - Fuller attach matrix → PYPOST-1208; mypy baseline drift out of scope
  - No Phase D Jira creates in this step (unticketed items left without links)
- [x] **STEP 8: Dev Docs**
  - Refined `doc/dev/agent_ui_actions_mcp.md` — AF_UNIX host, CLI,
    lifecycle mechanism, attach API, observability
  - Refined `doc/dev/agent_lifecycle.md` — attach composition-root /
    AF_UNIX notes; dependency rule for `main` vs UI
  - Cataloged attach log events in `doc/dev/logging.md`
  - Cross-links: `doc/dev/README.md`, `doc/dev/ui_actions.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1207/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1207/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_ui_attach.py` (was red; now green under Step 4)

### STEP 4: Development

- `pypost/agent/ui_drive.py` — `UiDriveSession` protocol + `MainWindowUiDrive`
- `pypost/agent/attach_ipc.py` — AF_UNIX attach host + client
- `pypost/agent/ui_actions_mcp.py` — spawn vs `--attach` entry
- `pypost/main.py` — composition-root attach host start/stop
- `tests/test_agent_ui_attach.py` — CLI + IPC round-trip + detach
- `doc/dev/agent_ui_actions_mcp.md` / `doc/dev/agent_lifecycle.md` — shipped
  attach capability notes

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1207/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1207/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1207/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_ui_actions_mcp.md` — attach architecture, CLI, API, lifecycle
- `doc/dev/agent_lifecycle.md` — attach bind/unbind mechanism
- `doc/dev/logging.md` — attach IPC event catalog
- `doc/dev/README.md` / `doc/dev/ui_actions.md` — index and cross-links

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.
