# Roadmap: PYPOST-1354

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`; review PASS.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md`; review PASS.
  - Review correction: canonical presenter ownership, persistence acknowledgment, and failure
    cleanup are explicit; missing callbacks cannot create selectable environments.
  - Review correction: persisted paired-path provenance replaces name-prefix inference;
    rename/reload and unrelated-name tests are specified.
  - Current primary Qt/Pydantic references and pattern justifications added; review PASS.
- [x] **STEP 3: Failing Repro Test**
  - Red repro: `tests/test_mcp_builtin_paired_env.py` (18 parametrized cases).
  - Covers immutable sanitized derivation, collision safety, exact persisted provenance,
    optional manual selection, missing owner, delayed completion, rejection/failure/retry,
    source changes, editor close, canonical ownership/wiring, and staged encrypted updates.
  - Command: `make test PYTEST_ARGS='tests/test_mcp_builtin_paired_env.py'`.
  - Result: 18 failed, Make exit 2 (expected red); no collection or fixture errors.
    Missing derivation and presenter APIs/copy action, unsupported editor callback, and
    provenance discarded on save/reload demonstrate the missing acceptance behavior.
  - Controlled encrypted storage tests use the real gateway and bounded worker gates;
    delayed success preserves queued updates, failure removes staged copies before dispatch.
    These assertions will execute after the missing creation API is implemented.
  - Production files unchanged. Independent Step 3 review pending; execution leaves `[/]`.
- [x] **STEP 4: Development**
  - [x] Iteration 1: optional persisted provenance and independent sanitized derivation.
    `make test PYTEST_ARGS='tests/test_mcp_builtin_paired_env.py -k "derivation or
    origin_roundtrips"'` passed (2 cases).
  - [x] Iteration 2: canonical staged creation with negative-token acknowledgment and queued
    failure cleanup preserving request-update dispositions. Targeted persistence tests passed.
  - [x] Iteration 3: typed creation callback injected and forwarded through both MCP UI layers.
    Targeted presenter persistence/wiring test passed.
  - [x] Iteration 4: copy button, exact provenance highlight, durable completion refresh,
    retryable failure state, and guarded late callbacks for changed/closed editors.
    `make test PYTEST_ARGS='tests/test_mcp_builtin_paired_env.py'` passed all 18 repro cases.
  - [x] Relevant regression run passed all nine modules: Built-in collections/dialog/lifecycle,
    environment presenter/gateway/worker, MCP controls/dialog, and presenter controller seam.
  - [x] Iteration 5: extracted staged creation into a cohesive presenter helper to retain
    existing file-size regression caps without changing guard policy.
  - [x] Required `make check` completed: 389 files, 368 passed, 14 failed, 7 skipped.
    Initial task-caused presenter size-cap failure was fixed by Iteration 5; the focused
    audit CLI now passes. No guard caps or tests were weakened.
  - [x] Snapshot failures reproduced at the base commit and are tracked in
    [PYPOST-1361](https://pypost.atlassian.net/browse/PYPOST-1361). This covers dialog audit discovery
    drift (recorded 1,031 versus base 1,112 lines) and the stale SOLID metrics snapshot.
  - [x] Registry bind-failure teardown race reproduced at base and passed on isolated current
    retry; tracked in [PYPOST-1362](https://pypost.atlassian.net/browse/PYPOST-1362).
  - [x] Full-suite Makefile fixture timeouts occur in shared-prewarm pip/flock setup and match
    existing [PYPOST-1298](https://pypost.atlassian.net/browse/PYPOST-1298); exit-policy worker timeout
    matches [PYPOST-1299](https://pypost.atlassian.net/browse/PYPOST-1299).
    One bounded current retry completed: nine modules, two passed and seven failed/timed out.
    Recipes and markers passed unchanged after their full-suite failures, supporting the
    existing flaky infrastructure classification. No further retry or scope expansion.
  - [x] Final focused run passed all 11 modules (including the 18-case repro and audit cap
    CLI); `make lint` and `make verify-ai-tasks` passed. Root virtual environment was restored
    through `make install` after an invalid baseline VENV override propagated into nested
    fixture Make commands; the contaminated fixture baseline results were discarded.
- [x] **STEP 5: Code Cleanup**
  - [x] Cleanup report: `40-code-cleanup.md`; task-added imports grouped by dependency layer.
  - [x] `make lint` passed; `make typecheck` passed with 181 known baseline errors and no additions.
    Existing focused validation is retained for import-only edits; baseline tickets are linked.
  - [x] Clean temporary baseline checkout removed with non-forced `git worktree remove`.
    `make verify-ai-tasks` passed.
- [x] **STEP 6: Observability**
  - [x] Added structured derivation/admission/rejection/durable outcome events and fixed UI
    exception reason codes; no variable values, display names, or raw exceptions in new logs.
  - [x] Strengthened existing caplog assertions for rejection, failed persistence/retry, and
    diagnostic privacy. All 18 repro cases plus presenter/gateway regressions passed.
  - [x] `make lint` passed; `50-observability.md` documents event context and the rationale
    for retaining existing storage/lifecycle metrics without adding a new schema.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `60-tech-debt.md` records reviewed design tradeoffs, coverage boundaries, and inherited
    baseline failures with exact node IDs and existing Jira links; no new implementation debt
    or proven unmet acceptance criterion identified. New tests remain bounded and timed.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/predefined_collection_library.md` with the implemented paired-copy
    overview, owner/API contract, durable acknowledgment, provenance/encryption, troubleshooting,
    diagnostics, and Make validation; implementation status and prior future wording corrected.
  - [x] `make lint-docs`, `make check-docs-links`, and `make verify-ai-tasks` passed.
    Existing documentation targets cover user/README files; developer additions and referenced
    local files were reviewed directly. User documentation is reserved for PYPOST-1356.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1354/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1354/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1354/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1354/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1354/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
