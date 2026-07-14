# PYPOST-804: CI check-lock-dev architecture

## Overview

Add a lightweight GitHub Actions job that installs `uv` and delegates lock verification to the
existing Makefile target `make check-lock-dev`. The job mirrors the production `check-lock`
Makefile pattern from PYPOST-779, applied to the dev lock from PYPOST-780.

## Components

### 1. GitHub Actions job (`check-lock-dev`)

| Property | Value |
| --- | --- |
| Workflow | `.github/workflows/test.yml` |
| Trigger | Same as existing jobs (push + PR, all branches) |
| Runner | `ubuntu-latest` |
| Steps | checkout → `astral-sh/setup-uv` (pinned SHA) → `make check-lock-dev` → job summary |

Rationale: separate job runs once per workflow (like `security-audit`), avoiding duplicate
`uv pip compile` work in each Python matrix cell.

### 2. Makefile target (unchanged)

| Property | Value |
| --- | --- |
| Target | `check-lock-dev` |
| Prerequisite | none (no venv) |
| Command | `uv pip compile requirements-dev.in` + body diff vs committed lock |

CI and local maintainers share one implementation — no inline compile in workflow YAML.

### 3. Documentation

- `doc/dev/setup.md` — note CI runs `check-lock-dev` on every push/PR.
- `doc/dev/testing.md` — new § CI lock verification; extend pip cache scope table.

## Out of Scope

- Production `check-lock` CI job (PYPOST-779 follow-up debt).
- Wiring `check-lock-dev` into `make check` (would require local `uv` for all contributors).
- Dev CVE scanning (`pip-audit` on dev lock — PYPOST-805).

## Dependency graph

```
requirements-dev.in
        │
        ▼
  uv pip compile (Makefile check-lock-dev)
        │
        ▼
  diff vs requirements-dev.txt ──► CI job pass/fail
```
