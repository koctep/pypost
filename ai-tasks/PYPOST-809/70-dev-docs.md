# PYPOST-809: Dev Docs Summary

## Updated files

| File | Changes |
| --- | --- |
| `doc/dev/licensing.md` | New § Transitive license inventory; updated distributor checklist and troubleshooting |
| `doc/dev/dependencies_audit.md` | Links to `LICENSES/transitive.csv`; R-P3-005 marked Done |
| `doc/dev/setup.md` | Dev lock table lists `pip-licenses` among direct dev deps |
| `doc/dev/testing.md` | New § CI transitive license inventory (PYPOST-809) |

## Key maintainer workflow

1. `pip-licenses` is a direct pin in `requirements-dev.in` (`pip-licenses>=5,<6`).
2. After editing `requirements.in`, run `make lock` then `make generate-license-inventory`.
3. Commit `requirements.txt`, `LICENSES/transitive.csv`, and any lock changes together.
4. Local verify: `make check-license-inventory` after `make install`.
5. CI `check-license-inventory` job runs the same `--check` path on every push/PR.

## Cross-links

- Parent audit finding: L-003 in `doc/dev/dependencies_audit.md`
- LGPL distributor guide: `doc/dev/licensing.md` (PYPOST-786)
- Dev lock workflow: `doc/dev/setup.md` § Development dependency lock file (PYPOST-780)
- CVE gate pattern: `doc/dev/testing.md` § CI dependency CVE scan (PYPOST-778)

## Worklog

role: execution, steps: 1-7, step_name: PYPOST-809 end-to-end, tokens_used: 95000
