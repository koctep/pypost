# PYPOST-32: Technical Debt Analysis

## Shortcuts Taken

- **No Request Indexing**: [FIXED in PYPOST-33] `RequestManager` currently iterates through all collections to find a request. For O(1) access, an internal dictionary mapping `id -> (request, collection)` should be maintained and updated on load/save. Given the current usage volume, linear search is acceptable.
- **StateManager Dependency**: `StateManager` is currently just a thin wrapper around `ConfigManager`'s loaded settings object. It assumes `settings` is mutable and shared. A more robust approach might be to have `StateManager` own the specific settings it manages or have granular updates.

## Code Quality Issues

- **Mixin Type Hinting**: `VariableHoverMixin` uses `self` as `QWidget` but inherits from `object` (implicit). Some `type: ignore` comments were added to satisfy static analysis conceptually, though runtime is fine since it's used with multiple inheritance.

## Missing Tests

- **Automated Tests**: No new automated tests were added because the project currently lacks a setup for running tests (pytest missing, empty tests folder). The refactoring was verified manually.

## Performance Concerns

- Same as before: Request lookup is O(N). [FIXED in PYPOST-33]

## Follow-up Tasks

- [ ] Implement `pytest` infrastructure and add tests for `RequestManager` and `StateManager`.
- [x] Add internal index to `RequestManager` for O(1) lookups. [DONE in PYPOST-33]

