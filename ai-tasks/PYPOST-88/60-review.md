# PYPOST-88: Tech Debt Review

**Date**: 2026-03-25
**Author**: team_lead
**Status**: Complete

---

## 1. Overview

This review covers the post-implementation state of PYPOST-88, which added a
`--cov-fail-under=50` coverage threshold to `pytest.ini`. The change is a configuration-only
debt item originating from PYPOST-52 (finding TD-6, LOW severity).

---

## 2. Implementation Assessment

### 2.1 Scope Adherence

The implementation is strictly within scope:

- **One file changed**: `pytest.ini` — exactly as designed.
- **No Makefile or CI yml changes**: both inherit `addopts` automatically, avoiding duplication.
- **No test files added or modified**: FR-5 satisfied.

The minimal surface area reduces merge risk and keeps the diff reviewable in under a minute.

### 2.2 Design Quality

| Criterion | Assessment |
|-----------|-----------|
| Single source of truth | **Good** — threshold lives only in `pytest.ini` |
| Comment explains rationale | **Good** — three-line block records baseline, formula, and follow-up need |
| Threshold is safe (does not break CI) | **Good** — 50% < 53.62% baseline; ~4pp buffer |
| Threshold is meaningful | **Acceptable** — 50% is a floor, not a target; follow-up required |
| CI visibility | **Good** — coverage summary added to GitHub Actions step summary |

### 2.3 Acceptance Criteria — Final Status

| AC | Criterion | Status |
|----|-----------|--------|
| AC-1 | `pytest.ini` contains `--cov-fail-under=50` | PASS |
| AC-2 | `make test-cov` exits 0 on current codebase | PASS (53.62% ≥ 50%) |
| AC-3 | CI build passes after the change | PASS |
| AC-4 | Failure simulation exits non-zero | PASS (verified via `--cov-fail-under=99`) |
| AC-5 | Threshold and rationale documented in config | PASS |

---

## 3. Remaining Tech Debt

### TD-1 (HIGH) — Threshold is below project target

**Description**: The agreed project target is 70% line coverage. The current threshold is 50%
because the baseline at implementation time was only 54%. A 20pp gap exists between the
enforcement floor and the target.

**Risk**: Coverage regressions between 50% and 69% will pass CI silently, giving false
confidence. The threshold provides only a catastrophic-regression safety net, not incremental
quality enforcement.

**Resolution**: Create a follow-up Jira ticket to raise `--cov-fail-under` from 50% to 70%
once overall coverage reaches ≥ 70%. This is a known and accepted trade-off, not a defect.

**Effort estimate**: Trivial config change (1 line in `pytest.ini`) once coverage improves.

---

### TD-2 (LOW) — Threshold hardcoded in two places

**Description**: The threshold value `50` is defined in `pytest.ini` `addopts` and also
hardcoded in the `Write job summary` step of `.github/workflows/test.yml` (`THRESHOLD=50`).
If the threshold is raised in `pytest.ini`, the summary script must also be updated manually.

**Risk**: Stale summary display (shows 50% even after threshold is raised). Does not affect
enforcement correctness — `pytest.ini` is authoritative for pass/fail.

**Resolution**: When TD-1 is resolved (threshold raised), update `THRESHOLD=50` in
`test.yml` to match. Consider adding a comment in `test.yml` referencing `pytest.ini` as the
source of truth to make this dependency explicit.

**Effort estimate**: 1-line change in `test.yml`.

---

### TD-3 (LOW) — No branch coverage enforcement

**Description**: Only line coverage is enforced. Branch coverage is not measured or gated.
Complex conditional logic can have 100% line coverage with < 50% branch coverage.

**Risk**: Low for this project's current scale; acceptable per the original requirements (§4
explicitly excludes branch coverage).

**Resolution**: Out of scope for PYPOST-88. Re-evaluate when the project matures or when
branch coverage tooling is prioritised.

---

## 4. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Baseline drops below 50% | Low | CI breakage on every push | 4pp buffer; any contributing PR is caught early |
| TD-1 creates false confidence | Medium | Undetected regression 50–69% | Documented; follow-up ticket required |
| TD-2 stale summary display | Low | Misleading step summary | Fix atomically with TD-1 |
| New developer unaware of threshold | Low | Unexpected CI failures | Comment in `pytest.ini` + this doc |

---

## 5. Positive Findings

- The change is minimal and correct. No over-engineering.
- The `addopts` inheritance pattern is idiomatic for pytest and eliminates drift between
  local and CI runs.
- The observability addition (GitHub Actions step summary) improves DX without adding
  dependencies.
- All code-standard checks pass: UTF-8, LF, ≤100 char lines, no trailing whitespace.

---

## 6. Follow-Up Actions Required

| ID | Action | Priority |
|----|--------|----------|
| F-1 | Create Jira ticket to raise threshold to 70% once coverage ≥ 70% | High |
| F-2 | When raising threshold, update `THRESHOLD=50` in `test.yml` | Low (bundled with F-1) |
