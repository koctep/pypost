# PYPOST-928: Harden workflow YAML parsing for CI contract tests

## Goals

Multiple CI contract tests (PYPOST-874, PYPOST-909, PYPOST-910, PYPOST-923, PYPOST-927)
each duplicated a fragile line-based `_job_block` heuristic to slice GitHub Actions workflow
YAML. When one parser drifts or breaks, sibling locks become inconsistent. Maintainers need a
single hardened helper so workflow contract tests stay reliable and DRY.

## User Stories

- **As a maintainer**, I want one shared workflow job-block parser so CI contract tests do not
  duplicate brittle heuristics.
- **As a contributor**, I want contract tests to validate job existence structurally (not only
  by substring search) before asserting upload/retention/composite wiring.
- **As a reviewer**, I want existing PYPOST-874/909/910/923/927 locks to remain green after
  consolidation.

## Definition of Done

- [x] Shared helper under `tests/helpers/` used by smoke, agent-e2e, and sibling CI contract
  tests.
- [x] Helper validates `jobs:` mapping via `yaml.safe_load` before text extraction.
- [x] Existing workflow contract tests pass unchanged in behavior.
- [x] Contract test asserts modules import the shared helper (no local `_job_block` copies).
- [x] Developer docs mention the helper for future CI locks.

## Task Description

**Source:** TD-5 from PYPOST-923/924/925 — shared fragility with PYPOST-874-style tests
([PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928)).

**Scope:** `tests/helpers/ci_workflow_yaml.py`, CI contract test modules, `doc/dev/testing.md`.

**Out of scope:** Full YAML AST for apt-line parsing; production runtime code; workflow YAML
changes.

**Constraints:**

- Preserve substring-based contract assertions (upload paths, `uses:` lines, etc.).
- Keep tests fast (read committed files only; no live Actions).
- Every test module retains explicit timeout markers.

## Q&A

| Question | Answer |
| --- | --- |
| Why not parse jobs into dict only? | Contract tests grep raw step text; returning a text block preserves lock phrases |
| PyYAML vs tiny subset parser? | PyYAML already a project dependency; validates structure then slices raw block |
| Which modules migrate? | All five copies: 874, 909, 910, 923/927 smoke+check-lock |
