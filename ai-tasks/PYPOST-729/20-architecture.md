# PYPOST-729: Architecture

## Approach

Each violation is an isolated, single-file change with no cross-cutting concerns:

| Violation | Fix |
|-----------|-----|
| F841 `error_prefix` | Delete line 104 in `encryption_migration.py` |
| F401 `MigrationReport` | Remove from import on line 10 in `encryption_migration_worker.py` |
| W391 trailing newline | Remove trailing blank line at EOF in `mixins.py` |
| E501 long line | Wrap `__init__` signature at 100 chars in `request_editor.py` |

No refactoring, no new abstractions — each fix is the minimum change to satisfy flake8.
