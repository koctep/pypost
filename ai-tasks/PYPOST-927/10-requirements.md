# PYPOST-927: CI check-lock job for production requirements.txt

## Goals

PYPOST-779 introduced a compiled production dependency lock (`requirements.txt`) and a local
`make check-lock` verifier, but CI did not fail when the committed lock drifted from
`requirements.in`. The license inventory gate can miss `.in`→`.txt` drift when the CSV still
matches a stale lock. Maintainers need an automated gate so stale production locks are caught
before merge.

## User Stories

- **As a maintainer**, I want CI to fail when `requirements.txt` is out of date so I do not merge
  `.in` edits without regenerating the lock.
- **As a contributor**, I want the CI check to mirror the local `make check-lock` command so
  failures are reproducible offline.
- **As a reviewer**, I want production lock drift visible as a dedicated workflow job (sibling of
  `check-lock-dev`, not buried in the pytest matrix).

## Definition of Done

- [x] GitHub Actions job installs `uv` and runs `make check-lock` on every push and PR.
- [x] Job fails when compiled output differs from committed `requirements.txt`.
- [x] Implementation mirrors the dev `check-lock-dev` CI job (PYPOST-804).
- [x] Developer docs describe the CI job and local parity command.
- [x] `make check` passes.

## Task Description

**Source:** PYPOST-923 TD-4 / PYPOST-779 follow-up — production `check-lock` CI job
([PYPOST-927](https://pypost.atlassian.net/browse/PYPOST-927)).

**Scope:** `.github/workflows/test.yml`, `doc/dev/setup.md`, `doc/dev/testing.md`.

**Out of scope:** OTel lock CI (`check-lock-otel`), wiring `check-lock` into `make check`,
`pip-audit` policy changes.

**Constraints:**

- Reuse existing Makefile `check-lock` target (no duplicate compile logic in YAML).
- Pin third-party actions to commit SHAs (PYPOST-784 convention).
- Do not add `check-lock` to `make check` (requires `uv` on PATH; CI-only gate is sufficient).

## Q&A

| Question | Answer |
| --- | --- |
| Which uv setup action? | `astral-sh/setup-uv` pinned to v8.3.2 commit SHA (same as `check-lock-dev`) |
| Python version for compile? | 3.11 via Makefile `LOCK_PYTHON_VERSION` (unchanged from PYPOST-779) |
| Why a separate job? | Same rationale as `check-lock-dev` — run once per workflow, not per matrix cell |
