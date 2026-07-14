# PYPOST-805: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/setup.md` | Dev lock table lists `pip-audit` among direct dev deps |
| `doc/dev/dependencies_audit.md` | CVE § notes pinned scanner in `requirements-dev.txt`; automation gap resolved |
| `doc/dev/testing.md` | New § CI dependency CVE scan (PYPOST-778, PYPOST-805) |

## Key maintainer workflow

1. `pip-audit` is a direct pin in `requirements-dev.in` (`pip-audit>=2,<4`).
2. After editing, run `make lock-dev` and commit `requirements-dev.in` + `requirements-dev.txt`.
3. Local CVE scan: `make install` then `make security-audit` (no inline pip install).
4. CI `security-audit` job installs `requirements-dev.txt` before running the scan.

## Cross-links

- CVE gate introduction: PYPOST-778 (`doc/dev/dependencies_audit.md` § CVE Scanning)
- Dev lock: `doc/dev/setup.md` § Development dependency lock file (PYPOST-780)
- Dev lock CI: `doc/dev/testing.md` § CI lock verification (PYPOST-804)

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-805 end-to-end, tokens_used: 85000
