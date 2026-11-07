# Roadmap: PYPOST-1463

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business purpose established by approved sprint goal and PYPOST-1439 follow-up context.
  - Requirements describe live configuration changes, recovery, and peer continuity.
- [x] **STEP 2: High-Level Architecture Design**
  - Process candidate transaction, worker identity routing, and rollback design documented.
  - Step 3 will exercise process reconfiguration before production changes.
- [x] **STEP 3: Failing Repro Test**
  - Red test path: `tests/test_mcp_process_reconfigure_repro.py`.
  - Added `tests/test_mcp_process_reconfigure_repro.py` (eight acceptance cases).
  - Real target and peer workers serve tools before each attempted replacement.
  - Same/new endpoint success, before/after-bind rejection, failed restore, concurrent stop.
  - `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_reconfigure_repro.py -q'`
    reports eight intended red failures: `_managers[instance_id]` raises `KeyError`.
  - No production changes; endpoint-rebind fixture cleanup succeeds after every case.
- [x] **STEP 4: Development**
  - [x] Added copied runner recovery snapshots and worker identity; retain failed-stop ownership.
  - [x] Serialized process handover with stop, bounded rollback, and generation-aware exit routing.
  - [x] Eight repro cases green; process isolation and thread registry suites also passed.
  - [x] Added stale retired-worker callback assertion and serialized process start/stop callbacks.
  - [x] Review fix: serialize validation and stopped-row decisions for concurrent process edits.
  - [x] Review fix: preserve state on clear/restore if cleanup remains; retry cleanup-only IDs.
  - Added bounded concurrent-edit, clear/restore retry, and cleanup-only stop regressions.
  - Expanded 12-case process reconfiguration suite passes after both review corrections.
  - `make typecheck` passed the existing 175-error baseline gate.
  - `make -o lint-tests lint` passed production and documentation checks.
  - `make lint` reproduces base `33d5cb1a` E501 at `tests/test_mcp_server_registry.py:308`.
  - Baseline lint evidence: `/tmp/PYPOST-1463-step4-baseline-lint.log`; Jira filing by orchestrator.
- [x] **STEP 5: Code Cleanup**
  - Reviewed formatting, imports, dead code, timeout marks, and implementation artifacts.
  - Production/docs lint and typecheck baseline pass; known test lint debt is PYPOST-1509.
  - Cleanup report: `ai-tasks/PYPOST-1463/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Retained safe structured transaction logs and existing aggregate status-count metrics.
  - Added commit/rejection caplog contracts and secret-bearing exception exclusion assertion.
  - Observability report: `ai-tasks/PYPOST-1463/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Reviewed process ownership, rollback snapshots, lifecycle serialization, and test coverage.
  - No new blocker found; baseline test lint remains linked as PYPOST-1509.
  - Technical debt report: `ai-tasks/PYPOST-1463/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - Documented process candidate handover, rollback snapshots, cleanup retries, and diagnostics.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1463/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1463/20-architecture.md`

### STEP 3: Failing Repro

- Automated red acceptance checks exercise real local process workers.
- `tests/test_mcp_process_reconfigure_repro.py`
- Red output recorded at `/tmp/PYPOST-1463-step3-red.log` for independent review.

### STEP 4: Development

- `pypost/core/mcp_server_registry.py`
- `pypost/core/mcp_server_runner.py`
- `pypost/core/mcp_process_supervisor.py`
- `tests/test_mcp_process_reconfigure_repro.py` (12 green acceptance cases)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1463/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1463/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1463/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_process_isolation.md`

### COMMIT

- No artifact beyond the acceptance mark; report branch and commit hash in chat only.
