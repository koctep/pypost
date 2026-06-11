# PYPOST-487: Technical Debt Analysis

## Shortcuts Taken

- **Private storage adapter access** — `_deserialize_all()` calls
  `self._storage._env_adapter.deserialize_environment()` instead of the public
  `StorageManager.load_environments()`. This bypasses `load_environments()` because that method
  swallows all failures and returns an empty list, while migration needs per-environment error
  details. The trade-off is tighter coupling to a private attribute.
- **Duplicate JSON read path** — Inventory scans `environments.json` directly via
  `_read_raw_environments()` / `_scan_raw_environments()` rather than going through
  `StorageManager`. This avoids full decrypt on `report` but duplicates envelope-shape detection
  (`enc: true`, `kid`) that also exists in `EnvironmentVariablesAdapter`.
- **CLI `sys.path` bootstrap** — `scripts/encryption_migrate.py` prepends the repo root to
  `sys.path` so it can run without package install. Consistent with ad-hoc operator scripts but
  not a registered console entry point.
- **Optional Settings UI deferred** — Architecture listed optional “Verify encryption” /
  “Re-encrypt all environments” actions in `SettingsDialog`; Step 3 scoped core + CLI only.
  Desktop operators must use the CLI until a follow-up wires the same service into the UI.
- **Operator runbook deferred to Step 7** — Rollout stages, scenario procedures, and fallback
  matrix are designed in architecture but `doc/dev/encryption_key_migration.md` is not written
  yet. Tooling exists ahead of operator documentation.

## Code Quality Issues

- **`build_inventory(check_decrypt=True)` is unused** — The parameter raises
  `EnvironmentEncryptionError` on the first decrypt failure, while `verify_decrypt_access()`
  collects all errors into a `MigrationReport`. No caller uses `check_decrypt=True`; the API
  surface is inconsistent and partially dead.
- **`bulk_re_encrypt` always rewrites** — When all hidden values already use the active `kid`,
  the service still loads, decrypts, and saves every environment. A pre-check comparing the
  histogram to the active key could skip the write (no functional bug, extra I/O).
- **Envelope edge cases not surfaced** — `_scan_raw_environments()` ignores hidden values that
  are neither envelope dicts nor plain strings (e.g. `null`, numbers, malformed dicts without
  `enc`). They are omitted from inventory counts rather than reported as data-quality errors.
- **Empty `kid` in envelopes** — Envelopes with `enc: true` but missing/empty `kid` increment
  `encrypted_envelope_count` but not `kid_histogram`; verify may pass `missing_kids` while
  hiding the bad envelope shape.
- **No `--data-dir` / path overrides on CLI** — Operators cannot point the tool at an alternate
  data directory; it always uses `ConfigManager` + default `StorageManager` paths. Backup/restore
  workflows on copied files require manual path setup or env overrides.
- **Human-readable stdout only** — CLI output is fixed text; no `--json` flag for automation or
  CI inventory checks.

## Missing Tests

- **`build_inventory(check_decrypt=True)`** — Raise-on-failure path has no coverage.
- **Non-env key sources** — Tests cover environment variable and env registry keys only. No
  integration tests for `keyring` or `secret_store` primary/fallback chains during verify or
  re-encrypt.
- **Malformed `environments.json`** — Non-list root, invalid JSON, and per-env deserialize
  failures beyond corrupt ciphertext (e.g. missing `name`) are untested.
- **Envelope shape edge cases** — Hidden values with wrong types, empty `kid`, or partial
  envelope dicts are not asserted in inventory or verify output.
- **Backup failure** — `backup_environments_file()` success is tested; disk-permission or
  full-disk failure during `--backup` is not.
- **CLI `encrypt-plaintext --dry-run`** — Service dry-run is tested; CLI wrapper for
  `encrypt-plaintext --dry-run` is not (only `re-encrypt --dry-run` has a CLI test).
- **Concurrent access** — No test that migration fails safely if the desktop app holds an open
  write lock (if applicable on the platform).

## Performance Concerns

- **Full-file load for every operation** — All commands read and (for verify/rewrite) decrypt
  the entire `environments.json`. Acceptable for typical desktop datasets; large team deployments
  with many environments may need batching or streaming (out of scope for PYPOST-487).
- **Double inventory scan on rewrite** — `_rewrite_environments()` calls `build_inventory()`
  before and after save. Correct for reporting but redundant work on large files.
- **No progress feedback** — Long-running bulk re-encrypt gives no incremental progress to
  the operator (logs only at start/end).

## Architecture Deviations

| Planned (Step 2) | Delivered (Step 3) | Impact |
| --- | --- | --- |
| Optional Settings UI verify/re-encrypt actions | Not implemented | Operators rely on CLI only |
| `doc/dev/encryption_key_migration.md` runbook | Deferred to Step 7 | Tooling without consolidated operator doc |
| Inventory via optional `check_decrypt` on `build_inventory` | Implemented but unused; verify uses separate path | API confusion |

Core boundaries are preserved: no changes to codec, envelope format, `KeySourceChain`, or
`StorageManager` atomic save contract.

## Follow-up Tasks

| ID | Priority | Task | Rationale |
| --- | --- | --- | --- |
| TD-1 | Medium | Add public `StorageManager` method to deserialize environments with per-item errors (or make `load_environments` raise/report) and remove `_env_adapter` access from migration | Reduce coupling to private API. Jira: [PYPOST-525](https://pypost.atlassian.net/browse/PYPOST-525) |
| TD-2 | Low | Remove or unify `build_inventory(check_decrypt=True)` with `verify_decrypt_access()` | Eliminate dead/inconsistent API. Jira: [PYPOST-526](https://pypost.atlassian.net/browse/PYPOST-526) |
| TD-3 | Medium | Optional Settings UI: “Verify encryption” and “Re-encrypt all environments” delegating to `EncryptionMigrationService` with confirmation | Architecture Step 3 optional scope. Jira: [PYPOST-527](https://pypost.atlassian.net/browse/PYPOST-527) |
| TD-4 | High | Complete `doc/dev/encryption_key_migration.md` (Step 7) with rollout stages, CLI usage, cross-link from `environment_encryption_at_rest.md` | **Done in PYPOST-487 Step 7** |
| TD-5 | Low | Skip no-op `bulk_re_encrypt` when histogram already matches active `kid` only | Avoid unnecessary writes. Jira: [PYPOST-528](https://pypost.atlassian.net/browse/PYPOST-528) |
| TD-6 | Low | Flag non-string/non-envelope hidden values in inventory as data-quality errors | Safer operator reports. Jira: [PYPOST-529](https://pypost.atlassian.net/browse/PYPOST-529) |
| TD-7 | Low | CLI `--json` output and optional `--data-dir` for scripted verify in CI/backup restores | Operability for teams. Jira: [PYPOST-530](https://pypost.atlassian.net/browse/PYPOST-530) |
| TD-8 | Low | Integration tests with keyring and secret_store fixtures | Confidence for Stage 2–3 rollouts. Jira: [PYPOST-531](https://pypost.atlassian.net/browse/PYPOST-531) |
| TD-9 | Low | CLI test for `encrypt-plaintext --dry-run` | Parity with service-layer dry-run coverage. Jira: [PYPOST-532](https://pypost.atlassian.net/browse/PYPOST-532) |

## Review

Step 6 analysis complete. No blocking debt prevents Step 7 (operator runbook and dev docs).
Highest-value follow-ups: **TD-4** (Step 7 deliverable), **TD-3** (UI parity), **TD-1**
(public deserialize API).

**User review requested** per workflow Step 6 before marking complete and proceeding to Step 7.
