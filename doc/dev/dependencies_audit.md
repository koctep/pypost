# Dependencies and Supply Chain Audit

This document summarizes the PyPost dependencies and supply chain audit (PYPOST-691). It covers
`requirements.txt`, version pinning, CVE scanning posture, dev vs production installs, the MCP/ASGI
stack, license compatibility, and Dependabot/CI gaps. It complements the security audit in
[security_audit.md](security_audit.md) (PYPOST-685) with a dependency-management lens.

## Audit Report

Full report:
[ai-tasks/PYPOST-691/30-audit-report.md](../../ai-tasks/PYPOST-691/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** 13 direct production dependencies, Makefile/CI install paths

## Executive Summary

| Metric | Value |
| --- | --- |
| Direct production deps | 13 |
| Unpinned direct deps | 1 (`pydantic>=2.0` lower bound only) |
| Lock / constraints file | `requirements.txt` (uv `pip compile` from `requirements.in`) |
| `pyproject.toml` | PEP 621 metadata + `dev` / `otel` optional extras (PYPOST-785) |
| CI vulnerability scanner | `pip-audit` job in `.github/workflows/test.yml` (PYPOST-778) |
| Dependabot config | `.github/dependabot.yml` (pip + GitHub Actions, weekly) |

**Remaining areas:**

1. **Production pins adopted** — Direct deps pinned to CI-tested versions; `mcp>=1.27,<2` blocks
   accidental v2 installs ([PYPOST-777](https://pypost.atlassian.net/browse/PYPOST-777)).
2. **CVE gate in CI** — `security-audit` job runs `pip-audit -r requirements.txt` on every push/PR
   ([PYPOST-778](https://pypost.atlassian.net/browse/PYPOST-778)).
3. **Automation gaps** — Resolved for dev security tooling: `pip-audit` is pinned in
   `requirements-dev.txt` (PYPOST-805). Production lock CI verification remains local-only.

**Positive:** Test tooling is excluded from `requirements.txt`. CI pip cache invalidates when
`requirements.in` or `requirements.txt` changes (PYPOST-311, PYPOST-779). Dependabot opens weekly
dependency PRs. Transitive production graph is locked via `uv pip compile` (PYPOST-779).

## CVE Scanning (PYPOST-778)

| Context | Command |
| --- | --- |
| CI | Job `security-audit` in `.github/workflows/test.yml` |
| Local | `make security-audit` (requires `make install` first) |

The scan runs `pip-audit -r requirements.txt` against the committed production lock. The
`pip-audit` CLI is pinned in `pyproject.toml` `[dev]` extra (mirrored in `requirements-dev.txt`,
PYPOST-805) — not installed ephemerally — so local and CI share the same scanner version via
`make install` / `pip install -e ".[dev]"`. The job fails when known vulnerabilities are
reported.

**Temporary exceptions:** If a CVE has no fixed release, add `pip-audit --ignore-vuln <CVE-ID>`
to the CI step and document the rationale here. Remove the ignore when a patched version is
available.

## Production Dependencies

| Package | Pinned | Primary role |
| --- | --- | --- |
| PySide6 | `==6.11.1` | Qt GUI |
| requests | `==2.34.2` | Outbound HTTP |
| PyYAML | `==6.0.3` | YAML parsing |
| jinja2 | `==3.1.6` | Request templating |
| pydantic | `>=2.11,<3` | Models / settings |
| platformdirs | `==4.10.0` | Config paths |
| mcp | `>=1.27,<2` | MCP server SDK (pulls starlette/uvicorn) |
| prometheus_client | `==0.25.0` | Default metrics |
| sseclient-py | `==1.9.0` | SSE response probe |
| cryptography | `==48.0.1` | Encryption at rest |
| keyring | `==25.7.0` | OS key store |

## Dev vs Production

| Category | Install source | Packages |
| --- | --- | --- |
| Production | `pyproject.toml` via `make install` (`pip install -e ".[dev,otel]"`) | Runtime deps (direct pins; transitive via lock files) |
| Development | `pyproject.toml` `[dev]` extra via `make venv-test` / CI | pytest, pytest-cov, pytest-timeout, flake8, flake8-print, mypy, pip-audit |
| OTel overlay | `pyproject.toml` `[otel]` extra via `make venv-otel` / `make install` | opentelemetry-api, opentelemetry-sdk |

Dev packages are **not** in `requirements.txt` (good separation). Versions are **pinned** in
`requirements-dev.in` / `requirements-dev.txt` (PYPOST-780).

## MCP Stack

PyPost inbound MCP uses the official `mcp` Python SDK plus direct `starlette` and `uvicorn`.
The SDK also depends on `httpx`, `jsonschema`, `pyjwt[crypto]`, `sse-starlette`, and others.

As of June 2026, MCP SDK **v2.0.0a1** is on PyPI. PyPost should bound `mcp<2` until a deliberate
v2 migration (SDK targets stable v2 July 2026).

See [mcp_integration.md](mcp_integration.md) for runtime architecture.

## License Notes

- **PyPost:** MIT (`LICENSE`)
- **PySide6:** LGPL-3.0 — relevant for binary distribution; see
  [licensing.md](licensing.md) (PYPOST-786)
- **Most Python deps:** MIT / Apache / BSD (permissive)

No transitive license inventory is checked into the repo. Distributor guidance for PySide6:
[licensing.md](licensing.md).

## Prioritized Recommendations

| Priority | ID | Title |
| --- | --- | --- |
| **P1** | R-P1-001 | Pin direct dependencies; add `mcp>=1.27,<2` upper bound |
| **P1** | R-P1-002 | Add `pip-audit` (or OSV) CI job on requirements/lock — **Done (PYPOST-778)** |
| P2 | R-P2-001 | Commit a lock file (`pip-compile` or `uv lock`) — **Done (PYPOST-779)** |
| P2 | R-P2-002 | Consolidate dev deps in `requirements-dev.txt` with pins — **Done (PYPOST-780)** |
| P2 | R-P2-003 | Add Dependabot for pip and GitHub Actions — **Done** |
| P2 | R-P2-004 | Align `pydantic` constraint with MCP SDK (`>=2.11,<3`) |
| P2 | R-P2-005 | Reconcile redundant `starlette`/`uvicorn` direct declarations |
| P2 | R-P2-006 | Pin GitHub Actions to full commit SHAs |
| P3 | R-P3-001 | Introduce `pyproject.toml` for metadata and optional extras — **Done (PYPOST-785)** |
| P3 | R-P3-002 | Document PySide6 LGPL distribution obligations — **Done (PYPOST-786)** |
| P3 | R-P3-003 | Split OpenTelemetry deps into optional extra — **Done (PYPOST-787)** |
| P3 | R-P3-004 | Refresh `setup.md` dependency list — **Done (PYPOST-788)** |

| Priority | Count |
| --- | ---: |
| P1 | 2 |
| P2 | 6 |
| P3 | 4 |

Follow-ups: [ai-tasks/PYPOST-691/60-tech-debt.md](../../ai-tasks/PYPOST-691/60-tech-debt.md)
(no Jira links).

## Related Work

- [PYPOST-89](../../ai-tasks/PYPOST-89/60-review.md) — CI workflow; Actions SHA pinning note
- [PYPOST-311](../../ai-tasks/PYPOST-311/) — Pip cache keyed on `requirements.txt`
- [PYPOST-434](../../ai-tasks/PYPOST-434/10-requirements.md) — No `pyproject.toml`
- [PYPOST-579](../../ai-tasks/PYPOST-579/00-roadmap.md) — OpenTelemetry deps added

## Related Audits

Sibling Code Audit summaries — hub:
[documentation_audit.md § Code Audit Hub](documentation_audit.md#code-audit-hub).

- [Architecture and Package Boundary Audit (PYPOST-684)](architecture_audit.md)
- [Security and Secrets Handling Audit (PYPOST-685)](security_audit.md)
- [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
- [Code Quality and Maintainability Audit (PYPOST-687)](maintainability_audit.md)
- [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
- [Performance and Scalability Audit (PYPOST-689)](performance_audit.md)
- [Documentation and ADR Alignment Audit (PYPOST-690)](documentation_audit.md)
