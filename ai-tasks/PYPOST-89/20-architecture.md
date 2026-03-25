# Architecture: PYPOST-89 — CI Pipeline for Tests

**Ticket**: PYPOST-89
**Author**: Senior Software Engineer
**Date**: 2026-03-25
**Based on**: `ai-tasks/PYPOST-89/10-requirements.md`

---

## 1. Overview

A single GitHub Actions workflow file (`.github/workflows/test.yml`) will provide a
fully automated CI pipeline that runs the project's pytest suite on every push and pull
request. The pipeline mirrors the local `make test-cov` workflow, supports a Python
version matrix (3.11, 3.13), sets up the headless Qt environment, and uploads a coverage
report as a downloadable CI artifact.

No new source code is required. The deliverable is one YAML file and the creation of the
`.github/workflows/` directory.

---

## 2. File Location

```
.github/
└── workflows/
    └── test.yml          ← single workflow file (the only deliverable)
```

The `.github/` directory does not yet exist in the repository. It must be created.

---

## 3. Workflow Structure

### 3.1 Name and Trigger Events (FR-1)

```yaml
name: Tests

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]
```

- `push` with `branches: ["**"]` catches every branch including feature branches.
- `pull_request` with `branches: ["**"]` triggers on PRs targeting any base branch.
- No path filters — any file change triggers the test suite to prevent blind spots.

### 3.2 Job Definition

A single job named `test` runs on `ubuntu-latest` (FR: runner OS constraint).

```yaml
jobs:
  test:
    name: "pytest (Python ${{ matrix.python-version }})"
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.13"]
    env:
      QT_QPA_PLATFORM: offscreen
```

**`fail-fast: false`**: Both matrix legs run to completion even if one fails. This gives
developers full visibility into which Python version(s) are broken rather than stopping
at the first failure.

**`env.QT_QPA_PLATFORM: offscreen`** (FR-4): Set at the job level so it applies to every
step, including any that import Qt before `conftest.py` runs. The `conftest.py` also sets
this via `os.environ.setdefault`, providing defence-in-depth.

### 3.3 Steps

#### Step 1 — Checkout

```yaml
- uses: actions/checkout@v4
```

Standard full checkout. No `fetch-depth` override needed (no git history analysis).

#### Step 2 — Python Setup (FR-2, FR-3)

```yaml
- uses: actions/setup-python@v5
  with:
    python-version: ${{ matrix.python-version }}
    cache: "pip"
```

`cache: "pip"` enables GitHub's built-in pip dependency cache keyed on
`requirements.txt`. This is the only caching used (per the non-goals constraint).

#### Step 3 — Upgrade pip (FR-3)

```yaml
- run: python -m pip install --upgrade pip
```

Ensures a current pip before any package installation, matching the Makefile's
`ensurepip --upgrade` + `pip install --upgrade pip` pattern.

#### Step 4 — Install Test Tools (FR-3)

```yaml
- run: pip install pytest pytest-cov flake8
```

Installs the exact tools listed in FR-3 and used by `make venv-test`.
`flake8` is included per FR-3 even though linting is not gated in this ticket.

#### Step 5 — Install Application Dependencies (FR-3)

```yaml
- run: pip install -r requirements.txt
```

Installs `PySide6`, `requests`, `jinja2`, `pydantic>=2.0`, and other runtime deps
from `requirements.txt`. This must run after pip upgrade to avoid resolver issues
with large packages like PySide6.

#### Step 6 — Run Tests (FR-5, FR-6)

```yaml
- name: Run tests
  run: |
    pytest tests/ -v --tb=short --cov=pypost \
      --cov-report=term-missing \
      --cov-report=xml:coverage.xml
```

- The command mirrors `make test-cov` exactly (FR-5), minus the HTML report.
- `--cov-report=xml:coverage.xml` is added alongside `term-missing` to produce a
  machine-readable file for the artifact upload step (FR-7). This is additive and does
  not conflict with FR-5.
- `pytest.ini` already injects `-v --tb=short` via `addopts`; the explicit flags in the
  command are harmless duplicates that document intent clearly in the YAML.
- A non-zero exit code from pytest automatically fails the job (FR-6).

#### Step 7 — Upload Coverage Artifact (FR-7)

```yaml
- name: Upload coverage report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: coverage-report-${{ matrix.python-version }}
    path: coverage.xml
    if-no-files-found: warn
```

- `if: always()` ensures the artifact upload runs even when tests fail, making
  partial coverage data available for diagnosis.
- Artifact name pattern `coverage-report-<python-version>` satisfies FR-7 exactly.
- `if-no-files-found: warn` prevents a missing XML from blocking the artifact step
  while still surfacing the problem in the job log.

---

## 4. Complete Workflow YAML (Reference)

```yaml
name: Tests

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  test:
    name: "pytest (Python ${{ matrix.python-version }})"
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.13"]
    env:
      QT_QPA_PLATFORM: offscreen

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: "pip"

      - name: Upgrade pip
        run: python -m pip install --upgrade pip

      - name: Install test tools
        run: pip install pytest pytest-cov flake8

      - name: Install application dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short --cov=pypost \
            --cov-report=term-missing \
            --cov-report=xml:coverage.xml

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report-${{ matrix.python-version }}
          path: coverage.xml
          if-no-files-found: warn
```

---

## 5. Design Decisions & Rationale

| Decision | Rationale |
|---|---|
| Single job `test` | Pipeline is simple; parallelism within the matrix is sufficient |
| `fail-fast: false` | See both Python legs even when one breaks |
| Job-level `env` for Qt | Guards against Qt imports before `conftest.py` fires |
| `cache: "pip"` in setup-python | Aligns with non-goals: pip cache only, nothing else |
| `--cov-report=xml` added | Required to produce an uploadable file; does not conflict with FR-5 |
| `if: always()` on upload | Partial coverage visible even after test failures |
| No `--cov-fail-under` | Explicitly out of scope; tracked in PYPOST-88 |
| `actions/checkout@v4` | Latest stable major version at time of writing |
| `actions/setup-python@v5` | Latest stable major version with native pip caching |
| `actions/upload-artifact@v4` | Latest stable major version |

---

## 6. Acceptance Criteria Mapping

| AC | How the design satisfies it |
|---|---|
| AC-1: valid YAML | Section 4 is valid GH Actions YAML; junior will validate with `yamllint` |
| AC-2: push triggers both versions | `on.push` + matrix covers both 3.11 and 3.13 |
| AC-3: PR triggers both versions | `on.pull_request` + matrix covers both |
| AC-4: 37+ tests pass | All test tools + app deps installed; no test skips added |
| AC-5: deliberate failure blocks CI | pytest non-zero exit propagates as job failure |
| AC-6: `QT_QPA_PLATFORM=offscreen` | Set at job `env` level, applies to all steps |
| AC-7: coverage in log | `--cov-report=term-missing` prints to the CI job log |

---

## 7. Out of Scope

- `--cov-fail-under` threshold: tracked in PYPOST-88.
- Linting gate: out of scope per non-goals.
- Deployment or release automation.
- Docker-based runners.
- Branch-protection rule configuration (manual GitHub repo setting).

---

## 8. Implementation Notes for Junior Engineer

1. Create `.github/workflows/` directory.
2. Create `.github/workflows/test.yml` using the YAML in Section 4 verbatim.
3. Verify line lengths ≤ 100 characters (all lines in the YAML are well within limit).
4. No changes to existing source files are required.
5. Push to a feature branch and confirm both matrix legs appear in the Actions tab.
