# PYPOST-481 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-10
> Sprint: (current)

---

## 1. What Changed and Why

PYPOST-481 exposes environment encryption-at-rest policy in the Settings UI. Before this task,
encryption was controlled only via process environment variables (`PYPOST_ENV_ENCRYPTION_ENABLED`,
`PYPOST_ENV_ENCRYPTION_KEY`). Users can now persist an explicit enable/disable choice and select
the key source strategy while keeping Fernet key material out of `settings.json`.

Runtime behavior is unchanged: hidden values are still encrypted only at persistence time when
encryption is enabled, and `Environment.variables` remains plain text in memory after load.

---

## 2. New and Updated Modules

- `pypost/core/encryption_config.py` (new)
  - `resolve_encryption_enabled()` — settings override with env-var fallback.
  - `resolve_key_source()` — key source strategy with unsupported-value fallback.
  - `build_key_provider()` — factory returning `LocalKeyProvider` for `"environment"`.
- `pypost/models/settings.py`
  - `env_encryption_enabled`, `env_encryption_key_source` optional fields on `AppSettings`.
- `pypost/core/storage.py`
  - `apply_encryption_settings()` rebuilds codec/key provider from resolved policy.
- `pypost/ui/dialogs/settings_dialog.py`
  - Encryption mode and key source combos with secure-setup helper label.
- `pypost/ui/main_window.py`
  - Calls `storage.apply_encryption_settings()` on init and after settings save.

---

## 3. Documentation Updated

- `doc/dev/environment_encryption_at_rest.md`
  - Added **Architecture** (mermaid diagram, component table, data flow).
  - Added **API / Usage** (`AppSettings` fields, resolver functions, storage apply hook, UI).
  - Expanded **Configuration** (app settings + env vars, unchanged secure-setup steps).
  - Added **Troubleshooting** (missing key, decrypt failures, policy timing, env-var restarts).
  - Retained payload format, metrics, and test references from PYPOST-447 baseline.
- `doc/dev/README.md` — no change required; navigation entry already present.

---

## 4. Configuration Summary

| Source | Field / variable | Effect |
| --- | --- | --- |
| Settings | `env_encryption_enabled = None` | Follow `PYPOST_ENV_ENCRYPTION_ENABLED` |
| Settings | `env_encryption_enabled = True/False` | Explicit override |
| Settings | `env_encryption_key_source` | `"environment"` (only supported value) |
| Env var | `PYPOST_ENV_ENCRYPTION_ENABLED` | Fallback when settings field is `None` |
| Env var | `PYPOST_ENV_ENCRYPTION_KEY` | Fernet key material (never in settings file) |

---

## 5. Testing

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_encryption_config.py \
  tests/test_settings_encryption.py \
  tests/test_storage_environments.py
```

Full regression:

```bash
make test
```

---

## 6. Related Tickets

- `PYPOST-447` — encryption-at-rest foundation.
- `PYPOST-481` — user-facing encryption settings (this task).
- `PYPOST-483` — additional key provider strategies (follow-up).
- `PYPOST-487` — migration tooling when toggling encryption on existing data (follow-up).
