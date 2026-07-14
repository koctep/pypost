# PYPOST-804: Add CI check-lock-dev job

## Goals

PYPOST-780 introduced a compiled dev dependency lock (`requirements-dev.txt`) and a local
`make check-lock-dev` verifier, but CI did not fail when the committed lock drifted from
`requirements-dev.in`. Maintainers need an automated gate so stale dev locks are caught before
merge.

## User Stories

- **As a maintainer**, I want CI to fail when `requirements-dev.txt` is out of date so I do not
  merge `.in` edits without regenerating the lock.
- **As a contributor**, I want the CI check to mirror the local `make check-lock-dev` command so
  failures are reproducible offline.
- **As a reviewer**, I want dev lock drift visible as a dedicated workflow job (not buried in the
  pytest matrix).

## Definition of Done

- [x] GitHub Actions job installs `uv` and runs `make check-lock-dev` on every push and PR.
- [x] Job fails when compiled output differs from committed `requirements-dev.txt`.
- [x] Implementation mirrors the production `check-lock` Makefile pattern (PYPOST-779).
- [x] Developer docs describe the CI job and local parity command.
- [x] `make check` passes.

## Task Description

**Source:** PYPOST-780 follow-up — CI check-lock-dev job ([PYPOST-804](https://pypost.atlassian.net/browse/PYPOST-804)).

**Scope:** `.github/workflows/test.yml`, `doc/dev/setup.md`, `doc/dev/testing.md`.

**Out of scope:** Production `check-lock` CI job (separate follow-up from PYPOST-779 debt),
`pip-audit` in dev lock (PYPOST-805), `pyproject.toml` optional extras (PYPOST-434).

**Constraints:**

- Reuse existing Makefile `check-lock-dev` target (no duplicate compile logic in YAML).
- Pin third-party actions to commit SHAs (PYPOST-784 convention).
- Do not add `check-lock-dev` to `make check` (requires `uv` on PATH; CI-only gate is sufficient).

## Q&A

| Question | Answer |
| --- | --- |
| Which uv setup action? | `astral-sh/setup-uv` pinned to v8.3.2 commit SHA |
| Python version for compile? | 3.11 via Makefile `LOCK_PYTHON_VERSION` (unchanged from PYPOST-780) |
| Why a separate job? | Same rationale as `security-audit` — run once per workflow, not per matrix cell |
