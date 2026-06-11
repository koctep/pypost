# PYPOST-540: encryption_migrate CLI optional --config-dir

## Goals

Backup-restore workflows copy both `environments.json` and `settings.json` into staging
directories. PYPOST-530 added `--data-dir` for restored data, but settings still load from the
platform default config path via `ConfigManager`. Operators need to point the CLI at a copied
config directory without changing system paths.

## Programming Language

Python 3.10+

## User Stories

- As an operator restoring a backup into staging directories, I want `--config-dir` so verify,
  report, re-encrypt, and encrypt-plaintext use the restored `settings.json`.
- As an operator running against restored data and settings together, I want to pass both
  `--data-dir` and `--config-dir` in one command.
- As a maintainer, I want default behavior unchanged when the flag is omitted.

## Definition of Done

- Global `--config-dir PATH` selects the PyPost config directory (`settings.json` location).
- `ConfigManager` accepts an optional config directory override for headless tooling.
- Missing `--config-dir` path exits non-zero with a clear message (mirrors `--data-dir`).
- Tests cover config-dir override, combined data+config override, and missing path.
- Developer documentation updated in the encryption migration runbook.

## Out of Scope

- Overriding config paths in the desktop application UI.
- JSON schema changes or new CLI subcommands.
- Automatic discovery of config dir from data dir.

## Acceptance Criteria

1. `verify --config-dir PATH` loads encryption policy from `PATH/settings.json`.
2. `--config-dir` and `--data-dir` can be used together for full backup-restore staging.
3. Non-existent `--config-dir` exits code 1 with `config directory does not exist`.
4. Default (no flag) behavior matches pre-PYPOST-540 behavior.
5. All existing and new CLI tests pass.
