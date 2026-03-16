# PYPOST-52: Observability

## Overview

PYPOST-52 adds test coverage only — no production code is changed. Observability
for this task focuses on making the test suite itself measurable and its failures
diagnosable.

---

## Changes Made

### 1. `pytest.ini` (new file)

```ini
[pytest]
addopts = -v --tb=short
log_cli = true
log_cli_level = WARNING
log_format = %(asctime)s %(levelname)-8s %(name)s: %(message)s
log_date_format = %H:%M:%S
```

**What it enables:**

| Setting | Effect |
|---|---|
| `-v` | Verbose output — each test name and PASS/FAIL printed, not just a dot |
| `--tb=short` | Short tracebacks on failure — shows the failing assertion and its context without scrolling |
| `log_cli = true` | Live log output to stdout during test execution |
| `log_cli_level = WARNING` | Captures `WARNING`/`ERROR` log records from production code (e.g. `request_manager` already uses `logging.getLogger(__name__)`) |
| `log_format` / `log_date_format` | Standardised timestamp + logger name in log lines, making it easy to correlate log lines with failing tests |

This configuration requires no new dependencies. It applies to every `pytest`
invocation including `make test`.

---

### 2. `Makefile` — `test-cov` target and `pytest-cov` dependency

```makefile
venv-test: $(VENV_MARKER)
    $(BIN)/python -m pip install pytest flake8 pytest-cov

test-cov: $(VENV_MARKER)
    QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/ \
        --cov=pypost --cov-report=term-missing --cov-report=html:htmlcov
```

**What it enables:**

- `make test-cov` produces a terminal report showing which lines of `pypost/`
  are hit by the 51 tests and which are not (`term-missing`).
- An HTML report is written to `htmlcov/` for interactive line-by-line inspection.
- `pytest-cov` is now installed automatically by `make venv-test` / `make install`.

This gives the team a clear, repeatable way to answer "what does this test
suite actually cover?" before and after any future refactoring.

---

## Baseline Coverage Snapshot

Run `make test-cov` after `make install` to generate the authoritative baseline.
The four new test files (PYPOST-52) add coverage to:

| Production module | New tests that cover it |
|---|---|
| `pypost/core/template_service.py` | `test_template_service.py` |
| `pypost/core/request_manager.py` | `test_request_manager.py`, `test_request_manager_delete.py` |
| `pypost/core/http_client.py` | `test_http_client.py` |
| `pypost/core/request_service.py` | `test_request_service.py` |

---

## What Was Not Added

- No `--cov-fail-under` threshold — establishing a threshold requires agreeing
  on a baseline first; this is left for the Tech Lead review step.
- No CI pipeline changes — out of scope for PYPOST-52.
- No production logging additions — the existing logging in `request_manager.py`
  is already captured by `pytest.ini`; other modules have no significant logging
  paths exercised by the new tests.
