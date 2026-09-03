# Roadmap: PYPOST-1102

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements are documented in `10-requirements.md`.
  - Scope covers shared dispatch lifecycle behavior while preserving current
    transport, exceptions, activity, metrics, and public method behavior.
  - The delegated worker service was unavailable after two 404 retries; the
    orchestrator completed a local fallback and will record this in the final
    review notes.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture is documented in `20-architecture.md`.
  - A single async dispatch boundary owns header resolution, upstream session
    lifecycle, error mapping, timing, metrics, logs, and activity recording.
  - Public proxy method signatures, result shapes, transports, and per-request
    connection behavior remain compatible.
  - The delegated architecture worker was unavailable because the subagent
    service returned repeated 404 errors; this is a local fallback artifact.
- [x] **STEP 3: Failing Repro Test**
  - Added `tests/test_mcp_proxy_dispatch_repro.py` with red tests for shared
    delegation and consistent prompt network-error lifecycle handling.
  - The red run failed because `_dispatch_proxy_operation` was absent and
    prompt errors bypassed the existing mapping boundary.
  - The repro module declares a 60-second timeout and runs through `make test`.
- [x] **STEP 4: Development**
  - Added `_dispatch_proxy_operation` and routed all six proxy protocol methods
    through it while preserving public signatures and result normalization.
  - Centralized header resolution, upstream cleanup, error mapping, timing,
    metrics, safe activity entries, and operation completion logs.
  - Focused proxy tests and the new repro pass; lint and typecheck pass.
  - Delegated review was unavailable after repeated subagent-service 404 errors;
    local read-only review found no scope or safety issues.
- [x] **STEP 5: Code Cleanup**
  - Cleanup report is recorded in `40-code-cleanup.md`.
  - The refactor removes duplicated lifecycle branches without adding a runtime
    dependency or changing transport/session ownership.
- [x] **STEP 6: Observability**
  - Observability behavior and verification are recorded in `50-observability.md`.
  - The shared boundary records one request/response lifecycle per operation and
    preserves tool-duration metrics and sanitized activity details.
- [x] **STEP 7: Technical Debt Analysis**
  - Technical-debt analysis is recorded in `60-tech-debt.md`.
  - Existing per-request upstream handshakes remain tracked by PYPOST-1101; no
    new Jira follow-up was needed for this refactor.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_runtime_validation.md` with the proxy dispatch lifecycle
    and troubleshooting guidance.
  - The documentation remains linked and Make-verified.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted

## Artifacts

### STEP 1: Requirements

- `10-requirements.md`
