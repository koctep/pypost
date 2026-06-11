# PYPOST-432: Requirements — Raise cov-fail-under toward 70%

**Date**: 2026-06-11
**Source**: PYPOST-88 follow-up (TD-1); Sprint 134 backlog TD-7
**Prerequisite**: PYPOST-88 merged (`df542ac`)

---

## 1. Background

PYPOST-88 established `--cov-fail-under=50` in `pytest.ini` when baseline coverage was 54%.
The project long-term target is 70% line coverage. Coverage has since grown substantially.

---

## 2. Problem Statement

The 50% enforcement floor no longer reflects actual coverage (~86%). Regressions between 50%
and 60% pass CI silently, weakening the protection added by PYPOST-88.

---

## 3. Goals

1. Audit current line coverage via `make test-cov`.
2. Raise `--cov-fail-under` incrementally toward the 70% project target.
3. Keep `pytest.ini` and `.github/workflows/test.yml` summary `THRESHOLD` in sync.
4. Confirm `make test-cov` exits 0 after the change.

---

## 4. Out of Scope

- Raising to the full 70% target in this ticket (incremental step only).
- Adding new tests to increase coverage.
- Branch coverage enforcement.

---

## 5. Baseline Audit

```
TOTAL   6687    920    86%
937 passed in 48.94s
Required test coverage of 50% reached. Total coverage: 86.24%
```

**Baseline**: **86.24%**

---

## 6. Threshold Selection

| Parameter | Value |
|-----------|-------|
| Previous threshold | 50% |
| Baseline (2026-06-11) | 86.24% |
| Increment step | +10pp |
| **New threshold** | **60%** |
| Buffer above threshold | ~26pp |
| Project target | 70% |

Formula considered: `floor(86/5)*5 = 85` — too aggressive for one sprint step. Incremental
raise to 60% (+10pp from 50%) matches task guidance (e.g. 55, 60).

---

## 7. Acceptance Criteria

| AC | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | `pytest.ini` contains `--cov-fail-under=60` | `grep cov-fail-under pytest.ini` |
| AC-2 | `test.yml` summary `THRESHOLD=60` | `grep THRESHOLD test.yml` |
| AC-3 | `make test-cov` exits 0 | Local run |
| AC-4 | Failure simulation exits non-zero | `--cov-fail-under=99` |
| AC-5 | Comment documents baseline and rationale | Visual review |
