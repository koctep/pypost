# PYPOST-50: Abstract StorageManager behind StorageInterface

## Summary

From PYPOST-40 audit R8. Introduce a `StorageInterface` protocol so consumers depend on
persistence contracts instead of the concrete `StorageManager` class. Enables test doubles
and future storage backends without changing manager or presenter code.

## Goals

- Define a structural protocol covering collection and environment persistence operations.
- Update core and UI consumers to type-hint against `StorageInterface`.
- Keep `StorageManager` as the production implementation and composition-root default.
- Preserve on-disk format and runtime behavior — no functional changes.

## User Stories

- As a developer, I want `RequestManager` to accept any storage implementation so that unit
  tests can use `FakeStorageManager` or mocks without subclassing `StorageManager`.
- As a developer, I want environment presenters and migration services to depend on a narrow
  persistence contract so that async workers and encryption flows remain testable.
- As a maintainer, I want SOLID audit R8 closed so that P3 storage abstraction debt is tracked
  as resolved.

## Scope

### In Scope

| Area | Expected Result |
| --- | --- |
| Protocol definition | `StorageInterface` with collection CRUD, environment load/save, encryption settings |
| Consumer type hints | `RequestManager`, `EncryptionMigrationService`, env gateway/worker, `EnvPresenter`, `SettingsDialog` |
| Test seam | `FakeStorageManager` satisfies protocol; protocol compliance tests |
| Documentation | `testability.md`, audit follow-up status |

### Out of Scope

- Splitting `StorageManager` into separate collection/environment modules (future debt).
- New storage backends (in-memory, remote) beyond existing fakes.
- Changing `MainWindow` composition root — still constructs `StorageManager`.

## Acceptance Criteria

- `StorageInterface` is `@runtime_checkable` and documents collections + environments API.
- All listed consumers accept `StorageInterface` in constructors.
- `StorageManager` and `FakeStorageManager` pass `isinstance(..., StorageInterface)`.
- Existing storage and request-manager tests pass without behavior changes.

## References

- PYPOST-40 audit R8
- `HTTPClientProtocol` pattern (PYPOST-46)
