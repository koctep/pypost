# PYPOST-778: Architecture — pip-audit CI gate

## Overview

Add a dedicated CI job and Makefile target that install production dependencies and run
`pip-audit -r requirements.txt`. The job is separate from the pytest matrix so the scan runs once
per workflow instead of per Python version.

## Components

### 1. GitHub Actions job (`security-audit`)

| Property | Value |
| --- | --- |
| Workflow | `.github/workflows/test.yml` |
| Trigger | Same as existing `test` job (push + PR, all branches) |
| Runner | `ubuntu-latest` |
| Python | 3.11 |
| Steps | checkout → setup-python (pip cache) → upgrade pip → install `-r requirements.txt` → install pip-audit → `pip-audit -r requirements.txt` |

Rationale: installing deps before audit ensures transitive packages (starlette, uvicorn via mcp)
match what pytest jobs resolve.

### 2. Makefile target (`security-audit`)

| Property | Value |
| --- | --- |
| Prerequisite | `install` (venv + production deps) |
| Command | `pip install pip-audit && pip-audit -r requirements.txt` |

Parity with CI; not added to `make check` to avoid slowing every local run.

### 3. Documentation

Update `doc/dev/dependencies_audit.md` — mark CVE CI gate as implemented, document local
`make security-audit` and `--ignore-vuln` exception workflow.

## Out of Scope

- Lock file / pip-compile (PYPOST-779)
- Pinning remaining lower-bound deps (PYPOST-777 follow-up)
- Scanning dev-only tools (pytest, flake8)
