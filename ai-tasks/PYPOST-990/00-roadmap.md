# Roadmap: PYPOST-990

## Task Metadata

- **Implementation language**: Python
- **Task kind**: Agent-UI MCP transport and lifecycle

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements are recorded in `10-requirements.md` from the Jira
    acceptance criteria and the existing stdio/attach contracts.
  - The delegated worker service was unavailable after its 404 response;
    the orchestrator completed the local fallback and recorded the limitation.
- [x] **STEP 2: High-Level Architecture Design**
  - Optional HTTP entry, transport ownership, Qt dispatch, and shutdown are
    recorded in `20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - Added focused tests for HTTP route construction, CLI selection, and
    cross-thread `call_tool` dispatch before production changes.
- [x] **STEP 4: Development**
  - Added explicit HTTP CLI mode, shared `/mcp` route, bounded Uvicorn
    lifecycle, and Qt main-thread dispatch while preserving stdio/attach.
- [x] **STEP 5: Code Cleanup**
  - Cleanup review and focused verification are recorded in
    `40-code-cleanup.md`.
  - The independent review worker did not return within bounded waits and was
    closed; the orchestrator performed the read-only fallback review.
- [x] **STEP 6: Observability**
  - Added lifecycle logs and the event catalog in `50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - Retained trust-boundary and endpoint tradeoffs are recorded in
    `60-tech-debt.md`; no new debt ticket is needed.
- [x] **STEP 8: Dev Docs**
  - HTTP usage, trust, troubleshooting, and logs are documented in
    `70-dev-docs.md` and the linked developer guides.
- [x] **COMMIT: Commit Changes**
  - Commit `f8961e28` contains only the PYPOST-990 implementation, tests,
    documentation, and task artifacts.
  - Focused Make checks pass; the full `make check` result is 323 passed,
    5 baseline failures, and 6 skips.

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
