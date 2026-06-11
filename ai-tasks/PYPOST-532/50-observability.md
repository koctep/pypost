# PYPOST-532: Observability

## Logging

No changes. Dry-run path already logs `encryption_migration_dry_run_completed` at service layer;
CLI test uses capsys and does not assert on stderr logs.

## Metrics

No new metrics; test-only task.

## Test as observability contract

The CLI test documents expected human-readable dry-run output for operators comparing
`re-encrypt` and `encrypt-plaintext` commands.
