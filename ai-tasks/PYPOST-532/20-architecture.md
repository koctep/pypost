# PYPOST-532: Architecture

## Approach

Add one pytest in `tests/test_encryption_migrate_cli.py` mirroring existing patterns:

| Reference test | Role |
| --- | --- |
| `test_cli_re_encrypt_dry_run` | CLI dry-run stdout shape (`dry_run: true`, kid histogram) |
| `test_cli_encrypt_plaintext` | Plain hidden fixture and `encrypt-plaintext` subcommand |
| `test_encrypt_plaintext_hidden_dry_run_projects_active_kid` | Service-layer projected inventory and file unchanged |

## Test flow

1. Patch user data/config dirs; enable encryption in settings.
2. Write `environments.json` with one plain hidden value.
3. Invoke `main(["encrypt-plaintext", "--dry-run", "--no-backup"])`.
4. Assert exit 0, projected inventory in stdout, plaintext value still on disk.

## Components

No production code changes. Test-only delta.
