# PYPOST-540 — Developer Documentation

> Date: 2026-06-11

---

## 1. What Changed and Why

PYPOST-540 adds optional `--config-dir` to `encryption_migrate.py` so backup-restore workflows
can load `settings.json` from a copied config directory instead of the platform default.
`ConfigManager` now accepts an optional `config_dir` keyword for headless tooling.

---

## 2. New and Updated Modules

- `pypost/core/config_manager.py`
  - Optional keyword-only `config_dir` parameter on `ConfigManager.__init__`
- `scripts/encryption_migrate.py`
  - Global `--config-dir PATH`; `_build_config_manager()` helper
- `tests/test_encryption_migrate_cli.py`
  - Three tests: config override, combined override, missing path

---

## 3. Documentation Updated

- `doc/dev/encryption_key_migration.md`
  - CLI usage lines include `[--config-dir PATH]`
  - Flag table documents `--config-dir`
  - Configuration and troubleshooting sections reference both path overrides

---

## 4. Configuration Summary

| CLI flag | Default | Effect |
| --- | --- | --- |
| `--config-dir PATH` | platform config dir | Load `settings.json` from `PATH` |
| `--data-dir PATH` | platform data dir | Load `environments.json` from `PATH` |

Flags are independent and composable for full staging restore.

---

## 5. Testing

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_encryption_migrate_cli.py -v
```

---

## 6. Related Tickets

- `PYPOST-530` — `--json` and `--data-dir` (predecessor)
- `PYPOST-487` — encryption migration CLI foundation
