# PYPOST-540: encryption_migrate CLI optional --config-dir

## Programming Language

Python 3.10+

## Research

### Current state (post PYPOST-530)

- `scripts/encryption_migrate.py` accepts global `--data-dir` and passes it to
  `StorageManager(data_dir=...)`.
- Settings load via `ConfigManager().load_config()` with no path override.
- `ConfigManager.__init__` always resolves `user_config_dir(app_name, app_author)`.
- Tests monkeypatch `user_config_dir` for isolation; `--data-dir` tests use alternate data paths
  while settings remain on the patched default config dir.

### Gap

Backup-restore staging often copies both trees. Without `--config-dir`, operators must either
symlink restored settings into the platform config path or temporarily replace live settings —
unsafe and awkward.

## Implementation Plan

1. **Extend `ConfigManager`** — add optional keyword-only `config_dir: Path | str | None`.
   When set, use it instead of `user_config_dir`. Preserve existing call sites (default `None`).

2. **Extend CLI global options** — add `--config-dir PATH` alongside `--data-dir` on the root
   parser and each subcommand (via `_add_global_options`).

3. **Add `_build_config_manager(config_dir)`** — mirror `_build_storage`:
   - `None` → `ConfigManager()` (default paths).
   - Resolve path, validate directory exists, exit 1 with message if not.
   - Return `ConfigManager(config_dir=resolved)`.

4. **Wire `main()`** — replace `ConfigManager().load_config()` with
   `_build_config_manager(args.config_dir).load_config()`.

5. **Logging** — include `config_dir` in `encryption_migrate_command_started` INFO log.

6. **Tests** — three cases:
   - Config override alone (encryption enabled in alt config, default config disabled).
   - Combined `--config-dir` + `--data-dir`.
   - Missing config dir exits with clear error.

7. **Docs** — update CLI flag table and troubleshooting in `doc/dev/encryption_key_migration.md`.

## Component Changes

| Component | Change |
| --- | --- |
| `pypost/core/config_manager.py` | Optional `config_dir` constructor parameter |
| `scripts/encryption_migrate.py` | `--config-dir`, `_build_config_manager`, log field |
| `tests/test_encryption_migrate_cli.py` | Three new tests |
| `doc/dev/encryption_key_migration.md` | Flag docs and troubleshooting |

## Risks

- **Low**: Constructor signature change is backward-compatible (keyword-only, default None).
- **Low**: Creating config dir on missing path is avoided by pre-flight `is_dir()` check in CLI.
