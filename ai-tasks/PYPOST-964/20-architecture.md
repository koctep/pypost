# PYPOST-964: Extend seed-contract parser

## Research

### Gap

| Field | In committed pyproject | Parser before | Parser after |
| --- | --- | --- | --- |
| dynamic version + readme | Yes | Yes | Yes |
| `[project.scripts]` | Yes | No | Yes |
| license-files | No | No | Yes (when added) |
| package-data | No | No | Yes (when added) |

### Root cause

PYPOST-943 intentionally narrowed the parser to version/readme (TD-2). Committed scripts
were deferred; the fast guard lagged packaging metadata.

## Implementation Plan

1. **Red repro** — extend parser for scripts; artifact contract test fails until seed updated.
2. **Move parser** — co-locate `_required_seed_paths_from_pyproject` with `_seed_installable_package`
   in `tests/test_makefile.py` for single source of truth.
3. **Extend parser** — scripts (module + parent inits), license-files, package-data globs.
4. **Seed alignment** — `_seed_installable_package` iterates parser paths; copy or stub.
5. **Policy constant** — add `agent/__init__.py` and `agent/ui_actions_mcp.py` stubs.
6. **Tests** — dedicated parser tests for scripts + synthetic license/package-data pyproject.
7. **Docs** — extend `doc/dev/testing.md` field table.

## Architecture

### Components

| Component | Change |
| --- | --- |
| `_required_seed_paths_from_pyproject` | **Extend** — scripts, license-files, package-data |
| `_seed_installable_package` | **Refactor** — derive paths from parser, materialize all |
| `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` | **Widen** — script stub modules |
| Seed contract tests | **Extend** — parser unit tests + existing artifact assertions |

### Design decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Parser location | `test_makefile.py` | Co-located with seed helper; contract test imports |
| Script modules | Minimal stub with `main()` | Satisfies entry-point path without full agent mirror |
| Package-data | Resolve globs from repo root | Matches files setuptools expects at install time |
| License-files | Union project + tool.setuptools | Covers static and dynamic declarations |

## Q&A

| Q | A |
| --- | --- |
| Does slow smoke import script modules? | No — stubs exist for metadata/contract only. |
| Full mirror of agent/? | No — PYPOST-963 stub policy preserved. |
