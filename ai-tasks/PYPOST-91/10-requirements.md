# PYPOST-91: Deduplicate collection type checks in tree state handlers

## Goals

The collections sidebar persists which collection nodes are expanded. Three methods repeated the
same `isinstance(data, str)` check to distinguish collection rows from request rows. Consolidate
that logic so future changes to item typing happen in one place.

## User Stories

- As a maintainer, I want a single helper for “is this tree index a collection?” so expand/collapse
  state logic stays consistent and easier to change.
- As a user, I expect expand/collapse persistence to behave exactly as before (no functional change).

## Definition of Done

- A private `_is_collection_item(index)` helper exists on `CollectionsPresenter`.
- `_on_tree_expanded` and `_on_tree_collapsed` use the helper instead of inline type checks.
- `restore_tree_state` no longer repeats inline `isinstance(data, str)` discrimination.
- Existing expand/collapse/restore behavior is unchanged.
- Unit tests cover the helper for collection and request indices.
- Relevant test suite passes.

## Task Description

Follow-up from [PYPOST-10](https://pypost.atlassian.net/browse/PYPOST-10) tech debt: repeated type
discrimination in `on_tree_expanded`, `on_tree_collapsed`, and `restore_tree_state`.

## Q&A

- **Q:** Should request expand/collapse update persisted state? **A:** No — only collections are
  tracked; the helper gates that behavior unchanged.
- **Q:** Functional change allowed? **A:** No — refactor only.
- **Q:** Relationship to PYPOST-387? **A:** Same refactor; implemented and committed under
  PYPOST-387. PYPOST-91 closes the PYPOST-10 tracking item with verification and documentation.
