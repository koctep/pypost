# PYPOST-48: Replace item_type branching with strategy in RequestManager

## Goals

The PYPOST-40 SOLID audit found that `RequestManager` branches on `item_type` strings when
deleting or renaming collection tree items. That coupling makes adding new item types a
modify-the-core-method change. This task improves extensibility so collection operations stay
maintainable as the product evolves.

## User Stories

- **As a developer**, I want collection item delete/rename routing to be extensible without
  editing `RequestManager` dispatch methods, so new tree item types can be added safely.
- **As a developer**, I want existing delete/rename behavior for collections and requests
  unchanged, so presenters and tests keep working without API churn.

## Definition of Done

- [ ] `delete_collection_item` and `rename_collection_item` no longer use inline
  `if item_type == ...` branching.
- [ ] A registry or strategy maps supported `item_type` values to delete/rename behavior.
- [ ] Default behavior for `"collection"` and `"request"` matches pre-refactor semantics.
- [ ] Unsupported types still log a warning and return `False`.
- [ ] Unit tests cover default routing and custom strategy injection.
- [ ] Developer docs note the pattern for future item types.

## Scope

**In scope:** `RequestManager` dispatch for `delete_collection_item` and
`rename_collection_item`; strategy module; unit tests; dev documentation.

**Out of scope:** New collection tree item types; presenter or UI changes; storage layer changes.

## Constraints

- Python codebase; follow existing `pypost/core` module layout.
- Preserve public method signatures on `RequestManager`.
- No change to logging event names or levels for supported types.

## Assumptions

- Only `"collection"` and `"request"` are supported today; future types register in the
  strategy map.
- Callers continue passing `item_type` as a string from the collections tree UI.
