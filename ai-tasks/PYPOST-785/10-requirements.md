# PYPOST-785: Introduce pyproject.toml

## Goals

PyPost has no PEP 621 project metadata or optional dependency groups. Dependency policy is
scattered across `requirements.in`, `requirements-dev.in`, Makefile, and CI. This task closes
audit finding **R-P3-001 (P-002)** from PYPOST-691 by adding a minimal `pyproject.toml` that
documents the project and expresses production, dev, and OpenTelemetry dependency groups.

## User Stories

- As a **maintainer**, I want PEP 621 metadata in one file so packaging policy is discoverable
  without reading multiple install paths.
- As a **contributor**, I want optional `dev` and `otel` extras defined so future install flows
  can use `pip install -e ".[dev]"` instead of ad-hoc requirement files.
- As a **reviewer**, I want `pyproject.toml` dependencies to mirror the pinned production lock
  source (`requirements.in`) so drift is detectable in tests.

## Definition of Done

- [x] `pyproject.toml` exists with `[project]` name, version, description, license, and
  `requires-python`.
- [x] `[project].dependencies` lists all 15 direct production packages from `requirements.in`.
- [x] `[project.optional-dependencies]` defines `dev` (pytest/flake8 stack) and `otel`
  (OpenTelemetry API/SDK) groups.
- [x] Tests verify `pyproject.toml` stays aligned with `requirements.in` and `requirements-dev.in`.
- [x] Makefile and CI continue using requirement files (no install-path wiring in this ticket).

## Task Description

**Source:** PYPOST-691 dependency audit — R-P3-001 / P-002.

**Scope:** `pyproject.toml`, `tests/test_pyproject.py`, `doc/dev/setup.md`,
`doc/dev/dependencies_audit.md`.

**Out of scope:** `pip install -e .` in Makefile/CI (sibling tickets), moving OpenTelemetry out
of default production deps (PYPOST-787), pytest config migration from `pytest.ini` (future).

**Constraints:**

- Mirror `requirements.in` pins exactly; do not change resolved production graph.
- Keep `requirements.txt` / `requirements-dev.txt` as the active install path until wired.
- No application runtime behavior changes.

## Q&A

- **Why keep OTel in both `[project].dependencies` and `[project.optional-dependencies].otel`?**
  Production install still includes OTel today; the extra pre-defines the group for PYPOST-787
  without changing current installs.
- **Why not wire Makefile/CI here?** Sibling tickets adopt `pyproject.toml` incrementally after
  metadata lands.
