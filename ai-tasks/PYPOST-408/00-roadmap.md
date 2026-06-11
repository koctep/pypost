# Roadmap: PYPOST-408

**Suggested branch:** `feature/PYPOST-408-sync-isolated-tab-metadata`

## Implementation

- **Programming language:** Python (PySide6 / Qt), same stack as the PyPost desktop app.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `request_sync` helpers and `persisted_baseline` on `RequestTab`
  - [x] Added `request_persisted` signal, sibling stale dialogs, and label sync on save
  - [x] Fixed overwrite save updating all matching tabs; extended rename baseline sync
  - [x] Tests in `tests/test_tabs_presenter.py` (715 total passing)
- [x] **STEP 4: Code Cleanup**
  - [x] flake8 clean on `request_sync.py`, `tabs_presenter.py`, `test_tabs_presenter.py`
  - [x] `40-code-cleanup.md` created
- [x] **STEP 5: Observability**
  - [x] Documented save/stale-guard logging in `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md` created (missing tests, logging gaps, Step 7 docs)
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/open_request_in_isolated_tab.md` with stale-tab sync
  - [x] `70-dev-docs.md` created

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-408/10-requirements.md`
- Programming Language: Python (PySide6 / Qt)

### STEP 2: Architecture

- `ai-tasks/PYPOST-408/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-408/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-408/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-408/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/open_request_in_isolated_tab.md`
- `ai-tasks/PYPOST-408/70-dev-docs.md`

## Context

Follow-up from [PYPOST-405](https://pypost.atlassian.net/browse/PYPOST-405) technical debt
(item TD-3 in `ai-tasks/PYPOST-405/60-review.md`). PYPOST-405 introduced isolated tabs so
unsaved edits in one tab do not leak to another. Renaming a request from the Collections
sidebar keeps tab titles aligned, but when a user saves other changes (for example an updated
URL) from one tab, other open tabs for the same saved request are not informed and may still
show outdated content. This task closes that gap from a user-awareness and consistency
perspective.
