# PYPOST-29: Technical Debt Analysis


## Shortcuts Taken

- **No Request Indexing**: [FIXED in PYPOST-8] `RequestManager` currently iterates through all collections to find a request. For O(1) access, an internal dictionary mapping `id -> (request, collection)` should be maintained and updated on load/save. Given the current usage volume, linear search is acceptable.
- **StateManager Dependency**: `StateManager` is currently just a thin wrapper around `ConfigManager`'s loaded settings object. It assumes `settings` is mutable and shared. A more robust approach might be to have `StateManager` own the specific settings it manages or have granular updates. — [PYPOST-249](https://pypost.atlassian.net/browse/PYPOST-249)

## Code Quality Issues

- **Mixin Type Hinting**: `VariableHoverMixin` uses `self` as `QWidget` but inherits from `object` (implicit). Some `type: ignore` comments were added to satisfy static analysis conceptually, though runtime is fine since it's used with multiple inheritance. — [PYPOST-250](https://pypost.atlassian.net/browse/PYPOST-250)

## Missing Tests

- **Automated Tests**: [RESOLVED in PYPOST-251/PYPOST-252] Pytest infrastructure (`pytest.ini`, `Makefile`, `tests/conftest.py`) and a broad `tests/` suite are in place; manager unit tests documented in `doc/dev/testing.md`.

## Performance Concerns

- Same as before: Request lookup is O(N). [FIXED in PYPOST-8]

## Follow-up Tasks

- [x] Implement `pytest` infrastructure and add tests for `RequestManager` and `StateManager`. [DONE in PYPOST-251/PYPOST-252]
- [x] Add internal index to `RequestManager` for O(1) lookups. [DONE in PYPOST-8]

