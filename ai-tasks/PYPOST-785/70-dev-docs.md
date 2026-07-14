# PYPOST-785: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | New § Project metadata (`pyproject.toml`) — PEP 621 layout, optional extras |
| `doc/dev/dependencies_audit.md` | `pyproject.toml` row updated; R-P3-001 marked Done (PYPOST-785) |

## Key maintainer workflow

1. Edit direct production pins in `requirements.in` (and mirror in `pyproject.toml`
   `[project].dependencies`).
2. Edit dev pins in `requirements-dev.in` (and mirror in `pyproject.toml` `dev` extra).
3. Run `make lock` / `make lock-dev` after `.in` changes.
4. Run `make check` — `tests/test_pyproject.py` fails on metadata drift.

## Cross-links

- Production lock: `doc/dev/setup.md` § Dependency lock file (PYPOST-779)
- Dev lock: `doc/dev/setup.md` § Development dependency lock file (PYPOST-780)
- Parent audit: `doc/dev/dependencies_audit.md`, `ai-tasks/PYPOST-691/30-audit-report.md`
