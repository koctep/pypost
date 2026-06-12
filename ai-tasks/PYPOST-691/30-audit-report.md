# PYPOST-691: Dependencies and Supply Chain Audit Report

**Task:** PYPOST-691 — Audit: dependencies and supply chain
**Date:** 2026-06-12
**Scope:** `requirements.txt`, dev/prod install paths, MCP/ASGI stack, cryptography/HTTP surface,
license posture, Dependabot/CI automation
**Baseline:** `doc/dev/setup.md`, `doc/dev/mcp_integration.md`, `doc/dev/testing.md`,
`.github/workflows/test.yml`, `Makefile`
**Methodology:** Static inventory of `requirements.txt`, Makefile/CI workflow review, MCP import
trace, PyPI metadata for `mcp` SDK (v1.27.2 / v2.0.0a1), cross-reference PYPOST-89 CI notes.
Local `pip-audit` was attempted but could not complete a full resolved-tree scan on the audit host
(disk constraints during install). No application code changes.

## Executive Summary

PyPost declares **15 production dependencies** in `requirements.txt`. **Fourteen are fully
unpinned**; only `pydantic>=2.0` sets a lower bound. There is **no** `pyproject.toml`, lock file,
`pip-audit` CI step, or Dependabot configuration. Dev tools (`pytest`, `flake8`, etc.) install from
unpinned `pip install` lines duplicated in `Makefile` and GitHub Actions.

**Three areas need attention:**

1. **Unpinned production graph** — Every `pip install -r requirements.txt` can pull new major/minor
   releases, including `mcp` **2.0.0a1** (pre-release on PyPI as of 2026-06-11) while the SDK
   documents `mcp>=1.27,<2` until v2 stable.
2. **No automated vulnerability gate** — CI runs tests and coverage but does not scan dependencies
   for known CVEs (`pip-audit`, OSV, or equivalent).
3. **Supply-chain automation gaps** — No Dependabot for pip or Actions; workflow uses major-version
   action tags (`@v4`, `@v5`) rather than immutable SHAs (noted in PYPOST-89).

**Positive findings:** Production and dev dependencies are **not commingled** in `requirements.txt`
(test tooling stays in Makefile/CI). CI pip wheel cache keys on `requirements.txt` content hash
(PYPOST-311). MIT-licensed project stack is predominantly permissive; PySide6 LGPL is the main
distribution consideration.

| Category | Count |
| --- | ---: |
| Direct production deps | 15 |
| Pinned (exact or bounded) | 1 (`pydantic>=2.0`) |
| Dev-only packages (not in requirements.txt) | 4 |
| Dependabot configs | 0 |
| CI vulnerability scanners | 0 |

---

## Direct Dependency Inventory (AC-1)

| # | Package | Pin in `requirements.txt` | Role |
| ---: | --- | --- | --- |
| 1 | `PySide6` | none | Qt GUI |
| 2 | `requests` | none | Outbound HTTP |
| 3 | `PyYAML` | none | YAML body / env parsing |
| 4 | `jinja2` | none | Request templating |
| 5 | `pydantic` | `>=2.0` | Settings/collection models |
| 6 | `platformdirs` | none | Config/user data paths |
| 7 | `mcp` | none | MCP server SDK |
| 8 | `starlette` | none | ASGI routing (MCP + metrics) |
| 9 | `uvicorn` | none | ASGI server process |
| 10 | `prometheus_client` | none | Default metrics exporter |
| 11 | `opentelemetry-api` | none | Alternate metrics API |
| 12 | `opentelemetry-sdk` | none | Alternate metrics SDK |
| 13 | `sseclient-py` | none | SSE response probe in `HTTPClient` |
| 14 | `cryptography` | none | Fernet encryption at rest |
| 15 | `keyring` | none | OS key store for encryption keys |

**Impact:** Identical `requirements.txt` on different dates can yield different resolved trees.
Reproducing production bugs or CVE fixes requires recording what was actually installed — not
represented in-repo today.

### P-001 — No lock file or constraints file (P2)

No `requirements.lock`, `constraints.txt`, or `uv.lock`. `make install` and CI always resolve
latest compatible versions per unpinned names.

**Evidence:** Repository root contains only `requirements.txt`.

**Impact:** Non-reproducible builds; incident response cannot replay exact dependency versions from
git history alone.

### P-002 — No `pyproject.toml` / packaging metadata (P3)

Project has no PEP 621 project table, optional dependency extras, or tool configuration centralization
(PYPOST-434). `pip install -e .` is unsupported; tests use `pytest.ini` `pythonpath = .`.

**Impact:** Cannot express `dev` / `otel` / `mcp` extras; dependency policy scattered across Makefile
and CI YAML.

---

## Version Pinning and Reproducibility

### P-003 — All production packages unpinned except pydantic lower bound (P1)

Only `pydantic>=2.0` constrains versions. The MCP SDK requires `pydantic>=2.11,<3` — the looser
project constraint allows installs the SDK does not test.

**Evidence:** `requirements.txt` lines 1–15; PyPI `mcp` 1.27.2 metadata.

**Impact:** Silent upgrades on every fresh install; harder bisect when regressions are dependency-
driven.

### P-004 — `mcp` without upper bound amid v2 pre-release (P1)

The official MCP Python SDK published **2.0.0a1** on 2026-06-11. Maintainers document adding
`mcp>=1.27,<2` before v2 stable (target 2026-07-27). PyPost lists bare `mcp`.

**Evidence:** `requirements.txt` line 7; [python-sdk README](https://github.com/modelcontextprotocol/python-sdk).

**Impact:** Future `pip install` may pull MCP v2 with breaking ASGI/tool API changes, breaking inbound
agent connectivity without a deliberate upgrade.

### P-005 — pydantic constraint weaker than MCP SDK (P2)

| Source | Constraint |
| --- | --- |
| `requirements.txt` | `pydantic>=2.0` |
| `mcp` 1.27.x | `pydantic>=2.11,<3` |

**Impact:** Theoretically allows pydantic 2.0–2.10 with current requirements file; MCP stack may fail
at import or runtime. In practice pip likely installs ≥2.11 via `mcp`, but the declared project floor
is misleading.

---

## Dev vs Production Dependencies (AC-2)

### D-001 — Test/lint tools correctly excluded from `requirements.txt` (PASS)

`pytest`, `pytest-cov`, `pytest-timeout`, and `flake8` are **not** production dependencies.

**Evidence:** `Makefile` `venv-test` target; CI `Install test tools` step.

### D-002 — Dev tool versions unpinned and duplicated (P2)

| Location | Command |
| --- | --- |
| `Makefile` | `pip install pytest flake8 pytest-cov pytest-timeout` |
| `.github/workflows/test.yml` | `pip install pytest pytest-cov flake8 pytest-timeout` |

No version pins, no shared `requirements-dev.txt`. Makefile and CI can diverge over time.

**Impact:** "Works on my machine" test/lint behavior; CI cannot be reproduced from a single locked
dev manifest.

### D-003 — flake8 installed in CI but not executed (P3)

PYPOST-89 TD-2: flake8 is installed in the test workflow but no step runs `make lint` or `flake8`.

**Impact:** False impression of lint gating; supply-chain cost of an unused package each CI run.

---

## MCP Stack Versions (AC-3)

### Direct MCP-related imports

| Module | Third-party imports |
| --- | --- |
| `mcp_server_impl.py` | `mcp.server.Server`, `mcp.types`, `starlette.*` |
| `mcp_server.py` | uvicorn lifecycle (via manager) |
| `mcp_streamable_http.py` | MCP streamable HTTP helpers |
| `mcp_legacy_sse.py` | Starlette ASGI SSE |
| `metrics_server.py` | Starlette + uvicorn (metrics scrape) |

### M-001 — Redundant direct `starlette` and `uvicorn` declarations (P2)

Both packages are **required dependencies of `mcp`** with minimum versions enforced by the SDK.
PyPost also lists them as top-level requirements.

**Evidence:** `requirements.txt` lines 7–9; PyPI `mcp` dependency table.

**Impact:** Ambiguous ownership of version pins; manual bumps to `starlette`/`uvicorn` could conflict
with SDK-tested ranges. Consider relying on `mcp` constraints or pinning only after lock-file adoption.

### M-002 — Known `mcp` transitive dependencies expand attack surface (PASS with note)

Installing `mcp` pulls (non-exhaustive): `httpx`, `httpx-sse`, `jsonschema`, `pydantic-settings`,
`pyjwt[crypto]`, `python-multipart`, `sse-starlette`, `anyio`. These are **inbound/outbound network
and crypto parsers** — appropriate for MCP but should be covered by CVE scanning.

**Impact:** Vulnerability in any transitive dep affects PyPost MCP surfaces; invisible without lock +
audit.

### M-003 — `sseclient-py` is separate from MCP server transport (PASS)

Used in `http_client.py` for operator SSE response probing, not MCP inbound server. Justified
production dep (PYPOST-39).

---

## CVE and Vulnerability Scanning (AC-4)

### V-001 — No `pip-audit` or equivalent in CI (P1)

`.github/workflows/test.yml` installs dependencies and runs pytest/coverage. No step runs
`pip-audit`, `safety`, or GitHub Dependabot security alerts for pip (Dependabot not configured).

**Evidence:** Workflow file; absent `.github/dependabot.yml`.

**Impact:** Known CVEs in `cryptography`, `requests`, `urllib3`, `starlette`, `uvicorn`, or
transitive `httpx`/`pyjwt` reach merges without an automated gate.

### V-002 — High-risk packages unpinned (P2 — overlaps P-003)

| Package | Risk category |
| --- | --- |
| `cryptography` | Crypto primitives for secrets at rest |
| `requests` | Outbound HTTP, redirects, TLS |
| `starlette` / `uvicorn` | Inbound HTTP parsing (MCP, metrics) |
| `PyYAML` | YAML parsing (typical `safe_load` usage — verify at code level) |
| `jinja2` | Template engine (sandboxed by policy) |

**Impact:** Even with pip-audit, unpinned versions mean CI may scan different versions day-to-day
until pins or locks exist.

### V-003 — Local pip-audit attempt (NOTE)

Audit host attempted `pip-audit -r requirements.txt` after `make install`. Full scan did not
complete due to disk space during environment provisioning. **Recommendation:** add CI job that runs
`pip-audit -r requirements.txt` (or on lock file) on every PR.

---

## License Compatibility (AC-5)

### L-001 — Project MIT license aligned with most dependencies (PASS)

Root `LICENSE` is MIT. Core Python stack (`requests`, `jinja2`, `pydantic`, `mcp`, `starlette`,
`uvicorn`, `prometheus_client`, `cryptography`) uses MIT/Apache/BSD-style licenses per PyPI.

### L-002 — PySide6 LGPL not documented for distributors (P3)

PySide6 is LGPL-3.0. Shipping standalone binaries or app bundles triggers Qt LGPL obligations
(dynamic linking notice, license text, object code offer). No `doc/dev/` licensing guide exists.

**Impact:** Low for source-only development; relevant if the project publishes installers or
commercial redistribution.

### L-003 — No transitive license inventory (P3)

No `pip-licenses` output or `LICENSES/` directory checked into the repo.

**Impact:** Enterprise adopters may require SPDX/CSV attribution; manual effort per release.

---

## Dependabot and CI Supply Chain (AC-4, AC-6)

### A-001 — No Dependabot configuration (P2)

No `.github/dependabot.yml` for:
- pip (`requirements.txt`)
- GitHub Actions (`test.yml`)

**Impact:** Dependency and action updates rely on manual monitoring; security advisories are not
auto-PR'd.

### A-002 — GitHub Actions use floating major tags (P2)

`actions/checkout@v4`, `actions/setup-python@v5`, `actions/upload-artifact@v4` — documented in
PYPOST-89 as acceptable but not SHA-pinned.

**Impact:** Low immediate risk for GitHub-owned actions; supply-chain hardening gap for paranoid
deployments.

### A-003 — Pip cache invalidates on `requirements.txt` hash only (PASS)

PYPOST-311: `cache-dependency-path: requirements.txt`. Unpinned names mean **cache hits still
install different versions** when PyPI publishes updates without requirements edits.

**Impact:** Cache improves speed but does not improve reproducibility.

### A-004 — CI Python matrix 3.11 and 3.13 (PASS)

Tests run on two Python versions; dependency resolution may differ (wheels, transitive deps).

---

## Observability Dependencies (cross-cutting)

| Package | Default path | Notes |
| --- | --- | --- |
| `prometheus_client` | **Yes** — `MetricsRegistry` | Production metrics |
| `opentelemetry-api` | Optional | `OtelMetricsTracker` swap-in |
| `opentelemetry-sdk` | Optional | Required for OTel export tests |

### O-001 — OpenTelemetry SDK in production requirements (P3)

Both OTel packages install for all users though Prometheus is the default metrics backend
(`metrics_registry.py`). Increases install size and CVE surface for operators who never enable OTel.

**Remediation:** Move to `[project.optional-dependencies] otel` when `pyproject.toml` exists, or
`requirements-otel.txt` overlay.

---

## Documentation Alignment

| Document | Status |
| --- | --- |
| `doc/dev/setup.md` | Lists 5 of 15 deps under "Key Dependencies" — **incomplete** (P3) |
| `doc/dev/mcp_integration.md` | Accurate architecture; does not document SDK version policy |
| `doc/dev/testing.md` | Documents CI pip cache; no CVE scan mention |
| `doc/dev/environment_encryption_at_rest.md` | Notes `keyring` in requirements |

---

## Prioritized Recommendations

| ID | Priority | Finding refs | Title |
| --- | --- | --- | --- |
| R-P1-001 | **P1** | P-003, P-004 | Pin direct dependencies; add `mcp>=1.27,<2` upper bound |
| R-P1-002 | **P1** | V-001 | Add `pip-audit` (or OSV) CI job on requirements/lock |
| R-P2-001 | P2 | P-001 | Adopt lock file (`pip-compile` or `uv lock`) committed to repo |
| R-P2-002 | P2 | D-002 | Consolidate dev deps in `requirements-dev.txt` with pins |
| R-P2-003 | P2 | A-001 | Add Dependabot for pip and GitHub Actions |
| R-P2-004 | P2 | P-005 | Align `pydantic` constraint with MCP SDK (`>=2.11,<3`) |
| R-P2-005 | P2 | M-001 | Reconcile redundant `starlette`/`uvicorn` direct declarations |
| R-P2-006 | P2 | A-002 | Pin GitHub Actions to full commit SHAs |
| R-P3-001 | P3 | P-002 | Introduce `pyproject.toml` for metadata and optional extras |
| R-P3-002 | P3 | L-002 | Document PySide6 LGPL distribution obligations |
| R-P3-003 | P3 | O-001 | Split OpenTelemetry deps into optional extra |
| R-P3-004 | P3 | setup.md gap | Refresh `setup.md` dependency list to match requirements.txt |

### Priority counts

| Priority | Count | Remediation IDs |
| --- | ---: | --- |
| **P1** | 2 | R-P1-001, R-P1-002 |
| **P2** | 6 | R-P2-001 – R-P2-006 |
| **P3** | 4 | R-P3-001 – R-P3-004 |
| **Total** | **12** | |

---

## Out of Scope

- Implementing pins, lock files, Dependabot, or pip-audit (recommendations only)
- Resolving specific CVE IDs (requires successful pip-audit/OSV run on locked tree)
- npm, Docker base images, or macOS/Windows code-signing supply chain
- Full transitive license legal review

## Related Tickets

- PYPOST-89 — CI workflow; Actions tag pinning note
- PYPOST-311 — Pip cache keyed on `requirements.txt`
- PYPOST-434 — Missing `pyproject.toml` / `PYTHONPATH` history
- PYPOST-579 — OpenTelemetry dependencies added to `requirements.txt`

**Follow-up tracking:** `60-tech-debt.md` (no Jira links per audit epic convention)
