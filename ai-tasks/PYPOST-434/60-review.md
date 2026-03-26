# Tech Debt Review: PYPOST-434 — GitHub Actions pytest import failure

**Ticket**: PYPOST-434
**Author**: Team Lead
**Date**: 2026-03-26

---

## 1. Summary

The change is a single configuration line (`pythonpath = .` in `pytest.ini`).  It aligns with
`10-requirements.md` and `20-architecture.md`, restores CI and local parity without
`PYTHONPATH`, and does not touch application code.

Overall tech debt introduced: **none**.  Pre-existing debt remains documented below for
follow-up tickets.

---

## 2. Strengths

| Strength | Detail |
|----------|--------|
| Minimal surface | One ini option; easy to review and revert |
| Official mechanism | pytest-supported `pythonpath` (≥ 7.0), not a `sys.path` hack |
| CI / local parity | Same config for `make test`, bare CLI, and GitHub Actions |
| No packaging churn | Avoids `pip install -e .` while the repo has no `pyproject.toml` |
| Observability restored | Existing junit, coverage, and job summary signals work again |

---

## 3. Tech Debt Items (Pre-Existing or Follow-Up)

### TD-1 (LOW) — `flake8` installed in CI but not run

**Description**: The workflow installs `flake8` but has no lint step.  Many violations exist
under `pypost/` and `tests/` (see `40-code-cleanup.md`).

**Recommendation**: Add a lint job or drop the unused install (see PYPOST-89 review TD-2).

**Tracking**: `doc/dev/tech-debt/PYPOST-434.md`

---

### TD-2 (LOW) — Qt `DeprecationWarning` in tests

**Description**: `QMouseEvent.globalPos()` deprecation in `pypost/ui/widgets/mixins.py`
surfaces as pytest warnings.

**Recommendation**: Migrate to the non-deprecated API in a dedicated UI hygiene ticket.

**Tracking**: Noted in `50-observability.md` §6.

---

### TD-3 (INFO) — pytest / Actions supply-chain hardening

**Description**: Unpinned pytest major version in CI; Actions use major tags not full SHAs.

**Recommendation**: Optional hardening pass; not required for this bugfix.

**Tracking**: Same theme as PYPOST-89 TD-1.

---

## 4. Acceptance Cross-Check

| AC (from requirements) | Status |
|------------------------|--------|
| AC-1 — collect without `PYTHONPATH` | Met locally (277 collected) |
| AC-2 / AC-3 — CI green on 3.11 / 3.13 | Expected after push; verify on Actions |
| AC-4 — `coverage.xml` artifacts | Unblocked once tests run |
| AC-5 / AC-6 — junit + coverage threshold | Unblocked |

---

## 5. Conclusion

**Approve** closure of implementation, cleanup, and observability steps.  No further code
changes are required on this ticket.  Remaining items are optional follow-ups, not blockers.
