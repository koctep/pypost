# PYPOST-785: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- `pyproject.toml` duplicates dependency specs from `requirements.in` and `requirements-dev.in`
  rather than generating one from the other (manual sync guarded by tests).
- OpenTelemetry packages remain in `[project].dependencies` while also listed under the `otel`
  extra; removal from default deps is deferred to PYPOST-787.
- Version is declared in both `pyproject.toml` and `pypost/version.py` (About dialog reads the
  module constant).

## Code Quality Issues

None blocking. New test module mirrors existing lock-file presence checks.

## Missing Tests

- No test runs `pip install -e ".[dev]"` or validates setuptools package discovery end-to-end
  (install wiring is out of scope).

## Performance Concerns

None. Metadata file only.

## Follow-up Tasks

### NON-BLOCKER

#### Wire pip install -e . in Makefile

- **Priority:** P3
- **Description:** `make install` and CI still use `requirements.txt`; `pyproject.toml` is
  declarative only.
- **Remediation:** Add editable install target and migrate install docs when sibling ticket lands.
- **Jira:** [PYPOST-806](https://pypost.atlassian.net/browse/PYPOST-806)

#### Move OpenTelemetry to otel extra only

- **Priority:** P3
- **Description:** OTel is duplicated in default deps and `[project.optional-dependencies].otel`.
- **Remediation:** [PYPOST-787](https://pypost.atlassian.net/browse/PYPOST-787)

#### Migrate pytest config to pyproject.toml

- **Priority:** P3
- **Description:** `pytest.ini` still holds `pythonpath`, coverage, and marker config.
- **Remediation:** Consolidate into `[tool.pytest.ini_options]` when install path adopts
  `pyproject.toml`.
- **Jira:** [PYPOST-807](https://pypost.atlassian.net/browse/PYPOST-807)

#### Dual version sources

- **Priority:** P3
- **Description:** `pyproject.toml` version and `pypost/version.py` can drift.
- **Remediation:** Single-source version (dynamic metadata or import hook) when packaging is
  wired.
- **Jira:** [PYPOST-808](https://pypost.atlassian.net/browse/PYPOST-808)
