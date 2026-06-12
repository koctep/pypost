# PYPOST-691: Audit — dependencies and supply chain

## Goals

PyPost ships as a Python desktop application with an inbound MCP/ASGI network surface,
Prometheus metrics, and cryptography for environment encryption. Dependencies are declared in a
single unpinned `requirements.txt` with dev tooling installed ad hoc via `Makefile` and CI.
Without a structured supply-chain review, silent upgrades, missed CVEs, and MCP SDK breaking
releases can reach operators before the team notices.

This audit establishes an evidence-based picture of **dependency management, pinning,
vulnerability exposure, dev/prod separation, MCP stack versions, license compatibility, and
automation gaps** so remediation can be scheduled.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up items).

## User Stories

- As a **maintainer**, I want direct and transitive dependencies inventoried with pinning status,
  so upgrades are deliberate rather than accidental on `pip install`.
- As a **security reviewer**, I want known CVE scanning gaps and high-risk packages identified,
  so supply-chain risk is visible before incidents.
- As a **release engineer**, I want reproducible install semantics documented, so CI and local
  `make install` resolve the same versions.
- As a **MCP integrator**, I want MCP/Starlette/uvicorn version posture clear, so SDK major
  bumps do not break inbound tool servers without warning.
- As a **tech-debt owner**, I want prioritized follow-ups (P1/P2/P3) without premature Jira
  ticketing, so dependency hardening is schedulable.

## Definition of Done

- [x] An audit report is stored under `ai-tasks/PYPOST-691/` with summary, scope, methodology,
  findings, and recommendations.
- [x] Findings cover `requirements.txt` (and absence of `pyproject.toml` / lock files).
- [x] Findings cover version pinning and reproducibility.
- [x] Findings cover CVE / vulnerability scanning posture (CI and local).
- [x] Findings cover dev vs production dependency separation (`Makefile`, CI).
- [x] Findings cover MCP stack (`mcp`, `starlette`, `uvicorn`, transitive httpx/pyjwt).
- [x] Findings cover license compatibility (MIT project + PySide6 LGPL + transitive deps).
- [x] Findings cover Dependabot / GitHub Actions supply-chain gaps.
- [x] Each significant finding includes impact and a recommended remediation direction.
- [x] Findings are prioritized (P1/P2/P3) for follow-up.
- [x] Developer summary added at `doc/dev/dependencies_audit.md`.
- [x] P1/P2/P3 follow-ups listed in `60-tech-debt.md` without Jira links.

## Task Description

**Problem:** Dependency declarations grew organically as features accumulated (MCP server,
OpenTelemetry alternate metrics, SSE client probe, keyring integration). There is no lock file,
no automated vulnerability scan, and no Dependabot config. The official `mcp` SDK is approaching
v2 with pre-releases on PyPI while `requirements.txt` lists `mcp` without an upper bound.

**Business intent:** Make dependency and supply-chain risk visible and schedulable — reducing
surprise breakages, silent CVE exposure, and non-reproducible CI installs.

### In Scope

- `requirements.txt` direct dependencies (15 packages).
- Absence of `pyproject.toml`, `setup.py`, constraints, or lock files.
- Dev tooling: `Makefile` `venv-test` target, `.github/workflows/test.yml` pip installs.
- MCP server dependency chain (`mcp`, `starlette`, `uvicorn`, transitive SDK deps).
- Security-sensitive packages: `cryptography`, `requests`, `keyring`, `PyJWT` (via `mcp`).
- License posture for distribution (MIT + PySide6 LGPL).
- Dependabot / GitHub Actions version pinning (cross-ref PYPOST-89).

### Out of Scope

- Application code fixes (audit only).
- Implementing lock files, Dependabot, or pip-audit in CI (recommendations only).
- Full license audit of every transitive wheel (spot-check + policy gaps).
- Container base image or OS package supply chain.
- npm or non-Python dependencies.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Report inventories all direct `requirements.txt` entries with pinning status |
| AC-2 | Report documents dev vs prod dependency install paths |
| AC-3 | Report documents MCP stack direct + known transitive dependencies |
| AC-4 | Report documents CVE scanning and Dependabot gaps |
| AC-5 | Report documents license compatibility notes (MIT, LGPL, transitive) |
| AC-6 | Recommendations prioritized P1/P2/P3 with impact statements |
| AC-7 | P1/P2/P3 follow-ups in `60-tech-debt.md` without Jira links |
| AC-8 | `doc/dev/dependencies_audit.md` summary and README TOC entry |

## Q&A

| Question | Answer |
| --- | --- |
| Why audit dependencies now? | MCP SDK v2 pre-releases, unpinned network/crypto stack, and no CI CVE gate increase supply-chain risk as the app gains agent-facing surfaces. |
| Is pip-audit required to close? | Methodology documents whether a live scan ran; static analysis and PyPI metadata suffice when tooling cannot install (disk/resource limits). |
| Are Jira tickets created? | No — follow-ups live in `60-tech-debt.md` only per audit epic convention for PYPOST-688+. |
