# PYPOST-779: Commit a lock file

## Goals

PyPost production installs must resolve to the same transitive dependency versions on every
machine and in CI. Without a committed lock, identical `requirements.txt` declarations can pull
different package trees over time, making regressions and security incident replay unreliable.
This task closes audit finding **R-P2-001 (P-001)** from PYPOST-691.

## User Stories

- As a **maintainer**, I want a committed transitive lock so I can reproduce any CI-tested
  dependency graph from git history alone.
- As a **contributor**, I want a documented workflow to bump direct dependencies and regenerate
  the lock without hand-editing dozens of transitive pins.
- As a **reviewer**, I want CI to install from the lock so pull requests are tested against the
  same resolved versions contributors use locally.

## Definition of Done

- [x] A lock workflow is adopted (`requirements.in` + compiled `requirements.txt`).
- [x] `requirements.txt` lists exact pins for all transitive production dependencies.
- [x] `make install` and CI install from the committed lock.
- [x] `make lock` regenerates the lock; upgrade workflow documented in `doc/dev/setup.md`.
- [x] Makefile and CI references updated; tests pass.

## Task Description

**Source:** PYPOST-691 dependency audit — R-P2-001.

**Scope:** `requirements.in`, `requirements.txt`, `Makefile`, `.github/workflows/test.yml`,
`doc/dev/setup.md`, `doc/dev/dependencies_audit.md`, `doc/dev/testing.md`.

**Out of scope:** Dev dependency consolidation (PYPOST-780), `pyproject.toml` (PYPOST-434).

**Constraints:**

- Preserve separation of production (`requirements.txt`) and dev tooling (Makefile/CI).
- Lock must support CI Python matrix (3.11 and 3.13).
- No change to application runtime behavior.

## Q&A

- **Why lock Python 3.11?** Minimum supported version; 3.11 lock includes stdlib backports
  needed on older Python and remains compatible with 3.13 CI.
- **Why uv instead of pip-tools?** `uv pip compile` is pip-tools-compatible, fast, and available
  on maintainer hosts; no new runtime dependency in the application venv.
