# Roadmap: PYPOST-1208

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1208/00-roadmap.md` created from template
  - [x] `ai-tasks/PYPOST-1208/10-requirements.md` drafted
  - [x] Implementation language recorded: Python
  - [x] Business goal stated (prove attach with tests as feasible; document gaps; docs/tests agree)
  - [x] Scope / non-goals aligned with Jira + ATTACH-2 residual matrix
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1208/20-architecture.md` drafted
  - [x] Verification-surface architecture (no attach rewrite); residual matrix feasibility mapped
  - [x] Failing-repro plan: red sentinels in `tests/test_agent_ui_attach.py` for residual rows (not N/A)
  - [x] Docs/tests agreement via proven vs manual table in `doc/dev/agent_ui_actions_mcp.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Red sentinels in `tests/test_agent_ui_attach.py` (catalog fill/select/send_key; host-stop unbind; sidecar-exit host listens; endpoint override)
- [x] **STEP 4: Development**
  - [x] Replaced six Step 3 sentinels in `tests/test_agent_ui_attach.py` with
    host+client / CLI proofs (fill, select, send_key, host.stop unbind,
    abrupt sidecar-exit rebind, endpoint env/CLI)
  - [x] Documented manual gaps + proven-vs-manual table in
    `doc/dev/agent_ui_actions_mcp.md` (protocol reject → PYPOST-1218;
    concurrent / stale-socket races)
  - [x] `make test PYTEST_ARGS='tests/test_agent_ui_attach.py -v'` — all green
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1208/40-code-cleanup.md` created
  - [x] `make lint` clean; scoped attach tests green
  - [x] Doc line-length cleanup in `doc/dev/agent_ui_actions_mcp.md`
  - [x] Timeout markers retained (`pytestmark` timeout 30)
  - [x] `make typecheck` baseline drift noted out-of-scope
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1208/50-observability.md` created
  - [x] New attach instrumentation: N/A (landed in PYPOST-1207)
  - [x] Catalog cross-check vs `doc/dev/logging.md` + PYPOST-1207/50-observability.md
  - [x] Verification notes: CI suite exercises attach paths; no new metrics
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1208/60-tech-debt.md` created
  - No blockers; PYPOST-1218 not duplicated; concurrent/stale accepted residual
  - Unticketed new debt: none (Phase D has nothing to open from this story)
- [x] **STEP 8: Dev Docs**
  - [x] Confirmed/refined Proven vs manual in
    `doc/dev/agent_ui_actions_mcp.md` (proof-scope notes; eleven-test
    agreement; no new capability)
  - [x] Cross-links: `doc/dev/README.md`, `testing.md`, `ui_actions.md`,
    `agent_lifecycle.md` → Proven vs manual (ATTACH-3 / PYPOST-1208)
  - [x] `ai-tasks/PYPOST-1208/70-dev-docs.md` task-local summary
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1208/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1208/20-architecture.md`

### STEP 3: Failing Repro

- Red sentinels in `tests/test_agent_ui_attach.py`:
  - `test_attach_host_client_ui_fill_sets_line_edit`
  - `test_attach_host_client_ui_select_sets_combo`
  - `test_attach_host_client_ui_send_key_changes_text`
  - `test_attach_host_stop_unbinds_client`
  - `test_attach_sidecar_exit_leaves_host_listening`
  - `test_attach_endpoint_override_env_and_cli`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1208/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1208/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1208/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_ui_actions_mcp.md` (Proven vs manual refined)
- `doc/dev/README.md`, `doc/dev/testing.md`, `doc/dev/ui_actions.md`,
  `doc/dev/agent_lifecycle.md` (discoverability cross-links)
- `ai-tasks/PYPOST-1208/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
