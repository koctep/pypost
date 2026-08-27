# Roadmap: PYPOST-1204

## Task Metadata

- **Implementation language**: Markdown (planning artifacts) + Jira process;
  child implementation stories under PYPOST-1117 use Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1204/10-requirements.md` drafted
  - Epic PYPOST-1117 inventoried; three proposed child slices
    (REPRO-1, DIAG-1, MITIGATE-1); no Jira children created in Step 1
  - Step 3 noted N/A for this decompose ticket (red tests belong to
    children)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1204/20-architecture.md` drafted (decompose workflow;
    mirrors PYPOST-1202 / PYPOST-1203 pattern)
  - Modules: epic → decompose → requirements → architecture → Jira create
    → REPRO-1 / DIAG-1 / MITIGATE-1 + ID→key mapping
  - Child field contract: Story under PYPOST-1117; labels `tech-debt`,
    `failing-test`, `gui-batch-segfault` (not `decompose`); SP ≤5 reject
  - Dependency order: REPRO-1 → DIAG-1 → MITIGATE-1 (hard chain)
  - Step 3 N/A reiterated; create sequence deferred to Step 4; no Jira
    children created in Step 2
  - Traceability filled in Step 4: REPRO-1 → PYPOST-1212, DIAG-1 →
    PYPOST-1213, MITIGATE-1 → PYPOST-1214 (was TBD until create)
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change (decompose / planning only; red tests
    belong to child REPRO-1 / DIAG-1 / MITIGATE-1 cycles)
  - Reason: PYPOST-1204 is decomposition / Jira planning only (Markdown
    artifacts + child issue creation under PYPOST-1117). Architecture
    (`20-architecture.md` § Mandatory — Failing Repro) states no product
    runtime change; no red automated test belongs on this ticket.
  - Red tests deferred to child Top-Down cycles (especially REPRO-1).
  - No test file written; no production code changed.
- [x] **STEP 4: Development**
  - [x] Child Stories already under epic PYPOST-1117 (orchestrator create;
    labels `tech-debt`, `failing-test`, `gui-batch-segfault`; SP set on
    create)
  - [x] REPRO-1 → [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212)
    (SP 3) — Deterministic repro and evidence baseline
  - [x] DIAG-1 → [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213)
    (SP 5) — Root-cause diagnosis (lifetime vs QStyle/QPalette)
  - [x] MITIGATE-1 → [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214)
    (SP 5) — Safe mitigation and CI ownership docs
  - [x] Fibonacci estimates matched preferred SP 3/5/5; estimation
    worklogs on 1212/1213 (MITIGATE-1 estimate tokens_used 0); no product
    code changed on PYPOST-1204
  - [x] Mapped provisional IDs → keys in `10-requirements.md`,
    `20-architecture.md`, and this roadmap
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1204/40-code-cleanup.md` drafted
  - Markdown/DECOMPOSE only — no product lint/test; stale TBD / Step 3
    narrative fixed in roadmap, `10-requirements.md`, and
    `20-architecture.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1204/50-observability.md` drafted
  - Runtime telemetry N/A (decompose / Markdown + Jira only)
  - Process observability: Top-Down worklogs + REPRO-1 / DIAG-1 /
    MITIGATE-1 → PYPOST-1212 / 1213 / 1214
  - Child runtime observability deferred to those Top-Down cycles
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1204/60-tech-debt.md` drafted
  - Verdict: no blockers for closing PYPOST-1204
  - Follow-ups already ticketed: PYPOST-1212 / 1213 / 1214 (browse links in
    artifact); process residuals NON-BLOCKER with no new ticket
- [x] **STEP 8: Dev Docs**
  - `ai-tasks/PYPOST-1204/70-dev-docs.md` drafted (DECOMPOSE decision)
  - Pointer-only: `doc/dev/gui_testing.md` Troubleshooting → epic
    PYPOST-1117 children PYPOST-1212 / 1213 / 1214; full repro /
    diagnosis / mitigation+CI docs deferred to children
  - No new `doc/dev/<feature>.md`; no `doc/user/`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1204/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1204/20-architecture.md`

### STEP 3: Failing Repro

- N/A — documented under Step Status (no red test; no behavioral change)
- Reason cross-ref: `20-architecture.md` § Mandatory — Failing Repro;
  red tests deferred to child REPRO-1 / DIAG-1 / MITIGATE-1 cycles

### STEP 4: Development

- Child Stories under PYPOST-1117:
  - [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) (REPRO-1, SP 3)
  - [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) (DIAG-1, SP 5)
  - [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) (MITIGATE-1, SP 5)
- Mapping recorded in `10-requirements.md` and `20-architecture.md`
- No product source/test changes on this decompose ticket

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1204/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1204/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1204/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1204/70-dev-docs.md` (decision note; gate pending)
- `doc/dev/gui_testing.md` (pointer-only to REPRO / DIAG / MITIGATE children)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.
