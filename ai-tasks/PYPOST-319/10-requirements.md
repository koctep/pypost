# PYPOST-319: Save As Tree Update Performance

## Goals

Users who duplicate requests via `Save As...` should see the Collections sidebar update promptly,
even as their collection libraries grow. The sidebar must reflect the new request without a
noticeable pause from rebuilding the entire tree.

## User Stories

- As a **PyPost user** with many collections, I want **Save As... to update the sidebar quickly**,
  so I can continue working without UI lag after saving a copy.
- As a **PyPost user**, I want **the new request to appear under the correct collection** after
  save-as, so the sidebar stays trustworthy.

## Definition of Done

- After a successful `Save As...`, the Collections tree shows the new request without a full
  model rebuild and tree-state restore cycle.
- New collections created during save-as appear in the tree incrementally.
- Target collection expansion state is preserved when the user had that collection expanded.
- Regular `Save` behavior is unchanged (still uses full tree refresh).
- Automated tests cover incremental insert for existing and new collections.
- Developer documentation describes the save-as tree update path.

## Task Description

Follow-up from PYPOST-34 technical debt: save-as previously emitted the same post-save signal as
regular save, causing `refresh_tree()` plus `restore_tree_state()` on every save-as. At current
scale this is acceptable; this task optimizes the hot path before large libraries make it
noticeable.

### In Scope

- Incremental tree insert API on `CollectionsPresenter`.
- Separate save-as completion signal from regular save.
- MainWindow signal wiring and tests.
- Developer documentation update.

### Out of Scope

- Incremental updates for regular save or rename/delete (delete/rename already incremental).
- Disk reload behavior (addressed by PYPOST-47).
- GUI-level save-as flow tests (PYPOST-317 / PYPOST-320).

### Constraints and Assumptions

- `RequestManager` memory is authoritative after save-as completes (same as regular save).
- Tree expansion state is tracked in `StateManager` (PYPOST-388).
- Save-as may target an existing collection or a newly created one.

## Functional Requirements

- After save-as, the UI must add the new request node (or new collection node) to the tree.
- The original request row in the tree must remain unchanged.
- Expanded collections in saved state must remain expanded after save-as.

## Non-functional Requirements

- **Performance:** avoid O(n) full tree rebuild on save-as where n is total requests.
- **Consistency:** tree must match RequestManager in-memory state after save-as.
- **Regression safety:** regular save path unchanged.

## Main Entities and Interactions

| Entity | Role |
|--------|------|
| **User** | Triggers Save As... from the request editor. |
| **TabsPresenter** | Orchestrates save-as persistence and emits completion to the UI layer. |
| **CollectionsPresenter** | Owns the sidebar tree model; performs incremental inserts. |
| **MainWindow** | Wires save-as completion to incremental tree update. |
| **StateManager** | Stores which collection nodes should stay expanded. |

## Q&A

| Question | Answer |
|----------|--------|
| Jira issue | [PYPOST-319](https://pypost.atlassian.net/browse/PYPOST-319) |
| Source debt | [PYPOST-34](https://pypost.atlassian.net/browse/PYPOST-34) `60-tech-debt.md` |
| Why not optimize regular save too? | Out of scope; save-as was flagged as the debt item. |
