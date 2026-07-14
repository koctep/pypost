# PYPOST-806: Wire pip install -e . in Makefile

## Goals

PYPOST-785 added PEP 621 metadata and optional `[dev]` / `[otel]` extras to `pyproject.toml`, but
`make install` and CI still installed from `requirements.txt` and separate lock files. This task
migrates the primary install path to editable package install so `pyproject.toml` is the runtime
source of truth for direct dependency pins.

## User Stories

- **As a contributor**, I want `make install` to install PyPost as an editable package with dev and
  OTel tooling so `import pypost` works without `PYTHONPATH` hacks.
- **As a maintainer**, I want CI to use the same editable install command as local `make install`
  for parity.
- **As a reviewer**, I want lock files (`requirements*.txt`) to remain for `pip-audit`, Dependabot,
  and `uv pip compile` workflows while install paths read from `pyproject.toml`.

## Definition of Done

- [x] `make install` runs `pip install -e ".[dev,otel]"`.
- [x] `make venv-test` and `make venv-otel` use editable extras (`.[dev]`, `.[otel]`).
- [x] CI `test` job installs via `pip install -e ".[dev,otel]"`.
- [x] CI `make-install-smoke` and `security-audit` jobs updated for editable dev install.
- [x] `tests/test_makefile.py` fixtures supply `pyproject.toml`; dependency-chain tests updated.
- [x] Developer docs updated (`setup.md`, `testing.md`, related).
- [x] `make check` passes (1617 tests).

## Task Description

**Source:** PYPOST-785 follow-up — wire editable install ([PYPOST-806](https://pypost.atlassian.net/browse/PYPOST-806)).

**Scope:** `Makefile`, `.github/workflows/test.yml`, `tests/test_makefile.py`, `doc/dev/`.

**Out of scope:** Removing `requirements*.txt` lock files; migrating `pytest.ini` to
`pyproject.toml` (PYPOST-807); production `check-lock` CI job.

**Constraints:**

- `pip-audit` scan target remains `requirements.txt` (production lock).
- `tests/test_pyproject.py` drift guard between `pyproject.toml` and `requirements*.in` unchanged.
- Lock regeneration targets (`make lock`, `make lock-dev`, `make lock-otel`) unchanged.

## Q&A

| Question | Answer |
| --- | --- |
| Why keep lock files? | Transitive pins, CVE scan input, Dependabot, and `check-lock-dev` CI |
| Does `install` still chain `venv-test`/`venv-otel`? | No — single `pip install -e ".[dev,otel]"` step |
| Security-audit production install? | Removed; scan is file-based on `requirements.txt`; dev extra provides `pip-audit` CLI |
