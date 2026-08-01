# PYPOST-963: Document or assert minimum pypost/ tree for slow-smoke seed

## Goals

PYPOST-943 restored slow Makefile install smoke by seeding `pypost/version.py` and
`README.md` atop a stub `pypost/__init__.py`. That fix is implicit: contributors and
future packaging changes cannot tell whether the isolated workspace should mirror the
full `pypost/` tree or stay minimal. If setuptools later requires modules beyond
version/readme (entry points, package-data, subpackages), the seed could silently
under-provision again.

**Business need:** Make the slow-smoke minimum `pypost/` tree policy explicit and
machine-checked so packaging metadata changes do not regress the isolated install
contract without a fast, local failure signal.

**Parent:** [PYPOST-943](https://pypost.atlassian.net/browse/PYPOST-943) TD-1.

## Programming Language

Python (pytest contract tests). Developer documentation in English Markdown.

## User Stories

- As a **maintainer**, I want the slow-smoke seed policy documented so I know when to
  extend the fixture versus copying the full package tree.
- As a **reviewer**, I want a fast test that asserts the minimum `pypost/` tree shape
  so packaging PRs cannot silently under-seed the isolated workspace.
- As a **contributor**, I want dev docs to explain stub-versus-mirror rationale so I
  can update the seed correctly when `pyproject.toml` changes.

## Definition of Done

- [x] Minimum `pypost/` tree policy is documented (stub `__init__.py` + required
  packaging files, not a full repo mirror).
- [x] Policy is asserted in the default `make test` matrix (fast contract test).
- [x] `make check` remains green for the change set.
- [x] Unticketed follow-ups (if any) live only in `60-tech-debt.md`.

## Task Description

### Problem

Slow-smoke isolated workspace seeding is correct today but implicit. Only
`pypost/version.py` and `README.md` are copied atop a stub `__init__.py`; the decision
not to mirror `pypost/core/`, `pypost/ui/`, etc. is undocumented and unasserted.

### In Scope

- Document minimum-tree policy in `doc/dev/testing.md`.
- Add or extend fast contract test to assert `pypost/` contains exactly the policy
  files (no subpackages, no full mirror).
- Named policy constant co-located with seed helper for single source of truth.

### Out of Scope

- Deduplicating `_materialize_slow_smoke_seed` vs `make_workspace_full_deps` (PYPOST-965).
- Extending `_required_seed_paths_from_pyproject` for new dynamic fields (PYPOST-964).
- Post-install `import pypost` in slow smoke (PYPOST-966).
- Jira ticket creation or git commit in this run.

## Functional Requirements

- FR1: Dev docs state whether slow-smoke uses a stub package or full mirror and why.
- FR2: Fast contract test fails if `pypost/` gains unexpected files or loses policy files.
- FR3: Policy constant lists canonical minimum paths under `pypost/` for the seed.

## Non-Functional Requirements

- NFR1: No network; runs in default `make test` matrix.
- NFR2: Per-test timeout per `do-testing.md`.
- NFR3: Prefer docs + small test extension over refactors.

## Constraints and Assumptions

- Current `pyproject.toml` needs only stub `__init__.py`, `version.py`, and `README.md`.
- `[project.scripts]` entry points do not require seeding subpackages for editable
  install metadata resolution today.
- PYPOST-943 seed helpers and contract parser remain the baseline.

## Q&A

| Q | A |
| --- | --- |
| Stub or full mirror? | Stub — sufficient for dynamic version + package discovery. |
| When to extend? | When `pyproject.toml` requires install-time paths beyond current policy. |
| Relation to PYPOST-964? | 964 extends parser for new dynamic fields; 963 locks tree shape policy. |
