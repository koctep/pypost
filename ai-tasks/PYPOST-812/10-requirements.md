# PYPOST-812: Wire pip install -e ".[otel]" in Makefile

## Goals

Follow-up from [PYPOST-787](https://pypost.atlassian.net/browse/PYPOST-787): make the PEP 621
`[otel]` optional extra the primary Makefile and CI install path for OpenTelemetry packages,
instead of installing from the compiled `requirements-otel.txt` overlay lock.

## User Stories

- **As a contributor**, I want `make venv-otel` to install OTel packages from `pyproject.toml`
  so direct pins stay in sync with the PEP 621 extra.
- **As a maintainer**, I want CI and local `make test` to use the same editable OTel extra as
  documented in developer setup guides.
- **As a reviewer**, I want `requirements-otel.txt` to remain a lock/audit artifact, not the
  day-to-day install command.

## Definition of Done

- [x] `make venv-otel` runs `pip install -e ".[otel]"`.
- [x] `make install` runs `pip install -e ".[dev,otel]"` (includes OTel extra).
- [x] CI `test` job installs via `pip install -e ".[dev,otel]"`.
- [x] `make test`, `make test-slow`, and `make test-cov` depend on `venv-otel`.
- [x] Developer docs no longer list `pip install -r requirements-otel.txt` as a primary install
  path.
- [x] `make check` passes.

## Task Description

**Source:** PYPOST-787 follow-up — wire editable OTel extra
([PYPOST-812](https://pypost.atlassian.net/browse/PYPOST-812)).

**Scope:** Verification of `Makefile`, `.github/workflows/test.yml`, `doc/dev/setup.md`.

**Out of scope:** Removing `requirements-otel.in` / `requirements-otel.txt` lock files;
`make lock-otel` / `make check-lock-otel` targets; production `check-lock-otel` CI job.

**Constraints:**

- Implementation was delivered in PYPOST-806; this task confirms wiring and closes documentation
  gaps.
- `tests/test_pyproject.py` drift guard between `pyproject.toml` and `requirements-otel.in`
  unchanged.

## Q&A

| Question | Answer |
| --- | --- |
| Was Makefile code changed in PYPOST-812? | No — PYPOST-806 already migrated `venv-otel` |
| Why keep `requirements-otel.txt`? | Transitive lock for `make lock-otel`, Dependabot cache keys |
| Primary OTel install for end users? | `pip install -e ".[otel]"` or `make venv-otel` |
