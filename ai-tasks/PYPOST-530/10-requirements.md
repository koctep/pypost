# PYPOST-530: encryption_migrate CLI --json and --data-dir

## Goals

Operators and CI pipelines need machine-readable output from `encryption_migrate.py` and the ability
to point the CLI at a copied data directory during backup-restore workflows without changing
platform default paths.

## Programming Language

Python 3.10+

## User Stories

- As a CI job verifying encryption health, I want `--json` output so I can assert on inventory
  fields programmatically.
- As an operator restoring `environments.json` from backup into a staging directory, I want
  `--data-dir` so verify/report/re-encrypt run against the restored copy.
- As a maintainer, I want human-readable output unchanged when flags are omitted.

## Definition of Done

- Global `--json` emits a single JSON document on stdout for `verify`, `report`, `re-encrypt`, and
  `encrypt-plaintext`.
- Global `--data-dir PATH` selects the PyPost data directory (where `environments.json` lives).
- Exit codes unchanged (`0` success, `1` failure).
- Tests cover JSON shape and data-dir override.
- Developer documentation updated.

## Out of Scope

- JSON schema versioning or streaming output.
- Overriding config directory (`settings.json`); settings still load via `ConfigManager`.
- Data-quality error reporting for malformed hidden values (PYPOST-529).

## Acceptance Criteria

1. `report --json` prints valid JSON with `success`, `inventory`, and `command` fields; exit 0 on
   empty inventory.
2. `verify --json` includes `errors` when verification fails; exit 1.
3. `--data-dir` pointing at a directory with restored `environments.json` inventories that data
   without using the default user data path.
4. Missing `--data-dir` path exits non-zero with a clear message.
5. Default (non-JSON) output remains backward compatible.
