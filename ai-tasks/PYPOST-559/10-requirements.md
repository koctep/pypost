# PYPOST-559: Optional slow CI smoke for make install in isolated workspace

## Goals

PYPOST-307 and PYPOST-310 validate Makefile contracts with lightweight fixtures (empty
`requirements.txt`, minimal project tree). A full `make install` that pulls real application
dependencies is network-heavy and too slow for the default CI feedback loop. Maintainers still
need an automated check that the install path works end-to-end when dependencies change, without
blocking every push on multi-minute PyPI downloads.

## User Stories

- As a **maintainer**, I want an optional CI job that runs `make install` with the real
  `requirements.txt` in an isolated workspace so broken install wiring is caught before release.
- As a **developer**, I want default `make test` and CI to stay fast while I can opt in to slow
  install smoke locally when validating dependency changes.
- As a **reviewer**, I want slow install tests clearly marked and separated from the main pytest
  matrix so PR checks remain predictable.

## Definition of Done

- A `@pytest.mark.slow` test runs `make install` in a temp workspace with copied project
  `requirements.txt` and asserts success.
- The `slow` marker is registered in `pytest.ini`.
- Default CI pytest invocation excludes slow tests; a separate CI job runs slow Makefile smoke
  with pip caching.
- `make test` excludes slow tests; `make test-slow` runs them on demand.
- Developer documentation describes scope, commands, and CI job behavior.

## Task Description

**Source:** `ai-tasks/PYPOST-307/60-tech-debt.md` — follow-up to automate full install smoke
when CI caching is available.

**Scope:** Extend `tests/test_makefile.py`, CI workflow, Makefile test targets, and dev docs.
No application code changes.

**Constraints:**

- Tests must not modify the repository `.venv`.
- Isolated `tmp_path` workspace pattern from PYPOST-307 must be reused.
- Explicit per-test timeouts per `do-testing.md`.
- Programming language: Python (pytest + subprocess).

## Q&A

- **Why not run full install in the main CI matrix?** PySide6 and related packages add minutes
  and network flakiness to every PR; empty-fixture tests already cover Makefile wiring.
- **Why a separate job instead of workflow_dispatch only?** Parallel optional job with pip cache
  gives continuous signal without slowing the primary test matrix.
