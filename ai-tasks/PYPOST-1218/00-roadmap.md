# Roadmap: PYPOST-1218

## Task Metadata

- **Implementation language**: Python
- **Task kind**: Agent-UI attach protocol hardening

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements are recorded in `10-requirements.md` from the Jira
    description and PYPOST-1207 technical-debt source.
  - The delegated worker service was unavailable; the orchestrator completed
    the local fallback and recorded the limitation.
- [x] **STEP 2: High-Level Architecture Design**
  - Handshake validation and fail-closed client behavior are recorded in
    `20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - Added a focused mismatch-handshake test before production validation.
- [x] **STEP 4: Development**
  - `AgentUiAttachHost` now requires exact `ATTACH_PROTOCOL_VERSION` and
    returns a rejected handshake for unsupported or missing versions.
- [x] **STEP 5: Code Cleanup**
  - Cleanup review is recorded in `40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Rejected-handshake logging is recorded in `50-observability.md` and the
    logging catalog.
- [x] **STEP 7: Technical Debt Analysis**
  - Retained protocol-version limitations are recorded in `60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - The attach verification matrix and manual residual section are updated in
    `agent_ui_actions_mcp.md`.
- [x] **COMMIT: Commit Changes**
  - Commit `2e0729c5` contains the handshake validation, focused test,
    documentation, and task artifacts.
  - Focused attach/sidecar Make tests, lint, typecheck, and verification pass.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted

## Artifacts

- `10-requirements.md`
- `20-architecture.md`
- `40-code-cleanup.md`
- `50-observability.md`
- `60-tech-debt.md`
- `70-dev-docs.md`
- `pypost/agent/attach_ipc.py`
- `tests/test_agent_ui_attach.py`
