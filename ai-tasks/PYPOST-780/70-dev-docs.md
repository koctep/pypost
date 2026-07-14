# PYPOST-780: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | New § Development dependency lock file — two-file layout, `make lock-dev`, `make check-lock-dev` |
| `doc/dev/dependencies_audit.md` | Dev deps now pinned; R-P2-002 marked Done (PYPOST-780) |
| `doc/dev/testing.md` | CI cache key includes dev lock files; install path references `requirements-dev.txt` |

## Key maintainer workflow

1. Edit direct dev pins in `requirements-dev.in`.
2. Run `make lock-dev` (requires `uv`).
3. Commit both `requirements-dev.in` and `requirements-dev.txt`.
4. Run `make check` before opening PR.

## Cross-links

- Production lock: `doc/dev/setup.md` § Dependency lock file (PYPOST-779)
- Parent audit: `doc/dev/dependencies_audit.md`, `ai-tasks/PYPOST-691/30-audit-report.md`
