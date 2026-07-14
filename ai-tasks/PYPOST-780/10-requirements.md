# PYPOST-780: Consolidate dev dependencies

## Goals

PyPost installs test and lint tooling from duplicate unpinned `pip install` lines in the Makefile
and CI. That drift risks local/CI mismatch and makes dependency upgrades harder to audit. This
task closes audit finding **R-P2-002 (D-002)** from PYPOST-691.

## User Stories

- As a **maintainer**, I want dev tool versions pinned in one committed file so Makefile and CI
  stay aligned without hand-editing two install paths.
- As a **contributor**, I want `make install` to provision the same pytest/flake8 stack CI uses.
- As a **reviewer**, I want dev dependency bumps to show up as lock-file diffs like production
  deps (PYPOST-779).

## Definition of Done

- [x] `requirements-dev.in` + compiled `requirements-dev.txt` with exact transitive pins.
- [x] `make venv-test` installs from `requirements-dev.txt` (no inline unpinned packages).
- [x] CI test jobs install dev tools from `requirements-dev.txt`.
- [x] Lock regeneration documented (`make lock-dev`); tests pass.

## Task Description

**Source:** PYPOST-691 dependency audit — R-P2-002.

**Scope:** `requirements-dev.in`, `requirements-dev.txt`, `Makefile`, `.github/workflows/test.yml`,
`doc/dev/setup.md`, `doc/dev/dependencies_audit.md`, `doc/dev/testing.md`.

**Out of scope:** `pip-audit` in dev lock (still ad-hoc in `make security-audit`), `pyproject.toml`
optional extras (PYPOST-434).

**Constraints:**

- Preserve production/dev separation (`requirements.txt` vs dev lock).
- Mirror PYPOST-779 lock workflow (uv compile, Python 3.11 baseline).
- No change to application runtime behavior.

## Q&A

- **Why not fold dev deps into `requirements.in`?** Keeps production install and CVE scan surface
  limited to runtime packages.
- **Why keep `venv-test` target name?** Existing Makefile graph and docs reference it; only the
  install source changes.
