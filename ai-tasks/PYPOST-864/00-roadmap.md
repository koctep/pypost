# Roadmap: PYPOST-864

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_seed_inventory_doc.py` —
    `test_seed_inventory_constants_match_doc`
    (Step 3: red `pytest.fail` placeholder; Step 4: real asserts)
- [x] **STEP 4: Development**
  - [x] Replaced placeholder with `SEED_*` ↔
    `doc/dev/agent_e2e_seed.md` presence asserts
  - [x] Verified: **1 passed**; no production edits
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE; unticketed optional follow-ups listed
    (bidirectional parse, POST body token) — Jira not called this run
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/agent_e2e_seed.md` and `doc/dev/agent_e2e.md`
  - [x] Artifact: `ai-tasks/PYPOST-864/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`) for the inventory drift guard test.
Markdown inventory page under `doc/dev/` follows `.cursor/lsr/do-markdown.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-864/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-864/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_seed_inventory_doc.py` —
  `test_seed_inventory_constants_match_doc`

### STEP 4: Development

- `tests/test_agent_e2e_seed_inventory_doc.py` (drift-guard body)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-864/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-864/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-864/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_seed.md`
- `doc/dev/agent_e2e.md`
- `ai-tasks/PYPOST-864/70-dev-docs.md`

## Suggested branch name

`test/PYPOST-864-seed-inventory-drift-guard`

## Decision

**SAFE TO CLOSE** — test-only lightweight Option C subset; production seed
module unchanged; docs point maintainers at the guard.

## Suggested commit message (not committed this run)

```
test(PYPOST-864): guard seed inventory code vs doc drift

Assert SEED_* constants appear in doc/dev/agent_e2e_seed.md so fixture
inventory and developer docs stay synced.
```
