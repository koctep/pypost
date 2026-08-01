# Roadmap: PYPOST-1016

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change
  - Rationale: Architecture and requirements are process/docs sync only
    (tech-debt → Jira link-backs, optional consolidate, scoped commit); no
    app runtime, API, or product acceptance behavior to assert with a red
    pytest. Review confirmed N/A; no red product test required or written.
  - Step 4 verification (not a product test): scan `60-tech-debt.md` for
    unticketed actionable items; confirm audit keys 799–803 linked in
    sources; regenerate consolidate if links changed; commit excludes
    secrets / agent config.
- [x] **STEP 4: Development**
  - [x] Verified residue Debt PYPOST-799–803 exist; browse links present in
        mapped `60-tech-debt.md` sources (75/794/747/63/68)
  - [x] Scanned all 769 `ai-tasks/*/60-tech-debt.md` for unticketed actionable
        follow-ups; classified create / skip / already-tracked
  - [x] Created Debt [PYPOST-1018](https://pypost.atlassian.net/browse/PYPOST-1018)
        and [PYPOST-1019](https://pypost.atlassian.net/browse/PYPOST-1019)
        (PYPOST-542 TD-14/TD-15; 3 SP each) via jira-create-issue
  - [x] Link-backs: new keys in PYPOST-542; existing owners in 837/838/839/939;
        resolved note for PYPOST-551 TD-2 → PYPOST-430
  - [x] Regenerated `ai-tasks/00-tech-debt-consolidated.md`; updated
        `scripts/untracked_debt_tickets_created.json`
  - [x] Completeness: no actionable unticketed remain (intentional skips only)
  - [x] Step 4 review (sync work): PASS — residue 799–803 + 1018/1019 linked;
        consolidate idempotent; intentional skips only
  - [x] Scoped commit by orchestrator after Step 8 (excludes unrelated dirt)
- [x] **STEP 5: Code Cleanup**
  - [x] Markdown table column alignment for sync link-backs
  - [x] Regenerated consolidated inventory; validated audit JSON
  - [x] `40-code-cleanup.md` written; app linters N/A
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — sync audit trail documented; product
        OTel/logging/metrics N/A (process/docs sync only)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — process-sync trade-offs documented (manual scan,
        intentional skips, Debt without Jira Parent, commit deferred)
  - [x] User docs N/A (dev process); review PASS (subagent replaces approval)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/tech_debt_jira_sync.md` — sync overview, SoT, consolidate,
        audit JSON, re-run; points at tech-debt-jira-sync skill
  - [x] Linked from `doc/dev/README.md` and `tech_debt_inventory.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Markdown (primary — `ai-tasks/*/60-tech-debt.md` link-back updates and related
inventory artifacts; follow `.cursor/lsr/do-markdown.md`).

Python (secondary — optional regeneration of the consolidated debt inventory via the
existing consolidate tooling; follow `.cursor/lsr/do-python.md` only if that script
must change). No application feature code is in scope.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1016/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1016/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (process/docs sync; review PASS)

### STEP 4: Development

- Updated `ai-tasks/*/60-tech-debt.md` with Jira browse links for newly ticketed items
- Optional regenerated `ai-tasks/00-tech-debt-consolidated.md`
- Audit log of created Debt issues (if retained)
- Committed legitimate artifact updates (excluding local agent config / secrets)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1016/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1016/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1016/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/tech_debt_jira_sync.md`
- Index links: `doc/dev/README.md`, `doc/dev/tech_debt_inventory.md`
