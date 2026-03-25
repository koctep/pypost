# PYPOST-88: Developer Documentation — Coverage Threshold Enforcement

**Date**: 2026-03-25
**Author**: team_lead

---

## 1. What Was Done

PYPOST-88 added a minimum line-coverage threshold to the pytest configuration. Every test run
(local and CI) now fails with a non-zero exit if the `pypost` package's line coverage falls
below **50%**.

This addresses the debt item originally identified in PYPOST-52 (TD-6): coverage data was
being collected but never enforced, so a refactoring regression that silently deleted coverage
would pass CI.

---

## 2. Files Changed

| File | Change |
|------|--------|
| `pytest.ini` | Added `--cov-fail-under=50` to `addopts`; added explanatory comment |
| `.github/workflows/test.yml` | Added coverage summary block to `Write job summary` step |

---

## 3. How the Threshold Works

### 3.1 Configuration

The threshold is set in `pytest.ini`:

```ini
[pytest]
# --cov-fail-under: enforces minimum line coverage for `pypost`.
# Threshold set to 50% (baseline 54%, floor(54/5)*5=50, buffer of one 5pp step).
# Baseline is below the project target of 70%; raise threshold in follow-up PYPOST-88-raise.
addopts = -v --tb=short --cov-fail-under=50
```

Because `--cov-fail-under` is in `addopts`, it is automatically applied to every `pytest`
invocation that activates coverage. You do not need to pass it explicitly on the command line.

### 3.2 When enforcement is active

The `--cov-fail-under` check is only triggered when pytest-cov is active, i.e. when a
`--cov=<source>` flag is provided. This means:

| Command | Coverage enforced? |
|---------|-------------------|
| `make test-cov` | **Yes** — passes `--cov=pypost` |
| `make test` | **No** — no `--cov` flag; fast unit run |
| `pytest tests/` (bare) | **No** — no `--cov` flag |
| `pytest tests/ --cov=pypost` | **Yes** |
| CI `Run tests` step | **Yes** — passes `--cov=pypost` |

### 3.3 Failure output

When coverage is below the threshold, pytest-cov prints:

```
FAIL Required test coverage of 50% not reached. Total coverage: XX%
```

and exits with code **2**. The CI job is marked as failed.

When coverage meets or exceeds the threshold:

```
Required test coverage of 50% reached. Total coverage: XX%
```

Exit code is 0 (assuming no test failures).

---

## 4. CI Visibility

The `Write job summary` step in `.github/workflows/test.yml` appends a coverage table to the
GitHub Actions job summary page:

```
## Coverage — Python 3.11

| Metric                       | Value   |
|------------------------------|---------|
| Line coverage                | 53.6%   |
| Threshold (--cov-fail-under) | 50%     |
| Status                       | ✅ PASS |
```

This is visible on the job overview without expanding any logs. The `coverage.xml` artifact
(uploaded on every run) provides full per-file breakdown for deeper investigation.

---

## 5. Changing the Threshold

To raise the threshold (e.g. from 50% to 70% as per the project target):

1. Verify the current coverage is at or above the new threshold:
   ```bash
   make test-cov
   ```
   Look for `TOTAL ... XX%` in the output.

2. Edit `pytest.ini` — update the `addopts` line and the comment:
   ```ini
   # Threshold set to 70% (project target reached).
   addopts = -v --tb=short --cov-fail-under=70
   ```

3. Edit `.github/workflows/test.yml` — update the hardcoded `THRESHOLD` in the summary
   script to match:
   ```bash
   THRESHOLD=70
   ```

4. Run `make test-cov` locally to confirm exit 0, then open a PR.

> **Note**: Steps 2 and 3 must be done together. The `THRESHOLD` value in `test.yml` is used
> only for the visual summary; it does not affect enforcement. But keeping them in sync
> prevents a misleading summary display.

---

## 6. Threshold Selection Rationale

| Parameter | Value |
|-----------|-------|
| Baseline at implementation (2026-03-25) | 54% |
| Formula applied | `floor(54 / 5) * 5 = 50` |
| Buffer above threshold | ~4pp (54% − 50%) |
| Project long-term target | 70% |
| Follow-up required | Yes — raise to 70% once coverage ≥ 70% |

The 50% threshold was chosen to be safe (does not immediately break CI) while providing
meaningful protection against catastrophic regressions. It is a floor, not a target.

---

## 7. Related Tickets

| Ticket | Description |
|--------|-------------|
| PYPOST-52 | Original tech debt review that identified the missing threshold (TD-6) |
| PYPOST-89 | CI pipeline that this ticket builds on (merged at `9f0a52d`) |
| PYPOST-88-raise (TBD) | Follow-up to raise threshold from 50% to 70% |
