# Developer Documentation: PYPOST-89 — CI Pipeline for Tests

**Ticket**: PYPOST-89
**Author**: Team Lead
**Date**: 2026-03-25

---

## 1. Overview

This document describes the GitHub Actions CI pipeline introduced in PYPOST-89.

The pipeline runs the full pytest suite automatically on every push and pull request,
providing an automated quality gate that was previously absent from the project.

**Deliverable**: `.github/workflows/test.yml`

---

## 2. What the Pipeline Does

On every `push` or `pull_request` event (all branches), the pipeline:

1. Checks out the repository.
2. Sets up Python 3.11 and Python 3.13 in parallel matrix legs.
3. Upgrades `pip` and installs test tools (`pytest`, `pytest-cov`, `flake8`) and application
   dependencies (`requirements.txt`).
4. Sets `QT_QPA_PLATFORM=offscreen` so PySide6 Qt tests run headlessly on the Linux runner.
5. Runs `pytest tests/` with verbose output, short tracebacks, coverage reporting, JUnit XML
   output, and XML coverage report.
6. Writes a test-count summary table to the Actions run summary page.
7. Uploads `junit.xml` and `coverage.xml` as downloadable artifacts.

A non-zero `pytest` exit code (any test failure) fails the job and blocks merging (once
branch-protection rules are configured — see Section 7).

---

## 3. File Location

```
.github/
└── workflows/
    └── test.yml
```

---

## 4. Trigger Events

| Event | Branches |
|---|---|
| `push` | All branches (`**`) |
| `pull_request` | All branches (`**`) |

No path filters are applied — any file change triggers the full test suite.

---

## 5. Python Version Matrix

| Version | Status |
|---|---|
| 3.11 | Active — mirrors local `.venv/lib/python3.11` |
| 3.13 | Active — mirrors local `.venv/lib/python3.13` |

`fail-fast: false` ensures both legs always run to completion even if one fails.

---

## 6. Workflow Steps Reference

| Step | Action / Command | Purpose |
|---|---|---|
| Checkout | `actions/checkout@v4` | Fetches repository source |
| Setup Python | `actions/setup-python@v5` (with `cache: "pip"`) | Installs target Python + caches deps |
| Upgrade pip | `python -m pip install --upgrade pip` | Ensures current pip resolver |
| Install test tools | `pip install pytest pytest-cov flake8` | Test runner + coverage + linter |
| Install app deps | `pip install -r requirements.txt` | PySide6, requests, jinja2, pydantic, etc. |
| Run tests | `pytest tests/ -v --tb=short --cov=pypost ...` | Executes full test suite |
| Write job summary | bash + `$GITHUB_STEP_SUMMARY` | Posts count table to Actions summary page |
| Upload test results | `actions/upload-artifact@v4` | Saves `junit.xml` as `test-results-<py>` |
| Upload coverage | `actions/upload-artifact@v4` | Saves `coverage.xml` as `coverage-report-<py>` |

---

## 7. Viewing Results

### 7.1 Actions UI

Navigate to **Actions** tab → select a workflow run → select a matrix leg.

- **Green check / Red X**: Overall pass/fail status.
- **Job log**: Full `pytest -v` output with per-test PASS/FAIL lines, tracebacks, and
  `--cov-report=term-missing` coverage table.
- **Summary tab**: Markdown table showing Total / Failures / Errors / Skipped counts for
  each Python version.

### 7.2 Artifacts

Each run produces up to four downloadable artifacts (two per Python version):

| Artifact name | Contents | Use case |
|---|---|---|
| `test-results-3.11` | `junit.xml` | Machine-readable test results for tooling |
| `test-results-3.13` | `junit.xml` | Machine-readable test results for tooling |
| `coverage-report-3.11` | `coverage.xml` | XML coverage data for badges or dashboards |
| `coverage-report-3.13` | `coverage.xml` | XML coverage data for badges or dashboards |

Artifacts are available from the **Artifacts** section of the Actions run page.

### 7.3 PR Checks

On pull requests, GitHub surfaces the `pytest (Python 3.11)` and `pytest (Python 3.13)` status
checks in the PR merge box. Both must pass (once branch-protection rules are configured).

---

## 8. Environment Variables

| Variable | Value | Scope |
|---|---|---|
| `QT_QPA_PLATFORM` | `offscreen` | Job level (all steps) |

This is required for PySide6 Qt tests to run on a headless Linux runner. The `conftest.py`
also sets this via `os.environ.setdefault` as a defence-in-depth fallback.

---

## 9. Running Tests Locally

The CI pipeline mirrors the local `make test-cov` command:

```bash
# Equivalent local command (run from project root):
pytest tests/ -v --tb=short --cov=pypost --cov-report=term-missing

# With all CI flags (for exact parity):
QT_QPA_PLATFORM=offscreen pytest tests/ -v --tb=short --cov=pypost \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --junit-xml=junit.xml
```

If `QT_QPA_PLATFORM` is not set locally, `conftest.py` sets it automatically before any Qt
import occurs.

---

## 10. Modifying the Pipeline

### Adding a new Python version

Edit the `matrix.python-version` list in `test.yml`:

```yaml
matrix:
  python-version: ["3.11", "3.13", "3.14"]  # add here
```

### Changing the test command

Edit the `run:` block under the `Run tests` step. Ensure the `pytest.ini` `addopts` value
and the explicit flags in the YAML do not contradict each other.

### Adding a linting step

Add a new step after `Install test tools`:

```yaml
- name: Lint
  run: flake8 pypost/ tests/
```

`flake8` is already installed in the `Install test tools` step.

### Removing `flake8` (if linting is not planned)

Remove `flake8` from the `Install test tools` step:

```yaml
- name: Install test tools
  run: pip install pytest pytest-cov
```

---

## 11. Known Limitations & Follow-On Work

| Item | Detail | Tracking |
|---|---|---|
| No coverage threshold | `--cov-fail-under` not enforced; coverage drop does not fail CI | PYPOST-88 |
| No branch-protection rules | CI must be set as a required check in GitHub repo settings manually | Manual task |
| `flake8` installed but not run | Lint gate not yet active | Follow-on ticket |
| No concurrency cancellation | Rapid pushes queue multiple runs instead of cancelling superseded ones | CI hygiene ticket |
| Action versions not SHA-pinned | Minor supply-chain consideration; major-version pinning is current state | Security hardening ticket |

---

## 12. Related Tickets

| Ticket | Relationship |
|---|---|
| PYPOST-52 | Source review that identified the missing CI pipeline |
| PYPOST-88 | Follow-on: add `--cov-fail-under` coverage threshold |
| PYPOST-83–87 | Test-quality fixes that rely on CI being in place |
