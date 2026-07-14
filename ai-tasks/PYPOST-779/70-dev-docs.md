# PYPOST-779: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | New § Dependency lock file — two-file layout, `make lock`, `make check-lock`, Dependabot workflow |
| `doc/dev/dependencies_audit.md` | Lock file status, R-P2-001 marked Done (PYPOST-779) |
| `doc/dev/testing.md` | CI cache key now hashes `requirements.in` + `requirements.txt` |

## Key maintainer workflow

1. Edit direct pins in `requirements.in`.
2. Run `make lock` (requires `uv`).
3. Commit both `requirements.in` and `requirements.txt`.
4. Run `make check` before opening PR.

## Cross-links

- Parent audit: `doc/dev/dependencies_audit.md`, `ai-tasks/PYPOST-691/30-audit-report.md`
- CVE scanning: unchanged `make security-audit` (PYPOST-778)
