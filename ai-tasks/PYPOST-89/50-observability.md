# Observability: PYPOST-89 — CI Pipeline for Tests

**Ticket**: PYPOST-89
**Author**: Senior Software Engineer
**Date**: 2026-03-25
**Artifact reviewed**: `.github/workflows/test.yml`

---

## 1. Existing Observability (Pre-This Step)

The following observability mechanisms were already present in the workflow after STEP 3/4:

| Mechanism | Where visible | Notes |
|---|---|---|
| `pytest -v` verbose output | CI job log | Every test name + PASS/FAIL printed |
| `--tb=short` tracebacks | CI job log | Concise failure context per test |
| `--cov-report=term-missing` | CI job log | Line-level coverage printed to stdout |
| `coverage.xml` artifact upload | Actions → Artifacts tab | `coverage-report-<py-version>` per matrix leg |
| `if: always()` on artifact step | Actions UI | Coverage available even after test failures |
| `fail-fast: false` matrix | Actions UI | Both Python legs always run and report |

---

## 2. Gaps Identified

| Gap | Impact |
|---|---|
| No JUnit XML test report | GitHub cannot surface per-test pass/fail annotations in PR checks or the "Test Results" tab; diagnosing failures requires opening raw logs |
| No job summary | The Actions run summary page shows no structured outcome; engineers must open each matrix leg's log to see counts |
| No JUnit artifact | Raw test result data is not downloadable for external tooling (coverage badges, dashboards, etc.) |

---

## 3. Observability Added

### 3.1 JUnit XML output (`--junit-xml=junit.xml`)

**Change**: Added `--junit-xml=junit.xml` to the `pytest` command.

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --tb=short --cov=pypost \
      --cov-report=term-missing \
      --cov-report=xml:coverage.xml \
      --junit-xml=junit.xml
```

**Effect**: pytest writes a machine-readable JUnit XML file after every run. GitHub Actions
parses this format natively — it powers the "Test Results" annotations on PR checks and the
"Tests" tab in the Actions run view. Individual test failures appear as inline annotations
directly on the diff, eliminating the need to read raw logs for initial triage.

### 3.2 Job Summary step

**Change**: Added a "Write job summary" step that posts a markdown table to
`$GITHUB_STEP_SUMMARY` after every run (including failures, via `if: always()`).

```yaml
- name: Write job summary
  if: always()
  run: |
    echo "## Test Results — Python ${{ matrix.python-version }}" >> "$GITHUB_STEP_SUMMARY"
    if [ -f junit.xml ]; then
      TOTAL=$(grep -oP 'tests="\K[0-9]+' junit.xml | head -1 || echo "?")
      FAILURES=$(grep -oP 'failures="\K[0-9]+' junit.xml | head -1 || echo "?")
      ERRORS=$(grep -oP 'errors="\K[0-9]+' junit.xml | head -1 || echo "?")
      SKIPPED=$(grep -oP 'skipped="\K[0-9]+' junit.xml | head -1 || echo "?")
      echo "| Metric | Count |" >> "$GITHUB_STEP_SUMMARY"
      echo "|---|---|" >> "$GITHUB_STEP_SUMMARY"
      echo "| Total | $TOTAL |" >> "$GITHUB_STEP_SUMMARY"
      echo "| Failures | $FAILURES |" >> "$GITHUB_STEP_SUMMARY"
      echo "| Errors | $ERRORS |" >> "$GITHUB_STEP_SUMMARY"
      echo "| Skipped | $SKIPPED |" >> "$GITHUB_STEP_SUMMARY"
    else
      echo "_junit.xml not found — pytest may have failed before producing output._" \
        >> "$GITHUB_STEP_SUMMARY"
    fi
```

**Effect**: The Actions run summary page (visible without opening any individual job log)
shows a table of total/failures/errors/skipped counts per Python version. Engineers get an
at-a-glance health indicator immediately after a run completes.

**Failure path**: If `junit.xml` is absent (e.g. pytest crashed before any test ran), the
summary prints a clear diagnostic message instead of silently failing.

### 3.3 JUnit artifact upload (`test-results-<python-version>`)

**Change**: Added an `Upload test results` step parallel to the existing coverage artifact step.

```yaml
- name: Upload test results
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-results-${{ matrix.python-version }}
    path: junit.xml
    if-no-files-found: warn
```

**Effect**: The raw JUnit XML is downloadable from the Actions run, enabling:
- External CI dashboards or badge generators to consume test data.
- Local re-inspection of a past run's test results without re-running.
- Future integration with tools such as `dorny/test-reporter` if richer PR annotations are
  desired.

---

## 4. Observability Coverage Matrix

| Requirement | Mechanism | Location |
|---|---|---|
| Know whether any test failed | Job status (red/green) + verbose log | Actions UI / job log |
| Know *which* tests failed | `--tb=short` in log + JUnit annotations on PR | Job log / PR checks |
| Know coverage % by module | `--cov-report=term-missing` | Job log |
| Download coverage data | `coverage-report-<py>` artifact | Actions → Artifacts |
| At-a-glance count summary | Job summary (§3.2) | Actions run summary page |
| Download raw test results | `test-results-<py>` artifact | Actions → Artifacts |
| Both Python versions always reported | `fail-fast: false` matrix | Actions UI |

---

## 5. What Was Not Added (and Why)

| Item | Rationale |
|---|---|
| `--cov-fail-under` threshold | Explicitly out of scope; tracked in PYPOST-88 |
| `dorny/test-reporter` third-party action | Adds external dependency; JUnit + native GitHub rendering is sufficient for now |
| Slack / email notifications | Not requested; no team notification infrastructure in scope |
| Concurrency cancellation group | Useful but not an observability concern; can be added in a separate cleanup ticket |
| Coverage badge | Requires a badge service; out of scope for this ticket |
