# Roadmap: PYPOST-992

## Task Metadata

- **Implementation language**: Python
- **Task kind**: Agent-UI MCP integration-test coverage

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements are recorded in `10-requirements.md` from the Jira TD-3
    description and acceptance criteria.
  - The delegated worker service was unavailable; the orchestrator completed
    the local fallback and recorded the limitation.
- [x] **STEP 2: High-Level Architecture Design**
  - The subprocess/client/widget coverage boundary is recorded in
    `20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - Added the process-level stdio click/fill test before final verification.
  - The first exploratory plus-tab click was rejected as an offscreen-menu
    harness hang; the test now uses the stable editable URL fixture widget.
- [x] **STEP 4: Development**
  - Extended `tests/test_agent_ui_actions_mcp.py` with bounded stdio
    `call_tool` coverage for real `ui_fill` and `ui_click` actions.
  - No production source change was required.
- [x] **STEP 5: Code Cleanup**
  - Cleanup review is recorded in `40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Test diagnostics and payload logging boundaries are recorded in
    `50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Retained test-harness limitations are recorded in `60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - The sidecar developer guide's test section documents the click/fill smoke.
- [x] **COMMIT: Commit Changes**
  - Commit `07770480` contains the PYPOST-992 stdio integration coverage and
    its task artifacts.
  - Focused agent-UI Make tests, lint, typecheck, and verification pass.

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
- `tests/test_agent_ui_actions_mcp.py`
