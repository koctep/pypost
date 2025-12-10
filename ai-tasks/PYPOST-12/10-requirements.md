# Requirements: PYPOST-12 - Saving Tree View State

## Goals
Users want the state of the collection tree (open/closed folders) to be preserved between application restarts. This will improve UX, as the user won't have to reopen necessary collections every time.

## User Stories
- As a user, I want the collection tree to be restored to the same state (open/closed branches) when I restart the application, so I don't have to search for necessary requests again.

## Acceptance Criteria
- [ ] On application startup, the state (collapsed/expanded) is restored for all collections.
- [ ] When collapsing/expanding a collection, the state is saved to configuration immediately (or on close).
- [ ] New collections are created collapsed by default (or expanded if convenient, but usually collapsed).
- [ ] Deleted collections are correctly removed from the saved state (cleanup, optional but desirable).

## Task Description
Implement a mechanism to save and restore the state of the `QTreeView` widget displaying collections.
To do this:
1. Add a field to the settings model to store the list of IDs of expanded collections.
2. Track branch expansion/collapse events in `MainWindow` and update settings.
3. Apply the saved state when loading collections.

## Technical Details
- **UI Component**: `QTreeView` (sidebar).
- **Storage**: `AppSettings` (json config).
- **Identification**: By collection `id` (UUID).

## Q&A
- **Do we need to save the state of nested folders?**
    - The current data model (`Collection -> Requests`) does not support nested collections (flat list of collections). If nesting appears in the future, the mechanism should be extensible. For now, we save only the state of top-level collections.
