# PYPOST-482: Technical Debt Analysis

## Shortcuts Taken

None. Refactor preserves behavior; no temporary workarounds introduced.

## Code Quality Issues

- `EnvironmentVariablesAdapter` still combines policy resolution, iteration, metrics, and logging
  in one class. Further split (e.g. metrics decorator or policy object) is optional.
- `StorageManager` retains collection and environment persistence in one module; splitting
  collection storage would be a separate task.

## Missing Tests

- Adapter tests cover happy path, settings override, metrics for encrypt/decrypt/unsupported
  format. Key-mismatch and missing-key scenarios remain covered only via `StorageManager` tests
  (acceptable regression coverage).

## Performance Concerns

None introduced. Same per-value encrypt/decrypt loop; PYPOST-485 tracks optimization separately.

## Follow-up Tasks

- Reduce per-value encryption overhead on save/load paths.
  Jira: [PYPOST-485](https://pypost.atlassian.net/browse/PYPOST-485)
- Represent encrypted envelope via typed model for centralized validation.
  Jira: [PYPOST-484](https://pypost.atlassian.net/browse/PYPOST-484)
- Add graceful shutdown wait for `EnvironmentStorageGateway` when encryption is enabled.
  Jira: [PYPOST-508](https://pypost.atlassian.net/browse/PYPOST-508)
