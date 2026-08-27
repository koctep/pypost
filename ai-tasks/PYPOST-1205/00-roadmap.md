# Roadmap: PYPOST-1205

## Task Metadata

- **Implementation language**: Markdown (planning artifacts) + Jira process;
  child implementation stories under PYPOST-1188 use Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1205/10-requirements.md` drafted
  - Epic PYPOST-1188 inventoried; three proposed child slices
    (REPRO-1, DIAG-1, FIX-1); no Jira children created in Step 1
  - Step 3 noted N/A for this decompose ticket (red tests belong to
    children)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1205/20-architecture.md` drafted
  - Workflow architecture only (mirror PYPOST-1204): REPRO-1 → DIAG-1
    → FIX-1 under PYPOST-1188; preferred SP 2/3/3; reject create if
    SP > 5; labels `tech-debt`, `failing-test`, `qt-uvicorn-race`
  - No Jira children created in Step 2; Step 3 N/A for this ticket
  - Traceability filled in Step 4: REPRO-1 → PYPOST-1215, DIAG-1 →
    PYPOST-1216, FIX-1 → PYPOST-1217 (was TBD until create)
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (decompose / planning only; red tests
    belong to child REPRO-1 / DIAG-1 / FIX-1 cycles)
  - Reason: PYPOST-1205 is decomposition / Jira planning only (Markdown
    artifacts + child issue creation under PYPOST-1188). Architecture
    (`20-architecture.md` § Mandatory — Failing Repro) states no product
    runtime change; no red automated test belongs on this ticket.
  - Red tests deferred to child Top-Down cycles (especially REPRO-1).
  - No test file written; no production code changed.
- [x] **STEP 4: Development**
  - [x] Child Stories already under epic PYPOST-1188 (orchestrator create;
    labels `tech-debt`, `failing-test`, `qt-uvicorn-race`; SP set on
    create)
  - [x] REPRO-1 → [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215)
    (SP 2) — Owned parallel flake evidence and baseline
  - [x] DIAG-1 → [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)
    (SP 3) — Root-cause diagnosis (race class vs alternatives)
  - [x] FIX-1 → [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)
    (SP 3) — Stabilize named node under parallel `make test`
  - [x] Fibonacci estimates matched preferred SP 2/3/3; no product code
    changed on PYPOST-1205
  - [x] Mapped provisional IDs → keys in `10-requirements.md`,
    `20-architecture.md`, and this roadmap
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1205/40-code-cleanup.md` drafted
  - DECOMPOSE only — Markdown/Jira artifacts; no product lint or
    make targets in scope
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1205/50-observability.md` drafted
  - Process observability only (worklogs + child key mapping); no
    product runtime telemetry on this ticket
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1205/60-tech-debt.md` drafted
  - Follow-ups already ticketed (PYPOST-1215 / 1216 / 1217); no
    blockers for closing PYPOST-1205; no new Phase D creates
- [x] **STEP 8: Dev Docs**
  - `ai-tasks/PYPOST-1205/70-dev-docs.md` drafted (DECOMPOSE decision)
  - Pointer-only: `doc/dev/testing.md` (named node) + `doc/dev/gui_testing.md`
    Troubleshooting → epic PYPOST-1188 children PYPOST-1215 / 1216 / 1217;
    full repro / diagnosis / fix docs deferred to children
  - No new `doc/dev/<feature>.md`; no `doc/user/`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1205/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1205/20-architecture.md`

### STEP 3: Failing Repro

- N/A — documented under Step Status (no red test; no behavioral change)
- Reason cross-ref: `20-architecture.md` § Mandatory — Failing Repro;
  red tests deferred to child REPRO-1 / DIAG-1 / FIX-1 cycles

### STEP 4: Development

- Child Stories under PYPOST-1188:
  - [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (REPRO-1, SP 2)
  - [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1, SP 3)
  - [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1, SP 3)
- Mapping recorded in `10-requirements.md` and `20-architecture.md`
- No product source/test changes on this decompose ticket

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1205/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1205/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1205/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1205/70-dev-docs.md` (DECOMPOSE decision)
- `doc/dev/testing.md` — pointer at named node paragraph
- `doc/dev/gui_testing.md` — Troubleshooting row (mirror PYPOST-1204 style)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
