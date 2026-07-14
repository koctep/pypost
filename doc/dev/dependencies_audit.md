# Dependencies and Supply Chain Audit

This document summarizes the PyPost dependencies and supply chain audit (PYPOST-691). It covers
`requirements.txt`, version pinning, CVE scanning posture, dev vs production installs, the MCP/ASGI
stack, license compatibility, and Dependabot/CI gaps. It complements the security audit in
[security_audit.md](security_audit.md) (PYPOST-685) with a dependency-management lens.

## Audit Report

Full report:
[ai-tasks/PYPOST-691/30-audit-report.md](../../ai-tasks/PYPOST-691/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** 15 direct production dependencies, Makefile/CI install paths

## Executive Summary

| Metric | Value |
| --- | --- |
| Direct production deps | 15 |
| Unpinned direct deps | 1 (`pydantic>=2.0` lower bound only) |
| Lock / constraints file | None |
| `pyproject.toml` | None |
| CI vulnerability scanner | None |
| Dependabot config | None |

**Three areas need attention:**

1. **Production pins adopted** — Direct deps pinned to CI-tested versions; `mcp>=1.27,<2` blocks
   accidental v2 installs ([PYPOST-777](https://pypost.atlassian.net/browse/PYPOST-777)).
2. **No CVE gate in CI** — `cryptography`, HTTP, and ASGI packages are not scanned before merge.
3. **Automation gaps** — No Dependabot; dev tool versions duplicated unpinned in Makefile and CI.

**Positive:** Test tooling is excluded from `requirements.txt`. CI pip cache invalidates when
`requirements.txt` changes (PYPOST-311).

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
| opentelemetry-api | `==1.42.1` | Alternate metrics API |
| opentelemetry-sdk | `==1.42.1` | Alternate metrics SDK |
| sseclient-py | `==1.9.0` | SSE response probe |
| cryptography | `==48.0.1` | Encryption at rest |
| keyring | `==25.7.0` | OS key store |

## Dev vs Production

| Category | Install source | Packages |
| --- | --- | --- |
| Production | `requirements.txt` via `make install` | 15 runtime deps |
| Development | `Makefile` `venv-test` + CI `pip install` | pytest, pytest-cov, pytest-timeout, flake8 |

Dev packages are **not** in `requirements.txt` (good separation) but versions are **unpinned**
and declared in two places (gap).

## MCP Stack

PyPost inbound MCP uses the official `mcp` Python SDK plus direct `starlette` and `uvicorn`.
The SDK also depends on `httpx`, `jsonschema`, `pyjwt[crypto]`, `sse-starlette`, and others.

As of June 2026, MCP SDK **v2.0.0a1** is on PyPI. PyPost should bound `mcp<2` until a deliberate
v2 migration (SDK targets stable v2 July 2026).

See [mcp_integration.md](mcp_integration.md) for runtime architecture.

## License Notes

- **PyPost:** MIT (`LICENSE`)
- **PySide6:** LGPL-3.0 — relevant for binary distribution; see R-P3-002 in tech debt
- **Most Python deps:** MIT / Apache / BSD (permissive)

No transitive license inventory is checked into the repo.

## Prioritized Recommendations

| Priority | ID | Title |
| --- | --- | --- |
| **P1** | R-P1-001 | Pin direct dependencies; add `mcp>=1.27,<2` upper bound |
| **P1** | R-P1-002 | Add `pip-audit` (or OSV) CI job on requirements/lock |
| P2 | R-P2-001 | Commit a lock file (`pip-compile` or `uv lock`) |
| P2 | R-P2-002 | Consolidate dev deps in `requirements-dev.txt` with pins |
| P2 | R-P2-003 | Add Dependabot for pip and GitHub Actions |
| P2 | R-P2-004 | Align `pydantic` constraint with MCP SDK (`>=2.11,<3`) |
| P2 | R-P2-005 | Reconcile redundant `starlette`/`uvicorn` direct declarations |
| P2 | R-P2-006 | Pin GitHub Actions to full commit SHAs |
| P3 | R-P3-001 | Introduce `pyproject.toml` for metadata and optional extras |
| P3 | R-P3-002 | Document PySide6 LGPL distribution obligations |
| P3 | R-P3-003 | Split OpenTelemetry deps into optional extra |
| P3 | R-P3-004 | Refresh `setup.md` dependency list |

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
