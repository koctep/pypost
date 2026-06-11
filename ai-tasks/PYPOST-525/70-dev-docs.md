# PYPOST-525 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-11
> Sprint: (current)

---

## 1. What Changed and Why

PYPOST-525 adds a supported storage API for loading stored environments while collecting
per-environment decrypt and deserialize failures. Encryption migration tooling (`verify`,
`re-encrypt`, `encrypt-plaintext`) needs every bad environment listed without aborting the batch;
the desktop UI path (`load_environments()`) intentionally returns `[]` on any failure.

Migration no longer reaches into private `StorageManager._env_adapter`. It calls
`load_environments_with_errors()` and maps structured `EnvironmentLoadFailure` records to the
existing operator string format (`"name: reason"`).

---

## 2. New and Updated Modules

- `pypost/core/storage.py`
  - `EnvironmentLoadFailure` — frozen dataclass with `name`, `environment_id`, `reason`,
    `format_operator_message()`
  - `StorageManager.load_environments_with_errors()` — batch load with per-item failure collection
  - `load_environments()` — unchanged all-or-nothing contract for desktop UI
- `pypost/core/encryption_migration.py`
  - `_deserialize_all()` — uses public storage API; no `_env_adapter` access

No changes to `EnvironmentVariablesAdapter`, codec, key provider, or CLI surface.

---

## 3. Documentation Updated

- `doc/dev/environment_encryption_at_rest.md`
  - Dual load contracts (`load_environments` vs `load_environments_with_errors`)
  - `EnvironmentLoadFailure` and migration-oriented API reference
  - Observability event names for the new load path
- `doc/dev/encryption_key_migration.md`
  - Architecture diagram and developer API note: migration uses
    `load_environments_with_errors()`
  - Troubleshooting: per-environment failure reporting via structured storage API

---

## 4. Configuration Summary

No new settings or environment variables. Callers must invoke
`StorageManager.apply_encryption_settings(settings)` before
`load_environments_with_errors()` when encryption policy matters (same as
`load_environments()`).

---

## 5. Testing

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_storage_environments.py \
  tests/test_encryption_migration.py \
  -k "load_environments_with_errors or deserialize_all_uses_public"
```

Full regression:

```bash
make test
```

---

## 6. Related Tickets

- `PYPOST-487` — encryption migration service and CLI (introduced private adapter coupling)
- `PYPOST-525` — supported per-environment failure reporting for migration (this task)
- TD-1 resolved in `ai-tasks/PYPOST-487/60-tech-debt.md`
