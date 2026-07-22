# Roadmap: PYPOST-881

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change (YAGNI deferral; inventory evidence only)
- [x] **STEP 4: Development**
  - [x] Decision: **defer** shared finish-teardown helper extraction
  - [x] Inventory: exactly two consumers
    (`EnvironmentStorageGateway`, `CollectionStorageGateway`); no third;
    teardown sequence still symmetric (no drift)
  - [x] No production refactor
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE (YAGNI deferral with inventory evidence)
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/environment_storage_async.md` +
    `doc/dev/collection_loading.md` (keep inline finish teardown)
  - [x] Artifact: `ai-tasks/PYPOST-881/70-dev-docs.md`

## Programming Language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-881/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-881/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change (documented in roadmap + architecture)

### STEP 4: Development

- Decision + inventory only (no production extraction)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-881/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-881/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-881/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/environment_storage_async.md`
- `doc/dev/collection_loading.md`
- `ai-tasks/PYPOST-881/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-881-defer-finish-teardown-helper`

## Decision summary

**Defer extraction.** PYPOST-829 TD-1 allowed an optional shared private
finish-teardown helper only if a **third** consumer appears or drift becomes
likely. Inventory (2026-07-22) still shows exactly two gateway consumers with
symmetric capture → `deleteLater` → short `wait` → WARNING → pending-restart
ordering. Prefer honest YAGNI close over forced DRY.
