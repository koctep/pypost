# PYPOST-307: Automated tests for Makefile behavior

## Goals

Developers and CI rely on the project `Makefile` for environment setup, dependency
installation, and quality gates. When Make targets misbehave (wrong prerequisites, broken
marker lifecycle, unexpected exit codes), local workflows and CI fail in confusing ways.
This task closes the gap identified in PYPOST-33 technical debt: there are no automated
checks that the Makefile contract still holds after changes.

## User Stories

- As a **developer**, I want Makefile behavior verified automatically so that refactors to
  build automation do not silently break `venv`, `install`, or quality targets.
- As a **maintainer**, I want regression tests for marker lifecycle and target dependencies
  so CI and local `make` usage stay aligned.
- As a **reviewer**, I want failing Make automation to surface in `make test` instead of
  only during manual troubleshooting.

## Definition of Done

- A dedicated pytest module exercises Makefile behavior without modifying the developer's
  working tree (isolated temporary workspace).
- **Marker lifecycle**: creating `venv` produces the versioned `.initialized-<major.minor>`
  marker; `clean` removes it; repeated `venv` is idempotent.
- **Dependency chain**: documented prerequisites for `install`, `venv-test`, `run`, `test`,
  and `lint` match the Makefile contract (install chains through venv tooling; run/test/lint
  require the marker only, not full `install`).
- **Exit behavior**: `clean` and `venv` succeed; unknown targets fail; `lint` fails when
  required tools are absent from a bare venv.
- All new tests declare explicit `pytest.mark.timeout` markers and pass under `make test`.
- Developer documentation describes how to run and extend Makefile tests.

## Task Description

**Source:** `ai-tasks/PYPOST-33/60-tech-debt.md` — missing dedicated Makefile automation
tests for marker lifecycle, dependency chain, and expected target exit behavior.

**Scope:** Test-only change plus dev docs. No Makefile behavior changes unless a test
reveals a defect (fix in scope only if required for acceptance criteria).

**Constraints:**

- Tests must not delete or overwrite the repository `.venv` used for development.
- Tests must complete within reasonable CI time (timeouts per `do-testing.md`).
- Programming language: Python (pytest + subprocess).

## Q&A

- **Why not shell scripts?** Pytest keeps Makefile checks in the same suite as application
  tests and reuses timeout enforcement in `conftest.py`.
- **Why isolated temp workspaces?** Copying the Makefile into a temp directory avoids
  interfering with the developer environment while still exercising real `make` behavior.
