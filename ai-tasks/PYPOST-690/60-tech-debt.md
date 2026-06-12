# PYPOST-690: Technical Debt Analysis

**Task type:** Documentation and ADR alignment audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Twelve remediation items for follow-up ticketing.

## Shortcuts Taken

- **Sampled stale checks:** Full alignment re-verification limited to PYPOST-684 PASS set plus
  `solid_audit.md` and `testability.md`.
- **No TOC rewrite in scope:** Gap measured; remediation deferred to R-P1-001.
- **No ADR files created:** Index recommendation only.

## Code Quality Issues

Not applicable — documentation audit only.

## Missing Tooling

- No automated TOC-vs-disk CI check
- No ADR lint or index generator
- No ai-tasks artifact completeness verifier in `make check`

## Documentation Concerns

See findings D-001 through D-011 in `30-audit-report.md`. Highest impact: incomplete dev README
TOC and absent ADR index block efficient onboarding.

## Follow-up Tasks

### P1 — Critical / onboarding blockers

#### R-P1-001 — Expand doc/dev/README.md table of contents

- **Priority:** P1
- **Finding refs:** D-001
- **Description:** 30 of 60 `doc/dev/` files are missing from the README TOC, including
  `request_execution.md`, `template_service.md`, `collection_loading.md`, and security policy
  docs.
- **Remediation:** Add categorized TOC sections (Core, Collections, UI/Editor, Security,
  Tech Debt). Re-run inventory script until gap is zero for capability docs.
- **Jira:** [PYPOST-765](https://pypost.atlassian.net/browse/PYPOST-765)

#### R-P1-002 — Create ADR index at doc/adr/README.md

- **Priority:** P1
- **Finding refs:** D-006
- **Description:** No `doc/adr/` directory or central index. Decisions are scattered in
  `ai-tasks/` and inline PYPOST references.
- **Remediation:** Add `doc/adr/README.md` listing top decisions (presenter split, composition
  root, async env storage, MCP threading, metrics injection) with links to capability docs and
  originating `ai-tasks/` reports. Link from `doc/dev/README.md` and `architecture.md`.

### P2 — Discoverability and consistency
- **Jira:** [PYPOST-766](https://pypost.atlassian.net/browse/PYPOST-766)

#### R-P2-001 — Maintain Code Audit hub in documentation_audit.md

- **Priority:** P2
- **Finding refs:** D-007
- **Description:** Audit summaries linked inconsistently; no single hub before PYPOST-690.
- **Remediation:** Keep hub table in `documentation_audit.md` updated when new audits land.
  Add "Related Audits" footer to each `*_audit.md` linking siblings.
- **Jira:** [PYPOST-767](https://pypost.atlassian.net/browse/PYPOST-767)

#### R-P2-002 — Refresh solid_audit.md MainWindow narrative

- **Priority:** P2
- **Finding refs:** D-002
- **Description:** MainWindow section mixes audit-era 1040 LOC with post-PYPOST-43 baseline
  without clear resolved status.
- **Remediation:** Strike through or move 1040-era text to history; cite
  `baseline-metrics.md` current caps (383 file / 343 class LOC). Mark PYPOST-43 complete.
- **Jira:** [PYPOST-768](https://pypost.atlassian.net/browse/PYPOST-768)

#### R-P2-003 — Standardize audit dev-doc follow-up tables

- **Priority:** P2
- **Finding refs:** D-007
- **Description:** `architecture_audit.md` and `security_audit.md` embed Jira URLs; PYPOST-688/689
  defer to `60-tech-debt.md` without inline links.
- **Remediation:** Pick one pattern: dev summaries link to `60-tech-debt.md` only; remove inline
  Jira from `doc/dev/*_audit.md` when debt is ticketed separately.
- **Jira:** [PYPOST-769](https://pypost.atlassian.net/browse/PYPOST-769)

#### R-P2-004 — Link root README.md to developer documentation

- **Priority:** P2
- **Finding refs:** D-008
- **Description:** Root README "## Development" lists Make targets but not `doc/dev/README.md`.
- **Remediation:** Add bullet: "Developer documentation — [doc/dev/README.md](doc/dev/README.md)."
- **Jira:** [PYPOST-770](https://pypost.atlassian.net/browse/PYPOST-770)

#### R-P2-005 — Add tech debt inventory to dev README TOC

- **Priority:** P2
- **Finding refs:** D-009
- **Description:** `tech_debt_inventory.md` and `tech-debt/` summaries are not in TOC.
- **Remediation:** Add "Technical Debt" section with inventory link and major audit debt pages.
- **Jira:** [PYPOST-771](https://pypost.atlassian.net/browse/PYPOST-771)

#### R-P2-006 — Document ai-tasks artifact completion expectations

- **Priority:** P2
- **Finding refs:** D-009b
- **Description:** 76 folders lack `60-tech-debt.md`; 95 have ≤2 markdown files.
- **Remediation:** Add subsection to `doc/dev/setup.md` or top-down workflow doc: minimum
  artifacts per closed task; optional `scripts/verify_ai_task_artifacts.py` for CI.

### P3 — Minor hygiene
- **Jira:** [PYPOST-772](https://pypost.atlassian.net/browse/PYPOST-772)

#### R-P3-001 — Add prometheus_monitoring.md to dev README TOC

- **Priority:** P3
- **Finding refs:** D-010
- **Description:** `doc/prometheus_monitoring.md` is linked from root README only.
- **Remediation:** Add cross-link under Observability in dev README (or move to `doc/dev/`).
- **Jira:** [PYPOST-773](https://pypost.atlassian.net/browse/PYPOST-773)

#### R-P3-002 — Cross-link user and developer MCP guides

- **Priority:** P3
- **Finding refs:** D-005
- **Description:** `doc/mcp_integration.md` and `doc/dev/mcp_integration.md` do not reference
  each other.
- **Remediation:** Add "See also" sections at top of each file.
- **Jira:** [PYPOST-774](https://pypost.atlassian.net/browse/PYPOST-774)

#### R-P3-003 — Add sibling audit links to test_audit.md

- **Priority:** P3
- **Finding refs:** D-011
- **Description:** `test_audit.md` links to `testing.md` but not sibling audit summaries.
- **Remediation:** Add Related Audits section (security, observability, maintainability).
- **Jira:** [PYPOST-775](https://pypost.atlassian.net/browse/PYPOST-775)

#### R-P3-004 — Regenerate baseline-metrics snapshot

- **Priority:** P3
- **Finding refs:** D-004
- **Description:** `baseline-metrics.md` MainWindow file LOC (282) drifts from live `wc -l` (383).
- **Remediation:** Run `scripts/audit_baseline_metrics.py --markdown` and commit if caps change.
- **Jira:** [PYPOST-776](https://pypost.atlassian.net/browse/PYPOST-776)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required.
README TOC expansion and ADR index should be scheduled first. Twelve remediation items
documented above.
