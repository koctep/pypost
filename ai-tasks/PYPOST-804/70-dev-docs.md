# PYPOST-804: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | Dev lock § notes CI `check-lock-dev` job on every push/PR |
| `doc/dev/testing.md` | New § CI lock verification (PYPOST-804); pip cache scope table includes `check-lock-dev` |

## Key maintainer workflow

1. Edit direct dev pins in `requirements-dev.in`.
2. Run `make lock-dev` (requires `uv`).
3. Commit both `requirements-dev.in` and `requirements-dev.txt`.
4. Run `make check` locally; CI `check-lock-dev` job verifies lock freshness on push/PR.

## Cross-links

- Dev lock introduction: `doc/dev/setup.md` § Development dependency lock file (PYPOST-780)
- Production lock: `doc/dev/setup.md` § Dependency lock file (PYPOST-779)
- CVE scanning: unchanged `security-audit` job (PYPOST-778)
