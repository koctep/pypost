# PYPOST-806: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | `make install` / manual install use `pip install -e ".[dev,otel]"`; lock files retained for audit |
| `doc/dev/testing.md` | Reproducible env table, Makefile test matrix, CI cache key includes `pyproject.toml` |
| `doc/dev/dependencies_audit.md` | Dev vs production install table reflects editable extras |
| `doc/dev/static_type_checking.md` | `make install` / `venv-test` reference `[dev]` extra |
| `README.md` | Manual install uses `pip install -e ".[dev,otel]"` |

## Key maintainer workflow

1. Edit direct pins in `requirements*.in` and mirror in `pyproject.toml`.
2. Regenerate locks with `make lock` / `make lock-dev` / `make lock-otel` as appropriate.
3. Local dev: `make install` (editable with dev + otel extras).
4. CVE scan unchanged: `make security-audit` after `make install`; scans `requirements.txt`.

## Cross-links

- PEP 621 metadata: PYPOST-785 (`doc/dev/setup.md` § Project metadata)
- pip-audit in dev extra: PYPOST-805 (`doc/dev/dependencies_audit.md` § CVE Scanning)
- Dev lock CI: PYPOST-804 (`doc/dev/testing.md` § CI lock verification)

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-806 end-to-end, tokens_used: 72000
