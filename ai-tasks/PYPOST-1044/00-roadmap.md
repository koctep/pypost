# Roadmap: PYPOST-1044

**Programming language:** Python

## STEP 1 Approval Record

The full-sprint workflow is running in autonomous mode.  Step 1 requirements
were independently reviewed and approved before the step was marked complete.

## STEP 2 Approval Record

The Step 2 architecture was independently reviewed. The reviewer required and
verified corrections for global port uniqueness, explicit Research/Q&A, and
persisted enabled auto-start semantics. The corrected architecture passed
review before this step was marked complete.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_server_registry.py` — red regression coverage for independent MCP server instances
- [x] **STEP 4: Development**
  - [x] Added isolated MCP server registry, per-instance environment/tool snapshots, lifecycle operations, and persisted multi-server settings.
  - [x] Wired persisted enabled-server startup and shutdown ownership, scoped collection/environment refresh, transactional reconfiguration, and MCP Servers management UI with explicit legacy conversion.
  - [x] Final independent review passed after regression coverage for transaction validation and MCP server management.
- [x] **STEP 5: Code Cleanup**
  - [x] Registry reference reconciliation, transactional replacement rollback, and delayed settings persistence were independently reviewed and approved.
- [x] **STEP 6: Observability**
  - [x] Added privacy-safe aggregate lifecycle metrics and structured server lifecycle logs.
  - [x] Independent review fixed and verified the bind-failure status/metric race.
- [x] **STEP 7: Review and Technical Debt**
  - [x] Independent review passed after correcting the aggregate MCP status and scoping the tools overview to the selected server.
- [x] **STEP 8: Dev Docs**
  - [x] Documented persisted multi-endpoint registry lifecycle, configuration,
    isolation, migration, operator telemetry, UI actions, and troubleshooting.
  - [x] Reconciled developer, user, example, trust-model, testing, and metric
    documentation with endpoint-selected collection/environment semantics.
  - [x] Final independent documentation review passed after all findings were
    corrected.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1044/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1044/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1044/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1044/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1044/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_server_registry.md` and related developer, operator, user, and
  example documentation updates
- `ai-tasks/PYPOST-1044/70-dev-docs.md`
