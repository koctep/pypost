# PYPOST-1060: Plaintext FakeStorageManager.deserialize_environment_records helper

## Goals

When writing unit and integration tests for environment import, presenter interactions, and storage-bound workflows, developers need test storage doubles that can deserialize environment payloads without requiring real cryptography setup, keyrings, or encryption keys.

Currently, the shared `FakeStorageManager` returns an empty stub (`([], ())`) from `deserialize_environment_records`. Because of this, test suites that exercise environment parsing or import wiring (such as `test_env_presenter.py`) must invent ad-hoc local subclasses to validate environment dictionaries into models. This creates duplicate scaffolding, increases test maintenance friction, and risks divergent double implementations across the codebase.

This task enhances the shared `FakeStorageManager` test double with built-in plaintext deserialization capabilities for environment records, providing a consistent, ready-to-use testing helper across all test suites.

**Implementation language**: Python (test infrastructure and developer productivity improvement within the existing Python test suite; no new language or stack is introduced).

## User Stories

- As a developer writing tests for environment-related features, I want the shared test storage manager (`FakeStorageManager`) to deserialize plaintext environment records by default, so that I do not need to create custom subclasses or stub methods in every test module.
- As a test suite maintainer, I want environment deserialization in `FakeStorageManager` to handle valid and invalid payloads cleanly, returning parsed environments and collected errors, so that error-handling tests can also rely on the standard fake double.
- As a developer maintaining existing tests that use `FakeStorageManager`, I want existing test cases to continue passing without regressions or unexpected side effects.

## Definition of Done

- `FakeStorageManager.deserialize_environment_records` deserializes valid environment dictionary records into domain `Environment` objects without requiring encryption ceremony or cryptographic keys.
- Invalid records (such as malformed payloads or missing required fields) produce descriptive error messages/objects and do not cause uncaught exceptions during batch deserialization.
- The return signature remains consistent with the storage interface expectations (a tuple of parsed environments and parse errors).
- Existing test suites using `FakeStorageManager` (including collection and presenter tests) continue to pass without unintended breakage.
- Existing ad-hoc overrides (such as the local `ImportFakeStorage` subclass in `tests/test_env_presenter.py`) are refactored to use the shared `FakeStorageManager` directly.
- Unit tests covering `FakeStorageManager.deserialize_environment_records` verify parsing of valid records, handling of empty inputs, and error reporting for invalid records.
- All new tests follow project test guidelines (explicit pytest timeouts, fast hermetic execution).

## Task Description

PYPOST-1000 identified technical debt in `ai-tasks/PYPOST-1000/60-tech-debt.md` where testing presenter import wiring required defining a local subclass (`ImportFakeStorage`) because `FakeStorageManager.deserialize_environment_records` was merely a no-op stub returning `([], ())`.

This task resolves that technical debt by equipping `FakeStorageManager` with a standard plaintext deserialization implementation for environment records.

### In Scope

- Updating `FakeStorageManager.deserialize_environment_records` in `tests/helpers/__init__.py` (or shared test helper module) to deserialize environment dictionaries.
- Simplifying existing tests (such as `tests/test_env_presenter.py`) that implemented local subclasses for this purpose.
- Adding dedicated unit tests for the updated helper functionality.

### Out of Scope

- Modifying production storage implementations (`pypost/core/storage_manager.py`) or encryption logic.
- Changing `StorageInterface` contracts or application behavior.
- Altering the on-disk storage format or environment serialization schemas.

## Non-Functional Requirements

- **Hermetic & Fast**: All operations in `FakeStorageManager` must run in-memory without filesystem I/O, network calls, or crypto delays.
- **Robustness**: Deserialization of bad/corrupt records must gracefully record errors without crashing.
- **Maintainability**: The helper must be clean, readable, and reuse standard model validation paths where appropriate.

## Main Entities

- **FakeStorageManager**: The shared test double representing storage interactions in unit and presenter tests.
- **Environment Record**: A raw dictionary representation of an environment's configuration and variables.
- **Environment**: The core domain model representing an environment in PyPost.
- **Deserialization Result**: The pair of successfully parsed `Environment` instances and any error descriptions encountered.

## User Scenarios

1. **Happy path parsing in tests**: A test passes a list of valid environment record dictionaries to `FakeStorageManager.deserialize_environment_records`. The helper returns a list of populated `Environment` model objects and an empty error tuple.
2. **Malformed record handling in tests**: A test passes invalid or malformed environment records to simulate import error scenarios. The helper collects the errors and returns the valid subset along with the error details.
3. **Presenter import test cleanup**: `test_open_env_manager_passes_working_read_import_file` uses `FakeStorageManager()` directly instead of defining a custom `ImportFakeStorage` class.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this a quality/productivity goal rather than just a cosmetic change? | Reusable, high-fidelity test doubles prevent test authors from writing redundant mocks and ensure consistent behavior across all environment-related unit tests. |
| Why plaintext deserialization in the test double? | In unit tests, requiring real encryption setup or mocked symmetric ciphers adds unnecessary complexity to tests that are only asserting higher-level logic (like UI wiring or import flows). |
| Will this break tests that expect `deserialize_environment_records` to return empty? | Existing tests that pass empty inputs will still receive empty results (`[], ()`). Tests that pass non-empty records will now receive properly parsed environment models instead of an empty list, matching expected fake storage semantics. |
