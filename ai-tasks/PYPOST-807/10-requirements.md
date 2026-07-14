# PYPOST-807: Migrate pytest config to pyproject.toml

## Goals

PYPOST-785 added PEP 621 metadata to `pyproject.toml` and PYPOST-806 wired editable install.
Pytest configuration still lived in a separate `pytest.ini`. This task consolidates pytest
settings into `[tool.pytest.ini_options]` so `pyproject.toml` is the single project metadata and
test-config source of truth.

## User Stories

- **As a contributor**, I want pytest markers, coverage gate, and logging defaults in
  `pyproject.toml` so I do not hunt across config files.
- **As a maintainer**, I want CI and local runs to behave identically after removing
  `pytest.ini`.
- **As a reviewer**, I want developer docs to reference the new config location for threshold
  and `log_cli` changes.

## Definition of Done

- [x] All former `pytest.ini` settings appear under `[tool.pytest.ini_options]` in
  `pyproject.toml`.
- [x] Root `pytest.ini` removed.
- [x] Developer docs updated (`setup.md`, `testing.md`, related audit docs).
- [x] `make check` passes (1617 tests).

## Task Description

**Source:** PYPOST-785 follow-up — migrate pytest config ([PYPOST-807](https://pypost.atlassian.net/browse/PYPOST-807)).

**Scope:** `pyproject.toml`, delete `pytest.ini`, `doc/dev/` references.

**Out of scope:** Changing coverage threshold, `log_cli` CI overrides, Makefile pytest flags,
historical `ai-tasks/` artifact text.

**Constraints:**

- Preserve existing `addopts`, markers, `pythonpath`, and `log_cli` values verbatim.
- `test.yml` `THRESHOLD=70` remains a display mirror; enforcement stays in `addopts`.

## Q&A

| Question | Answer |
| --- | --- |
| Keep `pythonpath = "."` after editable install? | Yes — fallback for pytest without `make install` |
| Change Makefile targets? | No — they invoke `python -m pytest`; config is discovered from `pyproject.toml` |
| Update historical ai-tasks docs? | No — point-in-time records |
