# PYPOST-805: pip-audit in dev lock architecture

## Overview

Move `pip-audit` from ephemeral per-run installs into the compiled dev dependency lock
(`requirements-dev.txt`), reusing the PYPOST-780 two-file layout and PYPOST-785
`pyproject.toml` parity tests.

## Components

### 1. Dev lock source (`requirements-dev.in`)

| Property | Value |
| --- | --- |
| New direct dep | `pip-audit>=2,<4` |
| Lock command | `make lock-dev` (`uv pip compile`, Python 3.11) |
| Committed output | `requirements-dev.txt` (includes transitive scanner deps) |

### 2. Makefile `security-audit`

| Property | Before | After |
| --- | --- | --- |
| Prerequisites | `install` | `install` (unchanged) |
| Scanner install | `pip install pip-audit` | via `venv-test` → `requirements-dev.txt` |
| Scan command | `pip-audit -r requirements.txt` | unchanged |

`install` already chains `venv-test` before `requirements.txt`, so `pip-audit` is on PATH in
`.venv/bin` when the scan runs.

### 3. CI `security-audit` job

| Step | Before | After |
| --- | --- | --- |
| App deps | `pip install -r requirements.txt` | unchanged |
| Scanner | inline `pip install pip-audit` | `pip install -r requirements-dev.txt` |
| Audit | `pip-audit -r requirements.txt` | unchanged |

Pip cache already keys on `requirements-dev.in` / `requirements-dev.txt` (PYPOST-311), so the
added install step reuses cached wheels when the dev lock is unchanged.

### 4. `pyproject.toml` parity

`[project.optional-dependencies].dev` gains `pip-audit>=2,<4` so `tests/test_pyproject.py`
continues to enforce alignment with `requirements-dev.in`.

## Scan boundary (unchanged)

```
requirements.txt  ──► pip-audit -r requirements.txt  ──► pass/fail
(production graph)         ▲
                           │
              pip-audit CLI from requirements-dev.txt
              (dev tooling, not scanned as production)
```

## Out of Scope

- Auditing the dev lock graph itself.
- Adding `security-audit` to `make check` (network/OSV lookup remains opt-in).
