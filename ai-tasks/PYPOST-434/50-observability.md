# PYPOST-434 — Observability

> Senior Engineer: senior_engineer
> Date: 2026-03-26

---

## 1. Application Runtime

**Scope:** No `pypost/` production code was modified.  No new log lines, metrics, or traces
were added.  Runtime observability of the desktop app is unchanged.

---

## 2. Test & CI Observability (Pre-Existing)

These mechanisms were already in place before PYPOST-434 and remain the source of truth
after the fix (see `.github/workflows/test.yml`):

- **Verbose pytest:** `addopts` includes `-v` and `--tb=short` (mirrored in CI).  Outcome:
  per-test lines and short tracebacks in the job log.
- **Live logs:** `log_cli = true` and `log_cli_level = WARNING` in `pytest.ini`.  Outcome:
  WARNING+ from tests and application code during runs.
- **Coverage:** `--cov=pypost`, XML report, and term-missing output.  Outcome: CI log plus
  `coverage.xml` artifact; `--cov-fail-under=50` enforced via `addopts`.
- **JUnit:** `--junit-xml=junit.xml` in the workflow.  Outcome: artifact
  `test-results-<python-version>` (PYPOST-89).
- **Run summary:** Step parses `junit.xml` into `$GITHUB_STEP_SUMMARY`.  Outcome: totals and
  failure/error/skip counts on the Actions summary page.
- **Matrix:** `fail-fast: false` so both Python legs always run and report.

---

## 3. Observability Gap This Ticket Closed

Before `pythonpath = .`, pytest failed at **collection** with
`ModuleNotFoundError: No module named 'pypost'`.  That broke the pipeline’s ability to
produce meaningful signals:

| Signal | Before fix | After fix |
|--------|------------|-----------|
| Per-test PASS/FAIL in log | Absent (no tests executed) | Restored |
| `junit.xml` with real `<testcase>` rows | Collection errors only | Restored (FR-1, AC-5) |
| `coverage.xml` | Often missing or empty of real run data | Restored (`pytest-cov` runs) |
| Job summary counts | Misleading (zero real tests) | Restored |
| `--cov-fail-under=50` | Not a useful signal (no coverage run) | Restored |

No new YAML or logging statements were required: **restoring imports unblocks the existing
instrumentation.**

---

## 4. Changes Made in Step 5

**None.**  Observability for this ticket is satisfied by documenting the above mapping and
confirming that the single `pytest.ini` change does not alter `log_cli` or `addopts`
behaviour beyond making the suite runnable.

---

## 5. Operator / Maintainer Guidance

| Question | Where to look |
|----------|----------------|
| Did CI run the full suite? | Job log: `PASSED` lines; summary shows non-zero test total |
| Did coverage meet the gate? | Job log, summary, and `coverage.xml` artifact |
| Collection still broken? | Would see `ModuleNotFoundError` at collection (should not recur) |
| Local parity with CI | From repo root: `pytest tests/` with no `PYTHONPATH` |

---

## 6. Follow-Ups (Out of Scope)

- The two pre-existing `DeprecationWarning` lines from Qt (`globalPos`) appear in pytest
  warnings summary; track separately if noise reduction is desired.
- A future ticket may add a `flake8` job or fix legacy flake8 debt (see
  `40-code-cleanup.md`); not part of observability for PYPOST-434.
