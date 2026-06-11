# PYPOST-310: Lightweight Make target automation suite

## Goals

PYPOST-33 technical debt called for automated checks on core `Makefile` targets (`venv`,
`install`, `test`, `lint`) so dependency flow and exit codes stay correct as the build
automation evolves. [PYPOST-307](https://pypost.atlassian.net/browse/PYPOST-307) already
delivered marker lifecycle, prerequisite chain, and partial exit-code coverage in
`tests/test_makefile.py`. This task closes the remaining gap: lightweight **execution**
smoke tests for `install`, `test`, and `lint` success/failure paths without duplicating
PYPOST-307 work.

## User Stories

- As a **developer**, I want `make install` and `make test` exit codes verified in CI so
  broken dependency wiring surfaces before manual troubleshooting.
- As a **maintainer**, I want documented overlap with PYPOST-307 so future tasks do not
  re-implement the same Makefile contract tests.
- As a **reviewer**, I want success and failure exit codes for quality targets after a
  minimal isolated workspace setup.

## Definition of Done

- Overlap with PYPOST-307 is documented in task artifacts and `doc/dev/testing.md`.
- `tests/test_makefile.py` gains execution-level cases:
  - `make install` succeeds with an empty `requirements.txt` fixture.
  - `make test` fails on a bare venv (no pytest) and succeeds after `install`.
  - `make lint` succeeds after `install` when a minimal `pypost/` tree is present.
- Existing PYPOST-307 cases (marker lifecycle, `make -p` prerequisites, bare-venv lint
  failure) remain unchanged.
- All tests keep explicit timeouts and pass under `make test`.
- Developer documentation describes the extended scope and how to run focused Makefile tests.

## Task Description

**Source:** `ai-tasks/PYPOST-33/60-tech-debt.md` — automate Make target checks for `venv`,
`install`, `test`, `lint`.

**Scope:** Extend `tests/test_makefile.py` and dev docs only. No Makefile changes unless a
defect is found (none expected).

**Constraints:**

- Tests must not modify the repository `.venv`.
- Keep additions lightweight (no full network-heavy dependency installs beyond empty
  `requirements.txt` and `venv-test` tooling).
- Programming language: Python (pytest + subprocess).

## Q&A

- **Why not a new test module?** PYPOST-307 already owns Makefile automation; extending the
  same module avoids duplicate fixtures and keeps one focused run command.
- **Why not full `make run`?** Out of scope; `run` needs application code and is covered by
  manual/CI workflows elsewhere.
