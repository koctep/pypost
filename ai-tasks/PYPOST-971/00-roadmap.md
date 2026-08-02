# Roadmap: PYPOST-971

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red test: `tests/test_display_role_scan_ownership.py`
    (`test_flat_and_tree_share_display_role_match_helper`)
- [x] **STEP 4: Development**
  - [x] Added `display_role_equals` + `find_child_index_by_display_text` in
    `tree_index.py`; wired `_select_item_view` and tree DFS to shared match
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Suggested branch
`refactoring/PYPOST-971-share-display-role-scan`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-971/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-971/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-971/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-971/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-971/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md` (shared helpers + flat vs recursive)
- `doc/dev/testing.md` (tree_index ownership note)
- `ai-tasks/PYPOST-971/70-dev-docs.md`
