# PYPOST-432: Architecture — Raise cov-fail-under to 60%

**Date**: 2026-06-11
**Status**: Implemented

---

## 1. Design Decision

Continue PYPOST-88 pattern: `pytest.ini` `addopts` is the enforcement source of truth.
Update the hardcoded `THRESHOLD` in `.github/workflows/test.yml` summary script in the same
change (resolves PYPOST-88 TD-2 for this increment).

---

## 2. Impacted Files

| File | Change |
|------|--------|
| `pytest.ini` | `--cov-fail-under=50` → `60`; update comment |
| `.github/workflows/test.yml` | `THRESHOLD=50` → `60` |
| `Makefile` | No change — inherits `addopts` |
| `doc/dev/testing.md` | Add coverage threshold policy section |

---

## 3. Verification Plan

1. `make test-cov` — expect exit 0, coverage ≥ 60%
2. `pytest tests/ --cov=pypost --cov-fail-under=99` — expect exit 2
3. `make test` — unaffected (no `--cov` flag)

---

## 4. Follow-Up

Create Jira Debt issue to raise threshold from 60% to 70% once the team agrees on timing.
