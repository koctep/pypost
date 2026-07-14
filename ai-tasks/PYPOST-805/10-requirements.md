# PYPOST-805: Add pip-audit to requirements-dev lock

## Goals

PYPOST-778 added a CI and local CVE gate using `pip-audit`, but the scanner was installed
ephemerally (`pip install pip-audit`) in `make security-audit` and the GitHub Actions
`security-audit` job. PYPOST-780 introduced a compiled dev dependency lock; this task pins
`pip-audit` there so local and CI share one versioned scanner alongside pytest, flake8, and mypy.

## User Stories

- **As a maintainer**, I want `pip-audit` version-pinned in `requirements-dev.txt` so security
  tooling upgrades go through the same lock workflow as other dev deps.
- **As a contributor**, I want `make security-audit` to use the venv-installed scanner (via
  `make install`) without an extra ad-hoc pip install step.
- **As a reviewer**, I want CI to install `pip-audit` from the committed dev lock, not latest
  PyPI on every run.

## Definition of Done

- [x] `pip-audit` listed in `requirements-dev.in` and mirrored in `pyproject.toml` `[dev]` extra.
- [x] `requirements-dev.txt` regenerated with `make lock-dev`.
- [x] Inline `pip install pip-audit` removed from Makefile `security-audit` target.
- [x] Inline `pip install pip-audit` removed from CI `security-audit` job; job installs
  `requirements-dev.txt` instead.
- [x] Developer docs updated for pinned scanner workflow.
- [x] `make check` and `make security-audit` pass.

## Task Description

**Source:** PYPOST-780 follow-up — pip-audit in dev lock ([PYPOST-805](https://pypost.atlassian.net/browse/PYPOST-805)).

**Scope:** `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml`, `Makefile`,
`.github/workflows/test.yml`, `doc/dev/`.

**Out of scope:** Scanning `requirements-dev.txt` itself for CVEs (production graph only);
production `check-lock` CI job (PYPOST-779 debt).

**Constraints:**

- Keep scanning input as `requirements.txt` (production deps only), unchanged from PYPOST-778.
- `make security-audit` prerequisite remains `install` (provides both app and dev tooling).
- Regenerate lock with existing `make lock-dev` / `uv pip compile` workflow.

## Q&A

| Question | Answer |
| --- | --- |
| Version constraint? | `pip-audit>=2,<4` (resolved to `2.10.1` in lock) |
| Why dev lock, not production? | Scanner is maintainer/CI tooling, not a runtime dependency |
| CI install order? | `requirements.txt` first (scan target), then `requirements-dev.txt` (scanner CLI) |
