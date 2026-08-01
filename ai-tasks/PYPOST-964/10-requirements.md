# PYPOST-964: Extend seed-contract parser for install-time pyproject paths

## Goals

PYPOST-943 added a fast seed-contract guard that parses committed `pyproject.toml` for
dynamic version and readme paths. The committed manifest also declares console scripts and
may later add license-files or package-data. When packaging metadata changes, the slow
network install smoke job is the last signal — maintainers need the fast contract test to
fail first.

**Business need:** Keep the slow-smoke isolated workspace seed aligned with all install-time
paths declared in `pyproject.toml` so packaging changes surface in the default `make test`
matrix before the 1–3 minute CI smoke job.

**Parent:** [PYPOST-943](https://pypost.atlassian.net/browse/PYPOST-943) TD-2.

## Programming Language

Python (pytest contract tests). Developer documentation in English Markdown.

## User Stories

- As a **maintainer**, I want the seed-contract parser to cover scripts and future
  license/package-data fields so I update the seed when packaging metadata changes.
- As a **reviewer**, I want a fast test that fails when `[project.scripts]` targets are
  missing from the slow-smoke seed.
- As a **contributor**, I want dev docs listing which `pyproject.toml` fields drive seed
  requirements.

## Definition of Done

- [x] `_required_seed_paths_from_pyproject` covers scripts, license-files, and package-data.
- [x] `_seed_installable_package` materializes every parser-required path.
- [x] Seed-contract tests pass in default `make test`.
- [x] `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` reflects new stub modules under `pypost/`.
- [x] Unticketed follow-ups (if any) live only in `60-tech-debt.md`.

## Task Description

### Problem

The fast guard parses only dynamic version attr and readme. Committed `pyproject.toml` already
declares `[project.scripts]` pointing at `pypost.agent.ui_actions_mcp:main`, but the parser
and seed ignore it. Future license-files or package-data additions would have the same gap.

### In Scope

- Extend parser for scripts, license-files, and package-data globs.
- Align `_seed_installable_package` with parser output (copy from repo or minimal stub).
- Update minimum-tree policy constant and dev docs.

### Out of Scope

- Deduplicating workspace assembly helpers (PYPOST-965).
- Post-install `import pypost` in slow smoke (PYPOST-966).
- Jira ticket creation or git commit in this run.

## Functional Requirements

- FR1: Parser returns module paths and parent `__init__.py` files for `[project.scripts]`.
- FR2: Parser returns paths for `license-files` (project and tool.setuptools).
- FR3: Parser resolves `[tool.setuptools.package-data]` globs against the repo tree.
- FR4: Seed helper creates every parser-required path before slow smoke runs.
- FR5: Fast contract tests assert parser coverage and seeded artifact presence.

## Non-Functional Requirements

- NFR1: No network; runs in default `make test` matrix.
- NFR2: Per-test timeout per `do-testing.md`.
- NFR3: Stub script modules — do not mirror full application subpackages.

## Constraints and Assumptions

- Current `pyproject.toml` declares one console script; no license-files or package-data yet.
- Script entry points get minimal stubs, not full repo copies of agent modules.
- PYPOST-963 minimum-tree policy remains stub-not-mirror for non-required paths.

## Q&A

| Q | A |
| --- | --- |
| Why stub script modules? | Avoid full `pypost/agent/` mirror; install metadata only needs importable paths. |
| Relation to PYPOST-963? | 963 locks stub tree shape; 964 widens parser + seed for script entry points. |
| When to copy vs stub? | Copy repo files when present; stub script targets and missing `__init__.py`. |
