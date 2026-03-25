# PYPOST-88: Architecture — No pytest cov-fail-under threshold

**Date**: 2026-03-25
**Author**: senior_engineer
**Status**: Ready for team_lead review

---

## 1. Baseline Coverage Audit

Per §5 of the requirements, `make test-cov` was executed before committing to a threshold:

```
TOTAL   3305   1533   54%
195 passed in 3.98s
```

**Baseline**: **54%**

Threshold formula (baseline < 70%): `floor(54 / 5) * 5 = 50`

**Chosen threshold**: **50%**

Since 50% < 70%, a follow-up ticket must be created to raise the threshold to 70% once
coverage improves. This is tracked as an explicit action item at the end of this document.

---

## 2. Design Decision: Single Source of Truth via `pytest.ini`

### Chosen approach: FR-3 (pytest.ini `addopts`)

`--cov-fail-under=50` will be added to the `addopts` line in `pytest.ini`. Both the Makefile
`test-cov` target and the GitHub Actions `Run tests` step invoke `pytest` normally and
therefore inherit `addopts` automatically — no duplication in Makefile or CI yml is needed.

**Why not duplicate in Makefile + CI?**
- Duplication creates drift risk: changing the threshold in one place but not the other.
- `pytest.ini` is already the config centre for `-v --tb=short`, log settings, etc.
- FR-3 explicitly prefers this approach and permits omitting the flag elsewhere when
  `pytest.ini` is the source.

### Safety: `make test` (no coverage)

The plain `test` target in the Makefile does not pass `--cov=pypost`. When no `--cov` source
is specified, pytest-cov does not initialise its plugin and `--cov-fail-under` has no effect.
The `test` target will continue to work without coverage overhead.

---

## 3. Impacted Files

| File | Change |
|------|--------|
| `pytest.ini` | Append `--cov-fail-under=50` to the existing `addopts` value |
| `Makefile` | **No change** — inherits from `addopts` |
| `.github/workflows/test.yml` | **No change** — inherits from `addopts` |

---

## 4. Exact Change

### `pytest.ini` — before

```ini
[pytest]
addopts = -v --tb=short
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
log_date_format = %H:%M:%S
```

### `pytest.ini` — after

```ini
[pytest]
# --cov-fail-under: enforces minimum line coverage for `pypost`.
# Threshold set to 50% (baseline 54%, floor(54/5)*5=50, buffer of one 5pp step).
# Baseline is below the project target of 70%; raise threshold in follow-up PYPOST-88-raise.
addopts = -v --tb=short --cov-fail-under=50
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
log_date_format = %H:%M:%S
```

---

## 5. Verification Plan

| AC | Verification step |
|----|-------------------|
| AC-1 | `grep cov-fail-under pytest.ini` outputs the threshold line |
| AC-2 | `make test-cov` exits 0 on the current codebase (baseline 54% ≥ 50%) |
| AC-3 | CI build passes after the change (same condition) |
| AC-4 | `pytest tests/ --cov=nonexistent` exits non-zero (total 0% < 50%) |
| AC-5 | Comment in `pytest.ini` records threshold value and rationale |

---

## 6. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Baseline fluctuates slightly between runs (e.g. 53%) | Low | 50% threshold gives a 4pp buffer above the rounded threshold |
| Future test deletions silently drop coverage below 50% | Low after this change | Enforcement catches it on every push |
| `--cov-fail-under` interacts badly with `make test` (no `--cov`) | Very low | pytest-cov skips fail-under check when no coverage plugin is active |

---

## 7. Follow-Up Actions

- **Create follow-up Jira ticket** (PYPOST-88-raise or new task): Raise `--cov-fail-under`
  from 50% to 70% once test coverage improves. Baseline must reach ≥ 70% before the ticket
  can be closed.

---

## 8. Non-Goals (explicitly excluded)

- Branch coverage (`--cov-branch`) — out of scope per §4 of requirements.
- Per-module exclusion rules — out of scope per §4.
- Adding new tests — out of scope per §4, FR-5.
- Raising threshold above 50% in this ticket — follow-up only.
