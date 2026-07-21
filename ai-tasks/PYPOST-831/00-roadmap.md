# Roadmap: PYPOST-831

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extracted `_ensure_current_is_navigable(preferred_index)` from
    `close_tab`'s PYPOST-824 reselect logic
  - [x] Wired helper into `close_tab` (behavior-preserving) and
    `close_tabs_for_request_ids` (once after removeTab loop;
    preferred = left of leftmost closed index)
  - [x] Added bulk-close regression tests so rightmost / multiple-rightmost
    close does not leave current on `+`; strengthened all-closed focus assert
  - [x] Focused presenter tests green
    (`close_tabs_for_request_ids` / `land_on_plus` / `close_tab`: 12 passed)

- [x] **STEP 4: Code Cleanup**
  - [x] `make lint` clean; scoped flake8 on presenter + tests (E402 ignored)
  - [x] Focused presenter tests green (61 passed); module `pytestmark` timeout
  - [x] `ai-tasks/PYPOST-831/40-code-cleanup.md` created
- [x] **STEP 5: Observability**
  - [x] Assessed logging/metrics for `_ensure_current_is_navigable` extract +
    bulk-close wire-up; no new logs (matches PYPOST-824 stance)
  - [x] Existing `close_tabs_for_deleted_requests` INFO retained
  - [x] `ai-tasks/PYPOST-831/50-observability.md` created
- [x] **STEP 6: Review and Technical Debt**
  - [x] Reviewed `_ensure_current_is_navigable`, `close_tab`,
    `close_tabs_for_request_ids`, and presenter tests vs requirements /
    architecture
  - [x] Focused close/bulk tests green (12 passed); module timeout present
  - [x] `ai-tasks/PYPOST-831/60-tech-debt.md` created — no new unticketed debt
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/request_actions.md` for shared navigable reselect
    (`_ensure_current_is_navigable`) on single and bulk close
  - [x] Updated `doc/dev/collection_item_delete.md` post-delete focus note
  - [x] `ai-tasks/PYPOST-831/70-dev-docs.md` created

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-831/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-831/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-831/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-831/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-831/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-831/70-dev-docs.md`
- `doc/dev/request_actions.md`
- `doc/dev/collection_item_delete.md`

## Suggested branch name

`fix/PYPOST-831-bulk-close-tab-reselect`
