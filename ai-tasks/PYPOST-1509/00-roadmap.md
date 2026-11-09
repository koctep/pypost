# Roadmap: PYPOST-1509

## Task Metadata

- **Task**: PYPOST-1509: Fix pre-existing registry test line-length lint failure
- **Story Points**: 1.0 SP
- **Implementation language**: Python
- **Base commit**: `33d5cb1a`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Documented business goal: restore a clean `make lint` gate for the
    registry test module without changing test behavior
  - [x] `ai-tasks/PYPOST-1509/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Confirmed comment-only wrap in `tests/test_mcp_server_registry.py`
  - [x] Failing-repro plan: `make lint` / `lint-tests` E501 at line 308
  - [x] `ai-tasks/PYPOST-1509/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Red repro: `make lint` at base `33d5cb1a` fails with
    `tests/test_mcp_server_registry.py:308:101: E501 line too long
    (111 > 100 characters)` (no pytest node id; lint gate is the acceptance
    check)
  - [x] Evidence: `/tmp/PYPOST-1509-lint-red.txt` (worktree at `33d5cb1a`)
  - [x] Note: current HEAD already wraps the comment; Step 3 documents the
    historical red gate rather than introducing a new pytest case
- [x] **STEP 4: Development**
  - [x] Confirmed wrap of the overlong comment at
    `tests/test_mcp_server_registry.py:308-309` (present on tree vs base
    `33d5cb1a`; no behavior change)
  - [x] Verified `make lint` green on working tree
    (`Test lint OK (408 accepted legacy occurrences)`)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1509/40-code-cleanup.md`
  - [x] Re-ran `make lint` after verification; line lengths ≤ 100 on the
    wrapped comment
- [x] **STEP 6: Observability**
  - [x] N/A — comment-only formatting; no runtime logging/metrics changes
  - [x] `ai-tasks/PYPOST-1509/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1509/60-tech-debt.md`
  - [x] No new follow-up debt from this formatting fix
- [x] **STEP 8: Dev Docs**
  - [x] Documented the registry E501 fix under `doc/dev/testing.md`
  - [x] Linked from task artifacts
- [x] **COMMIT: Commit Changes**
  - [ ] Not performed (execution agent instructed not to commit)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1509/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1509/20-architecture.md`

### STEP 3: Failing Repro

- Focused lint red repro via `make lint` (E501 at
  `tests/test_mcp_server_registry.py:308`); no new pytest module

### STEP 4: Development

- Comment wrap in `tests/test_mcp_server_registry.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1509/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1509/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1509/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (PYPOST-1509 subsection)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
