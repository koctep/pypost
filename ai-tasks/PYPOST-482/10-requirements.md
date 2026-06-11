# PYPOST-482: Refactor StorageManager encryption responsibilities into adapter/service

## Goals

Environment encryption at rest (PYPOST-447) grew encryption policy, variable serialization,
metrics, and logging inside `StorageManager`. That coupling makes the storage class harder to
test and maintain, especially after PYPOST-486 added async orchestration around the same API.
This task separates environment variable encoding from file I/O so each component has a single
responsibility while preserving runtime behavior and observability.

## User Stories

- As a maintainer, I want environment variable encryption logic isolated from file persistence so
  I can unit test policy and serialization without mocking the filesystem.
- As a developer extending encryption, I want a clear adapter boundary so changes to encrypt/decrypt
  flows do not require editing collection storage code.
- As an operator, I want unchanged encryption metrics and logs after the refactor so existing
  dashboards and alerts keep working.

## Definition of Done

- Environment variable serialization and deserialization (including encryption policy) live in a
  dedicated adapter/service module.
- `StorageManager` focuses on paths, collections, and atomic environment file I/O.
- Existing storage and encryption tests pass without behavior changes.
- Metrics counters and structured logs for encrypt/decrypt/error paths are preserved.
- `EnvironmentStorageGateway` / `EnvironmentStorageWorker` integration continues to work via
  the unchanged `StorageManager` public API.
- Developer documentation describes the new module boundary.

## Task Description

`StorageManager` currently combines encryption policy resolution, per-variable
serialize/deserialize, Prometheus metrics, and structured logging with collection and environment
file persistence. PYPOST-447 technical debt identified this as a maintainability risk.

### In Scope

- Extract environment value serialization/encryption into a dedicated adapter.
- Delegate from `StorageManager` on save/load environment paths.
- Preserve encryption policy application via `apply_encryption_settings`.
- Preserve metrics emission and log event names/fields.
- Add focused unit tests for the adapter.

### Out of Scope

- Changing encryption envelope format or policy resolution rules.
- Async load/save behavior (PYPOST-486).
- Per-value encryption optimization (PYPOST-485).
- Typed envelope model refactor (PYPOST-484).

## Functional Requirements

- Hidden-key values must still encrypt on save when encryption is enabled.
- Encrypted payloads must still decrypt on load with the same error semantics.
- Plain-text values and non-hidden keys must remain unencrypted.
- `apply_encryption_settings` must reconfigure the adapter without restarting the app.
- Save/load failures (encrypt, decrypt, unsupported format) must behave as before.

## Non-functional Requirements

- **Testability**: adapter testable without filesystem I/O.
- **Backward compatibility**: no changes to `environments.json` on-disk format.
- **Observability**: existing metric names and log keys unchanged.
- **Maintainability**: `StorageManager` reduced complexity; adapter owns variable encoding.

## Constraints and Assumptions

- `EnvironmentSecretsCodec` remains the low-level Fernet envelope implementation.
- Python 3.10+; project line-length and markdown rules apply.
- Async gateway continues calling synchronous `StorageManager` methods.

## Main Entities and Interactions

- **Storage manager**: persists collections and environment JSON files.
- **Environment variables adapter**: applies encryption policy to variable maps on save/load.
- **Secrets codec**: encrypts/decrypts individual hidden values.
- **Metrics manager**: counts encryption operations and errors (optional dependency).
- **Application settings**: encryption policy input via `apply_encryption_settings`.

Interaction overview:

1. UI or worker calls `StorageManager.save_environments` / `load_environments`.
2. Storage manager reads/writes JSON and delegates variable encoding to the adapter.
3. Adapter resolves policy, invokes codec, emits metrics/logs, returns plain variable maps.

## Q&A

- Q: Why not move file I/O into the adapter too?
  A: Collections and environment files share the storage manager; scope is variable encoding only.
- Q: Will async workers need changes?
  A: No — they keep using `StorageManager`; the adapter is an internal detail.
- Q: Are metric names allowed to change?
  A: No — preserve existing Prometheus counters for operational continuity.
