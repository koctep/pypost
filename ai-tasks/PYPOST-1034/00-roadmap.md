# Roadmap: PYPOST-1034

**Programming language:** Python

## STEP 1 Approval Record

The applicable `sprint-runner` workflow explicitly runs its phases in
autonomous mode and preauthorizes proceeding without a separate confirmation
between phases. That explicit autonomous preapproval is the required approval
basis before marking STEP 1 complete.

## STEP 2 Approval Record

The autonomous `sprint-runner` approval basis authorizes continuation without a
separate user gate. An independent architecture review completed with PASS and
no findings before STEP 2 was marked complete.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_server_integration.py` — PYPOST-1034 query/body MCP request
    substitution regression coverage; independently verified against local loopback.
  - [x] N/A — this is test-only coverage for behavior already corrected by PYPOST-1033.
    The two regression tests are intentionally green on the current branch and fail if
    the MCP argument merge, query/body rendering, or safe dotted-path support regresses;
    no artificial production rollback is appropriate to force a red phase.
- [x] **STEP 4: Development**
  - [x] Added fixture-backed, loopback MCP integration coverage for the existing
    Jira query and JSON-body request shapes; each scenario verifies the normal
    client-visible 200 result and the rendered outbound wire data.
  - [x] Independently reviewed with no findings; the focused loopback tests and
    the related MCP/fixture modules pass.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1034/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1034/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1034/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1034/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1034/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md` — MCP query/body argument substitution contract and focused regression command
- `doc/dev/testing.md` — integration-test boundary and focused regression command
- `doc/dev/README.md` — MCP documentation index entry
- `ai-tasks/PYPOST-1034/70-dev-docs.md`
