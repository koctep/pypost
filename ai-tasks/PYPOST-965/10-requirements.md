# PYPOST-965: Deduplicate slow-smoke workspace assembly helpers

## Goals

PYPOST-943 introduced slow-smoke isolated workspace seeding and a fast contract test that
mirrors the fixture assembly steps. PYPOST-963 and PYPOST-964 extended the seed and parser
but left two copies of the same three-step sequence (copy Makefile, copy pyproject, seed
package). When seed order or Makefile wiring changes, only one copy may be updated — causing
silent drift between the slow smoke fixture and the fast contract guard.

**Business need:** One shared assembly helper so maintainers change slow-smoke workspace
setup in a single place and the contract test always exercises the same path as the fixture.

**Parent:** [PYPOST-943](https://pypost.atlassian.net/browse/PYPOST-943) TD-3.

## Programming Language

Python (pytest test helpers). Developer documentation in English Markdown.

## User Stories

- As a **maintainer**, I want one function that assembles the slow-smoke workspace so I do
  not update fixture and contract test separately.
- As a **reviewer**, I want the contract test to call the same helper as `make_workspace_full_deps`
  so fast guards cannot diverge from slow smoke setup.

## Definition of Done

- [x] Single shared helper used by `make_workspace_full_deps` and seed-contract tests.
- [x] Duplicate `_materialize_slow_smoke_seed` removed from contract module.
- [x] Existing seed-contract and Makefile integration tests remain green.
- [x] Unticketed follow-ups (if any) live only in `60-tech-debt.md`.

## Task Description

### Problem

`make_workspace_full_deps` and `_materialize_slow_smoke_seed` both perform:

1. Copy root `Makefile`
2. Copy committed `pyproject.toml`
3. Run `_seed_installable_package`

The duplication is identical today but fragile when assembly steps change.

### In Scope

- Extract `_materialize_slow_smoke_workspace(workspace: Path) -> None` in `test_makefile.py`.
- Wire fixture and contract tests to the shared helper.
- Document helper name in dev testing docs.

### Out of Scope

- Changing seed contents, parser logic, or slow smoke behavior (PYPOST-964 scope).
- Post-install `import pypost` in slow smoke (PYPOST-966).
- Jira ticket creation or git commit in this run.

## Functional Requirements

- FR1: Fixture `make_workspace_full_deps` delegates to the shared helper.
- FR2: Contract tests materialize the workspace via the same helper (no local duplicate).
- FR3: No change to assembled workspace shape or test assertions.

## Non-Functional Requirements

- NFR1: Refactor only — no new network or slow-test dependencies.
- NFR2: Per-test timeout unchanged.

## Q&A

- **Why not move helper to a separate module?** Co-locate with seed helpers and fixture;
  contract test already imports from `test_makefile`; avoids a third file for ~5 lines.
