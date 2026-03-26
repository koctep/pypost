# PYPOST-434 Architecture — GitHub Actions: pytest job failed

## 1. Problem Summary

`pytest tests/` fails in CI (and locally without `PYTHONPATH`) because the repo root is not
in `sys.path`, so `import pypost` raises `ModuleNotFoundError`.  The project has no
`setup.py` / `pyproject.toml`, so the package is never installed into the virtual
environment; pytest must be told to prepend the repo root to `sys.path` itself.

---

## 2. Solution Overview

Add a single line to `pytest.ini`:

```ini
pythonpath = .
```

This is the canonical pytest ≥ 7.0 mechanism for uninstalled packages.  No workflow
changes, no production-code changes, no new files.

### Files changed

| File | Change |
|---|---|
| `pytest.ini` | Add `pythonpath = .` under `[pytest]` |

---

## 3. Detailed Design

### 3.1 Mechanism

When `pythonpath = .` is present in `pytest.ini`, pytest prepends the value (resolved
relative to the `rootdir`, which is the directory containing `pytest.ini`) to `sys.path`
**before** any test collection begins.  For this repo, `rootdir` is `/home/src` (or the
repo root in CI), so `sys.path` will contain `/home/src` first, making
`import pypost` succeed.

pytest deduplicates `sys.path` entries, so if a caller already has `PYTHONPATH=/home/src`
set, the directory is not duplicated — existing local workflows are unaffected.

### 3.2 pytest.ini — before / after

**Before**

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

**After** (matches committed layout)

```ini
[pytest]
pythonpath = .
# --cov-fail-under: enforces minimum line coverage for `pypost`.
# Threshold set to 50% (baseline 54%, floor(54/5)*5=50, buffer of one 5pp step).
# Baseline is below the project target of 70%; raise threshold in follow-up PYPOST-88-raise.
addopts = -v --tb=short --cov-fail-under=50
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
log_date_format = %H:%M:%S
```

`pythonpath` sits immediately under `[pytest]`, before the comment/`addopts` block, so
import path setup is explicit and separate from pytest flags.

### 3.3 Why not the alternatives

| Alternative | Reason rejected |
|---|---|
| Set `PYTHONPATH` in workflow `env:` | Workflow-only fix; local `pytest tests/` still breaks without env var. |
| `pip install -e .` in CI | Requires adding `setup.py` / `pyproject.toml` — out of scope per requirements §2. |
| `conftest.py` with `sys.path.insert` | Undocumented side-effect pattern; `pythonpath =` is the official mechanism. |
| Move tests inside `pypost/` | Layout change — out of scope. |

### 3.4 Compatibility

* `pythonpath` ini option was introduced in **pytest 7.0** (2022-01-30).
* The CI workflow installs `pytest` without a pinned version; any version ≥ 7.0 is
  supported.  Python 3.11 and 3.13 are both covered.
* If pytest < 7.0 is ever used, pytest will emit an `UnknownMarkWarning` for the unknown
  ini key and ignore it — the setting will silently have no effect, but it will not
  break existing behaviour.

---

## 4. Acceptance Criteria Mapping

| AC | Satisfied by |
|---|---|
| AC-1: `pytest tests/` collects all tests without errors | `pythonpath = .` prepends repo root → `import pypost` succeeds |
| AC-2/3: CI passes on Python 3.11 and 3.13 | Same mechanism; Python-version agnostic |
| AC-4: `coverage.xml` uploaded | Tests now run → `pytest-cov` generates `coverage.xml` |
| AC-5: `junit.xml` has ≥ 270 `<testcase>` entries | Tests collected and executed |
| AC-6: `--cov-fail-under=50` passes | Existing 53.6 % coverage unchanged |

---

## 5. Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| pytest version < 7.0 in CI | Very low (latest pip install) | Acceptable; worst case: silent no-op, same failure mode as today |
| Other `pytest.ini` keys conflict with `pythonpath` | None identified | `pythonpath` is orthogonal to all current keys |
| Tests fail for reasons other than import error | Low | Requirements confirm 277 pass locally; fix is import-path only |

---

## 6. Implementation Instructions for Junior Engineer

1. Open `pytest.ini`.
2. Add exactly one line — `pythonpath = .` — immediately after the `[pytest]` header line
   (before the existing comment and `addopts` block).
3. Verify locally:
   ```
   pytest tests/ --collect-only -q
   ```
   Expected: ≥ 270 items collected, exit 0, no `ModuleNotFoundError`.
4. No other files require changes.
