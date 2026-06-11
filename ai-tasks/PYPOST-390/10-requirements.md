# PYPOST-390: Optimize tree state restore for large collections

## Goals

Users with many collections (hundreds or thousands) should not pay a full root-level scan on
every tree state restore. Restore should scale with the number of expanded collections, which
is typically small, rather than total collection count.

## User Stories

- As a user with a large library, I want the collections sidebar to restore expansion state
  quickly after reload or save without noticeable delay.
- As a maintainer, I want restore logic documented and tested so regressions in performance or
  behavior are caught in CI.

## Definition of Done

- `restore_tree_state` no longer scans every root-level tree row to find expanded collections.
- Valid expanded ids still expand the correct Qt tree nodes after `load_collections` / rebuild.
- Stale ids in settings are still ignored (no regression from PYPOST-389).
- Subset expansion behavior preserved (PYPOST-391).
- Collection lookup by id remains correct for rename/delete/incremental insert paths.
- Relevant unit tests pass locally and in CI.
- Developer docs updated.

## Task Description

Follow-up from `ai-tasks/PYPOST-8/40-tech-debt.md`: `restore_tree_state` previously iterated
all root-level items and checked membership in the saved expanded list. With thousands of
collections this is unnecessarily slow when only a handful are expanded.

## Q&A

- **Q:** Target scale? **A:** Thousands of collections; expanded count remains dozens in
  typical usage.
- **Q:** Change persistence format? **A:** No — `StateManager.expanded_collections` unchanged.
