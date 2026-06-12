# PYPOST-691: Audit — dependencies and supply chain

## Research

### Dependency declaration surfaces

| Surface | Role | Pinning |
| --- | --- | --- |
| `requirements.txt` | Production/runtime install (`make install`, CI) | 14 unpinned; `pydantic>=2.0` only |
| `Makefile` `venv-test` | Dev tools: pytest, flake8, pytest-cov, pytest-timeout | Unpinned |
| `.github/workflows/test.yml` | CI: same dev tools + `requirements.txt` | Unpinned; pip cache keyed on `requirements.txt` hash |
| `pyproject.toml` | **Absent** | No PEP 621 metadata, no `[project.optional-dependencies]` |
| Lock / constraints | **Absent** | No `requirements.lock`, `constraints.txt`, or `uv.lock` |
| Dependabot | **Absent** | No `.github/dependabot.yml` |

PyPost is **not installed as a package** (`pip install -e .` unsupported). Tests rely on
`pythonpath = .` in `pytest.ini` (PYPOST-434). Runtime imports resolve from the repo root.

### Production dependency map (business view)

```text
Desktop GUI (PySide6)
├── HTTP client (requests) + SSE probe (sseclient-py)
├── Templating (jinja2) + validation (pydantic, PyYAML)
├── Paths (platformdirs)
├── Encryption / secrets (cryptography, keyring)
├── Metrics — default (prometheus_client) | alternate (opentelemetry-api/sdk)
└── MCP inbound server
    ├── mcp SDK (Server, tools, streamable HTTP)
    ├── starlette (ASGI routes, threadpool)
    └── uvicorn (daemon thread server)
```

### MCP stack version coupling

The `mcp` PyPI package (official MCP Python SDK) declares tight dependencies on:

- `starlette>=0.27`, `uvicorn>=0.31.1`, `sse-starlette>=1.6.1`
- `httpx<1.0,>=0.27.1`, `jsonschema>=4.20`, `pydantic>=2.11,<3`
- `pyjwt[crypto]>=2.10.1`, `python-multipart`, `anyio>=4.5`

PyPost lists **`mcp`, `starlette`, and `uvicorn` as separate direct lines** in
`requirements.txt`. Pip resolves a single installed version per package, but duplicate
declarations obscure which layer "owns" the version choice and can drift from SDK-tested
combinations.

As of June 2026, `mcp` **2.0.0a1** is on PyPI; SDK maintainers recommend `mcp>=1.27,<2`
until v2 stable (target July 2026). Unpinned `mcp` may accept a future major without review.

### Dev vs prod separation

| Category | Packages | Install path |
| --- | --- | --- |
| Production | `requirements.txt` (15 lines) | `make install` after `venv-test` |
| Development | pytest, flake8, pytest-cov, pytest-timeout | `Makefile` `venv-test`; CI duplicate `pip install` |
| Not in requirements | flake8 never run in CI (PYPOST-89 TD-2) | Installed but unused in workflow |

**Assessment:** Prod/dev split is **partially correct** (test tools not in `requirements.txt`) but
**versions are not pinned** in either path, and CI duplicates Makefile logic without a shared
`requirements-dev.txt`.

### Security-sensitive dependency surface

| Package | Exposure |
| --- | --- |
| `cryptography` | Fernet encryption for environment secrets at rest |
| `keyring` | OS credential store for encryption keys |
| `requests` / `urllib3` (transitive) | Outbound HTTP from operator and MCP tool execution |
| `starlette` / `uvicorn` | **Inbound** MCP and metrics HTTP listeners (default `0.0.0.0`) |
| `mcp` → `httpx`, `pyjwt` | MCP protocol transport and optional JWT validation |
| `jinja2` | Template rendering (SSTI risk bounded by `FunctionRegistry` policy) |

### License baseline

| Component | License | Notes |
| --- | --- | --- |
| PyPost | MIT (`LICENSE`) | Permissive |
| PySide6 | LGPL-3.0 | Qt dynamic linking; distribution obligations if shipping binaries |
| `mcp` SDK | MIT | Permissive |
| Most Python deps | MIT / Apache / BSD | Typical stack |

No `LICENSES/` or SPDX inventory exists for transitive dependencies.

## Implementation Plan

### Audit methodology

#### 1. Inventory direct dependencies

Parse `requirements.txt`; record pin style per line.

#### 2. Map dev vs prod install paths

Compare `Makefile`, `.github/workflows/test.yml`, and `doc/dev/setup.md`.

#### 3. MCP stack analysis

Review `pypost/core/mcp_server_impl.py` imports; cross-check PyPI `mcp` dependency metadata
(June 2026: v1.27.2 stable, v2.0.0a1 pre-release).

#### 4. CVE / scanning posture

Check CI for `pip-audit`, `safety`, or OSV integration. Attempt local `pip-audit` when environment
permits; document if blocked.

#### 5. Automation gaps

Search for `.github/dependabot.yml`; review Actions pinning (PYPOST-89).

#### 6. License spot-check

MIT project + PySide6 LGPL; note documentation gaps for distributors.

#### 7. Prioritize findings

P1 = breaking upgrades or missing CVE gate; P2 = reproducibility/automation; P3 = hygiene/docs.

### Deliverables (Step 3)

- `30-audit-report.md` — full findings with P1/P2/P3 table
- Cross-links to `doc/dev/mcp_integration.md`, `doc/dev/setup.md`, `doc/dev/testing.md`

### Step 4–7

- Step 4: Markdown artifact hygiene only
- Step 5: Note observability deps (`prometheus_client`, `opentelemetry-*`) in audit meta-doc
- Step 6: `60-tech-debt.md` — 12 follow-ups, no Jira links
- Step 7: `doc/dev/dependencies_audit.md` + `doc/dev/README.md` TOC

## Out of Scope

- Implementing pins, lock files, or CI scanners
- Resolving individual CVEs (recommend process only)
- Legal review of LGPL compliance
