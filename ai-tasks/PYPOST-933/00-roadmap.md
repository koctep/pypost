# Roadmap: PYPOST-933

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_recapture_doc.py`
    (doc lock; red then green)
- [x] **STEP 4: Development**
  - [x] Re-scanned public Actions (23 runs, 10 failed) — no qualifying artifact
  - [x] Continued **DEFER**; updated `live-proof-notes.md` + doc/dev scan note
  - [x] Recapture lock green (2 passed; PYPOST-911 lock still green)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python pytest doc guards + English Markdown developer docs.
Guides: `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`,
`.cursor/lsr/do-markdown.md`. No application runtime change.

## Decision

**DEFER** (continued) — PYPOST-933 re-scan found no public failed run with
downloadable `agent-e2e-failure-artifacts*` (2026-08-01). Checklist and notes
stub updated; no invented screenshots. See `20-architecture.md`.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-933/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-933/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_recapture_doc.py`

### STEP 4: Development

- Notes: `ai-tasks/PYPOST-911/live-proof-notes.md` (PYPOST-933 re-scan section)
- Docs: `doc/dev/agent_e2e_failure_artifacts.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-933/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-933/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-933/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-933/70-dev-docs.md`
- Updates under `doc/dev/`
