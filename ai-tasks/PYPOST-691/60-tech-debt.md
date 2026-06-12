# PYPOST-691: Technical Debt Analysis

**Task type:** Dependencies and supply chain audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Twelve remediation items for follow-up ticketing (no Jira links in this file).

## Shortcuts Taken

- **Static analysis primary:** `requirements.txt`, Makefile, and CI YAML review; PyPI metadata for
  `mcp` SDK; no committed lock file to diff.
- **pip-audit incomplete:** Full resolved-tree CVE scan attempted but did not complete on audit
  host (disk constraints). CI recommendation stands; specific CVE IDs not enumerated.
- **No code fixes in scope:** Pinning, Dependabot, and lock-file adoption deferred to follow-ups.
- **License spot-check only:** MIT/LGPL noted; no full transitive `pip-licenses` export committed.

## Code Quality Issues

Dependency management gaps in the repository (not introduced by this task):

- **Unpinned production graph (P1):** 14 of 15 direct deps have no version pin; fresh installs are
  non-deterministic.
- **MCP v2 exposure (P1):** Bare `mcp` without `<2` upper bound amid 2.0.0a1 pre-release.
- **No CVE CI gate (P1):** Tests run without `pip-audit` or Dependabot security PRs.
- **No lock file (P2):** Cannot reproduce exact transitive trees from git alone.
- **Dev deps duplicated (P2):** Makefile and CI both unpinned-install pytest/flake8 stacks.

## Missing Tooling

- No `requirements-dev.txt` or `pyproject.toml` optional `dev` extra
- No `pip-audit` / OSV CI job
- No `.github/dependabot.yml`
- No `pip-licenses` or SPDX inventory in repo

## Performance Concerns

N/A for this audit. Install time and wheel size (OTel SDK, PySide6) not profiled.

## Follow-up Tasks

### P1 — Critical / breaking upgrades or missing CVE gate

#### R-P1-001 — Pin direct dependencies; bound mcp below v2

- **Priority:** P1
- **Recommendation ID:** R-P1-001
- **Finding refs:** P-003, P-004
- **Description:** `requirements.txt` leaves 14 packages unpinned. The MCP SDK has 2.0.0a1 on PyPI
  with breaking changes expected at v2 stable; maintainers recommend `mcp>=1.27,<2`.
- **Remediation:** Pin all direct deps to tested versions (exact or compatible release). Add
  `mcp>=1.27,<2` immediately; regenerate when v2 migration is planned. Consider `pip-compile` output
  as the single source of truth.
- **Jira:** [PYPOST-777](https://pypost.atlassian.net/browse/PYPOST-777)

#### R-P1-002 — Add pip-audit to CI

- **Priority:** P1
- **Recommendation ID:** R-P1-002
- **Finding refs:** V-001
- **Description:** No automated scan for known vulnerabilities in `cryptography`, `requests`,
  `starlette`, `uvicorn`, or MCP transitive deps before merge.
- **Remediation:** Add CI job: `pip install pip-audit && pip-audit -r requirements.txt` (or audit
  lock file). Fail on known critical/high CVEs; document exception process. Enable GitHub Dependabot
  security alerts as complement.

### P2 — Reproducibility and automation gaps
- **Jira:** [PYPOST-778](https://pypost.atlassian.net/browse/PYPOST-778)

#### R-P2-001 — Commit a lock file

- **Priority:** P2
- **Recommendation ID:** R-P2-001
- **Finding refs:** P-001
- **Description:** Identical `requirements.txt` can resolve different transitive versions over time.
- **Remediation:** Adopt `pip-tools` (`requirements.in` + `requirements.txt` compiled) or `uv lock`;
  CI installs from lock; document upgrade workflow in `doc/dev/setup.md`.
- **Jira:** [PYPOST-779](https://pypost.atlassian.net/browse/PYPOST-779)

#### R-P2-002 — Consolidate dev dependencies

- **Priority:** P2
- **Recommendation ID:** R-P2-002
- **Finding refs:** D-002
- **Description:** `pytest`, `flake8`, `pytest-cov`, `pytest-timeout` install from duplicate unpinned
  lines in `Makefile` and `.github/workflows/test.yml`.
- **Remediation:** Add `requirements-dev.txt` with pins; `make install-dev` and CI reference it.
  Remove drift between Makefile and workflow.
- **Jira:** [PYPOST-780](https://pypost.atlassian.net/browse/PYPOST-780)

#### R-P2-003 — Add Dependabot for pip and Actions

- **Priority:** P2
- **Recommendation ID:** R-P2-003
- **Finding refs:** A-001
- **Description:** No `.github/dependabot.yml`; dependency updates are manual.
- **Remediation:** Configure weekly Dependabot for `requirements.txt` (or lock), and for
  `github-actions` ecosystem on `test.yml`.
- **Jira:** [PYPOST-781](https://pypost.atlassian.net/browse/PYPOST-781)

#### R-P2-004 — Align pydantic constraint with MCP SDK

- **Priority:** P2
- **Recommendation ID:** R-P2-004
- **Finding refs:** P-005
- **Description:** Project declares `pydantic>=2.0`; MCP 1.27.x requires `>=2.11,<3`.
- **Remediation:** Change to `pydantic>=2.11,<3` in requirements input; verify collection/settings
  models on lower bound.
- **Jira:** [PYPOST-782](https://pypost.atlassian.net/browse/PYPOST-782)

#### R-P2-005 — Reconcile starlette and uvicorn direct declarations

- **Priority:** P2
- **Recommendation ID:** R-P2-005
- **Finding refs:** M-001
- **Description:** `starlette` and `uvicorn` are both direct requirements and `mcp` dependencies.
- **Remediation:** After lock-file adoption, drop redundant direct lines **or** document why explicit
  pins override SDK ranges (e.g. security backport). Ensure `metrics_server.py` and MCP share tested
  combo.
- **Jira:** [PYPOST-783](https://pypost.atlassian.net/browse/PYPOST-783)

#### R-P2-006 — Pin GitHub Actions to commit SHAs

- **Priority:** P2
- **Recommendation ID:** R-P2-006
- **Finding refs:** A-002, PYPOST-89
- **Description:** Workflow uses `@v4`/`@v5` tags on third-party actions.
- **Remediation:** Pin `actions/checkout`, `setup-python`, `upload-artifact` to full SHAs; use
  Dependabot `github-actions` ecosystem to bump SHAs.

### P3 — Hygiene and documentation
- **Jira:** [PYPOST-784](https://pypost.atlassian.net/browse/PYPOST-784)

#### R-P3-001 — Introduce pyproject.toml

- **Priority:** P3
- **Recommendation ID:** R-P3-001
- **Finding refs:** P-002, PYPOST-434
- **Description:** No PEP 621 metadata, optional extras, or unified tool config.
- **Remediation:** Add minimal `pyproject.toml` with `[project]` dependencies, `[project.optional-dependencies]
  dev` and `otel`, pytest `pythonpath` if desired.
- **Jira:** [PYPOST-785](https://pypost.atlassian.net/browse/PYPOST-785)

#### R-P3-002 — Document PySide6 LGPL obligations

- **Priority:** P3
- **Recommendation ID:** R-P3-002
- **Finding refs:** L-002
- **Description:** PySide6 is LGPL-3.0; no distributor guidance in `doc/dev/`.
- **Remediation:** Add short `doc/dev/licensing.md` covering Qt dynamic linking, notice files, and
  when obligations apply.
- **Jira:** [PYPOST-786](https://pypost.atlassian.net/browse/PYPOST-786)

#### R-P3-003 — Optional OpenTelemetry dependency group

- **Priority:** P3
- **Recommendation ID:** R-P3-003
- **Finding refs:** O-001
- **Description:** `opentelemetry-api` and `opentelemetry-sdk` install for all users; Prometheus is
  default.
- **Remediation:** Move to optional extra; document `pip install -e ".[otel]"` or overlay requirements
  file; keep OTel tests installing extra in CI matrix.
- **Jira:** [PYPOST-787](https://pypost.atlassian.net/browse/PYPOST-787)

#### R-P3-004 — Refresh setup.md dependency list

- **Priority:** P3
- **Recommendation ID:** R-P3-004
- **Finding refs:** setup.md gap
- **Description:** `doc/dev/setup.md` lists 5 of 15 production packages under "Key Dependencies".
- **Remediation:** Expand list or link to `dependencies_audit.md` inventory table; mention MCP stack
  and encryption packages.
- **Jira:** [PYPOST-788](https://pypost.atlassian.net/browse/PYPOST-788)

## Summary

| Priority | Count | IDs |
| --- | ---: | --- |
| P1 | 2 | R-P1-001, R-P1-002 |
| P2 | 6 | R-P2-001 – R-P2-006 |
| P3 | 4 | R-P3-001 – R-P3-004 |

**Verdict:** Audit complete. Supply-chain hardening is schedulable via follow-ups above; no
application code changes required to close PYPOST-691.
