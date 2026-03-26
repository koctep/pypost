# PYPOST-434 Requirements — GitHub Actions: pytest job failed

## 1. Problem Statement

The GitHub Actions CI pipeline (`.github/workflows/test.yml`) fails on every push
because pytest cannot import the `pypost` package.  All 26 test-module imports raise:

```
ModuleNotFoundError: No module named 'pypost'
```

causing 26 collection errors and zero tests executed.  The root cause is a missing
`sys.path` entry: the project root (`/home/src` in the repo) is not added to Python's
module search path when pytest is invoked without an explicit `PYTHONPATH`.

### Evidence

| Observation | Value |
|---|---|
| CI run | `23586633184` (commit `a397a18`, PYPOST-420) |
| Failing jobs | `pytest (Python 3.11)` **and** `pytest (Python 3.13)` |
| Failing step | `Run tests` |
| `junit.xml` size | ~1 764 bytes (consistent with ~26 collection-error entries, zero test cases) |
| `coverage.xml` | **not generated** (no tests ran, `pytest-cov` never collected data) |
| Local reproduction | `pytest tests/` without `PYTHONPATH` → identical `ModuleNotFoundError` |
| Local passing run | `PYTHONPATH=/home/src pytest tests/` → **277 passed in ~6–8 s** |

### Why the module is not found

`pypost` is a plain directory package at `<repo-root>/pypost/`.  The project has no
`setup.py`, `setup.cfg`, or `pyproject.toml`, so the package is never installed into
the virtual environment.  pytest's default import mode (`prepend` / `importlib`) does
**not** unconditionally insert the repo root into `sys.path` unless one of the following
is present:

* `pythonpath = .` in `pytest.ini` / `pyproject.toml`, **or**
* `PYTHONPATH` set in the calling shell, **or**
* the package installed via `pip install -e .`

None of these conditions exists in the current CI workflow or `pytest.ini`.

### Why the bug was not caught earlier

The GitHub Actions workflow was added in commit `9f0a52d` (PYPOST-89, 2026-03-25) and
all prior commits were pushed to GitHub in a single batch with `a397a18` as HEAD on
2026-03-26.  That first push triggered the first — and only — CI run, which immediately
failed.  Local development used an environment with `PYTHONPATH` set (or pytest run from
within the package path), masking the issue.

---

## 2. Scope

This ticket covers only making the existing test suite runnable in CI.  It does **not**
cover adding new tests, changing production code, or refactoring the project layout.

---

## 3. Functional Requirements

### FR-1 — pytest discovers and runs all tests in CI

When the CI workflow executes `pytest tests/ ...` on any push to any branch:

* **All 270+ tests must be collected** without `ModuleNotFoundError`.
* The `Run tests` step must exit `0` when all tests pass and coverage ≥ 50 %.
* `junit.xml` must contain individual `<testcase>` entries for every test.
* `coverage.xml` must be generated and uploaded as an artifact.

### FR-2 — Fix is version-portable

The fix must work for **both Python 3.11 and Python 3.13** as specified in the CI
matrix, and for any Python 3.10 + version that may be added in the future.

### FR-3 — Fix is minimal and non-breaking

The change must not:

* Alter production source code in `pypost/`.
* Require installing `pypost` as a distribution package (`pip install -e .`).
* Break local development workflows (running pytest from the repo root with no extra env).

### FR-4 — Preferred fix: `pythonpath = .` in `pytest.ini`

The recommended solution, endorsed by the pytest project since v 7.0, is to add:

```ini
[pytest]
pythonpath = .
```

This single line instructs pytest to prepend the current working directory (the repo
root) to `sys.path` before collecting tests, making `import pypost` succeed without any
shell-level `PYTHONPATH` manipulation.

This satisfies FR-1 through FR-3: it is Python-version-agnostic, requires no
workflow changes, and is invisible to users who already set `PYTHONPATH` (the directory
is only prepended once even if already present).

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-1 | The CI `Run tests` step must complete in under 5 minutes on `ubuntu-latest`. |
| NFR-2 | The fix must not introduce new warnings in the pytest output. |
| NFR-3 | All 270+ existing tests must continue to pass after the fix. |
| NFR-4 | Line coverage must remain ≥ 50 % (current baseline: ~53.6 %). |

---

## 5. Acceptance Criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-1 | `pytest tests/` (no PYTHONPATH) collects all tests without errors. | `pytest tests/ --collect-only -q` exits 0 with ≥ 270 items collected |
| AC-2 | All tests pass in CI on Python 3.11. | GitHub Actions job `pytest (Python 3.11)` → conclusion `success` |
| AC-3 | All tests pass in CI on Python 3.13. | GitHub Actions job `pytest (Python 3.13)` → conclusion `success` |
| AC-4 | `coverage.xml` artifact is uploaded for both Python versions. | Artifact `coverage-report-3.11` and `coverage-report-3.13` present in the run |
| AC-5 | `junit.xml` contains ≥ 270 `<testcase>` entries with no `<error>` collection entries. | Parse the uploaded `junit.xml` artifact |
| AC-6 | `--cov-fail-under=50` does not fire (coverage ≥ 50 %). | No exit-code-2 from pytest-cov |

---

## 6. Out of Scope

* Adding new tests or removing existing ones.
* Changing the CI matrix (Python versions, OS).
* Migrating to a `pyproject.toml`-based build system.
* Fixing any test logic issues unrelated to module discovery.
