# PYPOST-94: Linear search on restore — tree expansion performance

## Goals

Users with large collection libraries should not experience delay when the sidebar restores
which collection nodes were expanded after a reload or save. Restore should remain responsive
as the library grows.

## User Stories

- As a user with many collections, I want expansion state to restore quickly after reload so
  the sidebar feels instant.
- As a maintainer, I want restore behavior covered by automated tests so performance
  regressions are caught before release.

## Definition of Done

- Tree state restore no longer scans every root-level collection row on each call.
- Saved expanded collection ids still expand the correct nodes after model rebuild.
- Stale ids in settings are ignored without error.
- Only collections listed in saved state are expanded (subset behavior preserved).
- Relevant unit tests pass locally and in CI.
- Developer documentation reflects the optimized restore path.

## Task Description

Follow-up from `ai-tasks/PYPOST-10/40-tech-debt.md`: `restore_tree_state` previously iterated
all root-level items to match saved expanded ids. With thousands of collections this is
unnecessarily slow when only a handful are expanded.

Implementation may already exist via PYPOST-390 (`_collection_items_by_id`); this task
verifies acceptance criteria and closes any remaining documentation or test gaps.

## Q&A

- **Q:** What scale matters? **A:** Thousands of collections; expanded count typically
  remains small (dozens).
- **Q:** Change persisted settings format? **A:** No — `StateManager.expanded_collections`
  unchanged.
