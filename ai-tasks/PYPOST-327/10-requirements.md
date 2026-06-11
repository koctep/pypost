# PYPOST-327: Decouple collection persistence identity from display name

## Goals

Collection files on disk must use a stable identifier so renaming a collection in the UI
does not change its storage location, and two collections with the same display name cannot
overwrite each other's persisted data.

## User Stories

- As a user, when I rename a collection, my requests stay associated with that collection
  without risk of data loss from filename changes.
- As a user, I can have collections with distinct identities even if display names collide
  on disk (no silent overwrites).

## Definition of Done

- Collection JSON files are stored under a stable collection ID, not the display name.
- Existing name-based collection files are migrated automatically on load.
- Renaming a collection updates only the JSON content, not the filename.
- Regression tests cover save, rename, delete, and legacy migration.

## Task Description

Follow-up from PYPOST-35 tech debt: `StorageManager` used `collection.name` as the filename,
coupling persistence identity to a mutable display field.

## Q&A

- **Why not only fix collisions?** Stable ID filenames eliminate rename side effects and
  are the foundation for safer collection lifecycle work in this sprint.
