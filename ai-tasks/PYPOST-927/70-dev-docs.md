# PYPOST-927: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | Production lock § notes CI `check-lock` job on every push/PR |
| `doc/dev/testing.md` | CI lock verification § covers both `check-lock` and `check-lock-dev`; pip cache scope table includes `check-lock` |

## Key maintainer workflow

1. Edit direct production pins in `requirements.in`.
2. Run `make lock` (requires `uv`).
3. Commit both `requirements.in` and `requirements.txt`.
4. Run `make check` locally; CI `check-lock` job verifies lock freshness on push/PR.

## Cross-links

- Production lock introduction: `doc/dev/setup.md` § Dependency lock file (PYPOST-779)
- Dev lock CI: `doc/dev/setup.md` § Development dependency lock file (PYPOST-804)
- Contract test: `tests/test_ci_check_lock_job.py`
