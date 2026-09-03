# Roadmap: PYPOST-1105

## Task Metadata

- **Implementation language**: Python
- **Task kind**: Integration-test coverage

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements are documented in `10-requirements.md`.
  - The delegated worker service was unavailable after two 404 retries; the
    orchestrator completed a local fallback and recorded the limitation.
- [x] **STEP 2: High-Level Architecture Design**
  - The process topology and bounded lifecycle are documented in
    `20-architecture.md`.
  - The proxy is tested as a separate process from a separate upstream process.
- [x] **STEP 3: Failing Repro Test**
  - Added `tests/test_mcp_proxy_live_integration.py` with two slow-marked
    process-based wire tests.
  - This test-only debt task had no missing production behavior to reproduce;
    the new tests were green against the current implementation.
- [x] **STEP 4: Development**
  - Added separate spawned Uvicorn upstream and proxy harnesses with bounded
    startup, client, and teardown behavior.
  - Added large Streamable HTTP and real legacy SSE round-trip assertions.
  - No production source changes were required.
- [x] **STEP 5: Code Cleanup**
  - Cleanup report is recorded in `40-code-cleanup.md`.
  - The harness is self-contained, typed, and leaves no child process behind.
- [x] **STEP 6: Observability**
  - Test observability and failure diagnostics are recorded in
    `50-observability.md`.
  - Child lifecycle failures surface as bounded test failures; no payload
    logging or secret data was added.
- [x] **STEP 7: Technical Debt Analysis**
  - Analysis is recorded in `60-tech-debt.md`.
  - No new product debt was introduced; existing transport pooling remains
    PYPOST-1101 scope.
- [x] **STEP 8: Dev Docs**
  - Added the live wire-test workflow to `doc/dev/mcp_runtime_validation.md`.
  - The guide records the explicit slow-marker invocation.
- [x] **COMMIT: Commit Changes**
  - Focused slow wire tests passed (2/2), and fast lint/typecheck/verification
    passed.
  - Full `make check` reached 323 passed, 5 failed, and 6 skipped; failures are
    unrelated pre-existing parser/template/SOLID/Qt baseline behavior.

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
- `tests/test_mcp_proxy_live_integration.py`
