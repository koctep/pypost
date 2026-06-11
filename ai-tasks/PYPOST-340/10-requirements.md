# PYPOST-340: Evaluate index-assisted deletion path for large datasets

## Goals

PYPOST-35 and PYPOST-333 introduced `_request_index` for O(1) request lookup during
delete. This debt item evaluates whether the delete path scales for large collections
and closes any gaps found without changing user-visible behavior.

## Programming Language

Python (pypost application codebase).

## User Stories

- As a maintainer, I want a documented evaluation of delete-path complexity so future
  performance work targets the right bottleneck.
- As a user with large collections, I want request deletion to remain responsive when
  many requests exist across collections.
- As a developer, I want automated tests that guard index consistency after bulk deletes.

## Definition of Done

- Evaluation documents lookup, list-removal, and index-update costs for
  `delete_request` and `delete_collection`.
- Delete paths use incremental index updates instead of full `_rebuild_index()` when
  safe.
- Tests prove index consistency and that delete avoids full rebuild.
- Large-collection test (hundreds of requests) passes.
- Developer docs describe the index-assisted delete behavior.
- All related unit tests pass.

## Task Description

Follow-up from `ai-tasks/PYPOST-35/60-tech-debt.md`. PYPOST-333 added index lookup;
this task evaluates and hardens the remainder of the delete path for scale.

### Scope

- In scope: `RequestManager.delete_request`, `delete_collection`, index helpers,
  unit tests, dev docs.
- Out of scope: UI incremental tree refresh (PYPOST-334), ID-based filenames
  (PYPOST-336), save/rename index strategy changes.

## Q&A

- **Q:** Is a full index rebuild required after every delete? **A:** No — only the
  removed request IDs need to leave the index; evaluation confirms incremental drop is
  sufficient.
- **Q:** What remains O(n) after this task? **A:** Removing a request from its parent
  collection list is O(m) where m is requests in that collection; acceptable for
  single-item deletes.
