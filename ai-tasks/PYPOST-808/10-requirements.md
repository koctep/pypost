# PYPOST-808: Unify version between pyproject.toml and pypost/version.py

## Goals

PYPOST-785 introduced PEP 621 metadata in `pyproject.toml` while the About dialog and runtime
code read `pypost.version.__version__`. Two copies of `0.1.0` could drift. This task makes
`pypost/version.py` the single source and wires packaging to read it dynamically.

## User Stories

- **As a maintainer**, I want one place to bump the release version so packaging and UI stay
  aligned.
- **As a contributor**, I want tests to fail if `pyproject.toml` stops referencing the runtime
  version module.
- **As a user**, I want the About dialog to show the same version as the installed package.

## Definition of Done

- [x] `pypost/version.py` holds the canonical `__version__` string.
- [x] `pyproject.toml` uses `dynamic = ["version"]` and setuptools `attr` metadata.
- [x] About dialog continues importing `pypost.version.__version__` (no change required).
- [x] `tests/test_pyproject.py` validates dynamic version wiring.
- [x] `make check` passes.

## Task Description

**Source:** PYPOST-785 follow-up — dual version sources ([PYPOST-808](https://pypost.atlassian.net/browse/PYPOST-808)).

**Scope:** `pyproject.toml`, `pypost/version.py`, `tests/test_pyproject.py`, developer docs.

**Out of scope:** Release automation, semver bump scripts, changelog generation.

**Constraints:**

- Prefer runtime module as source (About dialog already imports it).
- No behavior change to displayed version string (`0.1.0`).

## Q&A

| Question | Answer |
| --- | --- |
| Source in `pyproject.toml` or `version.py`? | `pypost/version.py` — packaging reads it via setuptools dynamic metadata |
| Change About dialog? | No — already imports `__version__` |
| Remove sync test? | No — assert dynamic attr wiring instead of duplicated literal |
