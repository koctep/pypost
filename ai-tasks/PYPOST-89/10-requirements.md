# Requirements: PYPOST-89 — CI Pipeline for Tests

**Ticket**: PYPOST-89
**Type**: Debt
**Priority**: Medium (highest-priority item in Sprint 134 Wave 2)
**Source**: ai-tasks/PYPOST-52/60-review.md (finding #7)
**Date**: 2026-03-25

---

## Problem Statement

The project has a working `pytest.ini` and `make test-cov` local test setup, but no automated
CI pipeline. Tests run only on developer machines. There is no quality gate that validates tests
on push or pull request, meaning regressions can land in the repository undetected.

---

## Goals

1. Run the full test suite automatically on every push and every pull request.
2. Fail the CI build if any test fails (non-zero pytest exit code blocks merge).
3. Produce a coverage report as a CI artifact for visibility.
4. Support the Python versions the project targets.
5. Mirror the local `make test-cov` workflow as closely as possible to avoid CI/local divergence.

---

## Non-Goals

- Enforcing a `--cov-fail-under` threshold (tracked separately in PYPOST-88).
- Linting / flake8 gate (out of scope for this ticket).
- Deployment or release automation.
- Caching beyond pip dependency caching (keep the workflow simple for now).

---

## Functional Requirements

### FR-1: Trigger Events

The workflow MUST run on:

| Event | Branches |
|---|---|
| `push` | all branches |
| `pull_request` | all branches targeting any base |

Rationale: catching regressions early on feature branches is more valuable than gating only
`main`.

### FR-2: Python Version Matrix

The workflow MUST test against the Python versions the project uses locally:

- **3.11**
- **3.13**

Both versions are present in `.venv/lib/` and are the project's active runtimes.

### FR-3: Environment Setup

The runner MUST:

1. Check out the repository.
2. Set up the target Python version.
3. Upgrade `pip`.
4. Install test dependencies: `pytest`, `pytest-cov`, `flake8`.
5. Install application dependencies from `requirements.txt`.

### FR-4: Qt Headless Environment

PySide6 (Qt) requires a virtual display for tests. The runner MUST set:

```
QT_QPA_PLATFORM=offscreen
```

before invoking `pytest`. The `conftest.py` already applies this via
`os.environ.setdefault`, but it MUST also be set at the workflow environment level to
guard against any test that imports Qt before `conftest.py` runs.

### FR-5: Test Command

The workflow MUST execute:

```
pytest tests/ -v --tb=short --cov=pypost --cov-report=term-missing
```

This matches the local `make test-cov` target (minus the HTML report, which is
not useful in CI terminal output).

### FR-6: Pass / Fail Criteria

- Any test failure (non-zero `pytest` exit code) MUST fail the CI job.
- A missing or broken dependency install step MUST fail the CI job.
- The coverage report is informational only (no minimum threshold — see PYPOST-88).

### FR-7: Coverage Report Upload

The workflow SHOULD upload the coverage report as a CI artifact so it can be inspected
without re-running locally. Artifact name: `coverage-report-<python-version>`.

---

## Constraints

| Constraint | Detail |
|---|---|
| CI platform | GitHub Actions (project is hosted on GitHub) |
| Workflow file location | `.github/workflows/test.yml` |
| Runner OS | `ubuntu-latest` |
| No secrets required | All dependencies are public; no API keys needed |
| Line length | ≤ 100 characters (CLAUDE.md rule) |

---

## Acceptance Criteria

1. `.github/workflows/test.yml` exists and is syntactically valid GitHub Actions YAML.
2. A push to any branch triggers the workflow on both Python 3.11 and 3.13.
3. A pull request triggers the workflow on both Python 3.11 and 3.13.
4. All 37+ existing tests pass in the CI environment.
5. A deliberate test failure (e.g. `assert False`) causes the CI job to report failure.
6. The `QT_QPA_PLATFORM=offscreen` variable is set so PySide6 tests run headlessly.
7. Coverage output (term-missing) is visible in the CI job log.

---

## Dependencies / Related Tickets

| Ticket | Relationship |
|---|---|
| PYPOST-52 | Source review that identified this gap |
| PYPOST-88 | Follow-on: add `--cov-fail-under` threshold to the same workflow |
| PYPOST-83–87 | Test-quality fixes that rely on CI being in place to enforce them |
