# PYPOST-387: Deduplicate collection type checks in tree state handlers

## Goals

The collections sidebar persists which collection nodes are expanded. Three methods repeat the
same `isinstance(data, str)` check to distinguish collection rows from request rows. Consolidate
that logic so future changes to item typing happen in one place.

## User Stories

- As a maintainer, I want a single helper for “is this tree index a collection?” so expand/collapse
  state logic stays consistent and easier to change.
- As a user, I expect expand/collapse persistence to behave exactly as before (no functional change).

## Definition of Done

- A private `_is_collection_item(index)` helper exists on `CollectionsPresenter`.
- `_on_tree_expanded`, `_on_tree_collapsed`, and `restore_tree_state` use the helper instead of
  inline `isinstance(data, str)` checks.
- Existing expand/collapse/restore behavior is unchanged.
- Unit tests cover the helper for collection and request indices.
- Full relevant test suite passes.

## Task Description

Follow-up from PYPOST-8 tech debt: repeated type discrimination in tree state methods.

## Q&A

- **Q:** Should request expand/collapse update persisted state? **A:** No — only collections are
  tracked; the helper gates that behavior unchanged.
- **Q:** Functional change allowed? **A:** No — refactor only.
