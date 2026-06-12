# PYPOST-690: Documentation and ADR Alignment Audit Report

**Task:** PYPOST-690 — Audit documentation and ADR alignment
**Date:** 2026-06-12
**Scope:** `doc/dev/` completeness, stale docs vs code, missing ADR index, cross-links between
audit docs, README TOC, ai-tasks artifact quality
**Baseline:** PYPOST-684 doc alignment section, `doc/dev/README.md`, seven Code Audit summaries
**Methodology:** File inventory, TOC diff, module-count verification, audit cross-link matrix,
ai-tasks metrics. No code changes.

## Executive Summary

PyPost developer documentation is **substantive** (60 files under `doc/dev/`, seven Code Audit
summaries with full `ai-tasks/` reports). `architecture.md` matches the live tree (141 Python
modules). Capability docs for request execution, MCP, and templating align with code (verified
PYPOST-684).

**Three areas need immediate attention:**

1. **Incomplete dev README TOC (P1)** — Half of `doc/dev/` files are absent from the table of
   contents, including `request_execution.md`, `template_service.md`, and `collection_loading.md`.
2. **No ADR index (P1)** — No `doc/adr/` directory. Architectural decisions are scattered across
   `ai-tasks/` and inline PYPOST references.
3. **Audit summary inconsistency (P2)** — `architecture_audit.md` and `security_audit.md` embed
   Jira URLs; newer audits defer to `60-tech-debt.md`. No unified Code Audit hub existed before
   this task.

Secondary findings: `solid_audit.md` mixes pre-refactor MainWindow LOC with current baseline;
root `README.md` lacks a developer docs link; `tech_debt_inventory.md` not in TOC; 76 ai-tasks
folders missing `60-tech-debt.md`.

Findings use **P1** (onboarding blocker), **P2** (discoverability/consistency), **P3** (minor
hygiene).

---

## doc/dev Inventory

| Signal | Value |
| --- | ---: |
| Markdown files (excl. `README.md`) | 60 |
| `tech-debt/` subdirectory files | 8 |
| README TOC entries | 30 |
| Missing from TOC | **30 (50%)** |
| Broken TOC links | 0 |

### Missing from TOC (grouped)

| Category | Files |
| --- | --- |
| Core capability | `request_execution.md`, `template_service.md`, `collection_loading.md`, `collection_storage.md`, `state_manager.md`, `request_data_copy_policy.md` |
| UI / editor | `gui_testing.md`, `hotkeys.md`, `json_syntax_highlighting.md`, `ui_mixins.md`, `settings_dialog.md`, `environments_dialog.md`, `method_body_autoswitch.md`, `open_request_in_isolated_tab.md` |
| Collections | `collection_tree_actions.md`, `collection_tree_performance.md`, `copy_curl.md` |
| Security / variables | `mcp_secrets_policy.md`, `sensitive_data_masking_policy.md`, `variable_propagation.md`, `variable_validation.md` |
| Tech debt | `tech_debt_inventory.md`, `tech-debt/PYPOST-*.md` (8 files) |

**Assessment (P1 — D-001):** New contributors must use search to find half of developer docs.
Critical execution and templating guides are not linked from the hub page.

---

## Stale Documentation vs Code

### architecture.md (PASS — post PYPOST-684)

| Claim | Live code | Status |
| --- | --- | --- |
| 141 Python modules | 141 (`find pypost -name '*.py'`) | PASS |
| core 68 / ui 61 / models 6 | 68 / 61 / 6 | PASS |
| Directory tree | Matches major subsystems | PASS |

### Capability docs (PASS — PYPOST-684 sample)

| Document | Alignment |
| --- | --- |
| `request_execution.md` | Pipeline, history, cancellation — aligned |
| `mcp_integration.md` | Threading, transports, per-call service — aligned |
| `template_service.md` | Consumer matrix — aligned |
| `collection_loading.md` | Presenter → `RequestManager` — aligned |
| `state_manager.md` | Debounced session state — aligned (not in TOC) |

### Stale or misleading narratives

| ID | Document | Finding | Severity |
| --- | --- | --- | --- |
| D-002 | `solid_audit.md` | MainWindow section cites "1040 at audit time" alongside 282/246 baseline without strikethrough or "resolved (PYPOST-43)" marker | **P2** |
| D-003 | `testability.md` | Composition-root table omits `HistoryManager`, `RequestManager`, `MCPServerManager` (noted PYPOST-684) | P2 |
| D-004 | `ai-tasks/PYPOST-376/baseline-metrics.md` | MainWindow file LOC 282 in file vs 383 from live `wc -l` — snapshot drift | P3 |

### User vs developer MCP docs

| File | Audience | Cross-link |
| --- | --- | --- |
| `doc/mcp_integration.md` | End user | No link to dev guide |
| `doc/dev/mcp_integration.md` | Developer | No link to user guide |

**Assessment (P3 — D-005):** Intentional split, but mutual links would reduce confusion.

---

## ADR Alignment

| Signal | Status |
| --- | --- |
| `doc/adr/` directory | **Absent** |
| Formal ADR files | **0** |
| Decisions in `ai-tasks/*/20-architecture.md` | Hundreds |
| Inline `PYPOST-N` in dev docs | Common |
| Central index | **None** |

**Representative decisions without ADR index entry:**

| Decision | Primary artifact |
| --- | --- |
| Presenter split (MainWindow decomposition) | PYPOST-43, `solid_audit.md` |
| Composition root in `main.py` | PYPOST-404, `testability.md` |
| Async encrypted env storage | PYPOST-486, `environment_storage_async.md` |
| MCP threading model | `mcp_integration.md`, PYPOST-556 |
| MetricsManager injection | PYPOST-44/167 |

**Assessment (P1 — D-006):** Architectural knowledge is recoverable only by searching closed
task folders or reading long capability docs. No lightweight index for onboarding.

---

## Audit Doc Cross-Links

### Matrix (sibling `*_audit.md` links)

| Doc | Links to siblings | Links to full report | Jira in dev summary |
| --- | ---: | --- | --- |
| `architecture_audit.md` | 1 (solid) | Yes | **Yes** |
| `security_audit.md` | 1 (architecture) | Yes | **Yes** |
| `test_audit.md` | 0 | Yes | Partial text |
| `maintainability_audit.md` | 2 | Yes | Partial text |
| `observability_audit.md` | 2 | Yes | No |
| `performance_audit.md` | 2 | Yes | No |
| `solid_audit.md` | 0 | Yes | **Yes** (inline) |

**Assessment (P2 — D-007):** `test_audit.md` does not link to security or architecture audits
despite overlapping concerns (log guardrails, masking). Jira URL style diverges between early and
late Code Audit dev summaries.

### Code Audit hub

Before PYPOST-690, no single page listed all seven audits with report links. `documentation_audit.md`
(now Step 7) fills this gap.

---

## README Navigation

| Entry point | Dev docs link | Notes |
| --- | --- | --- |
| `doc/dev/README.md` | Self | TOC incomplete (50%) |
| Root `README.md` | **Missing** | Links `doc/prometheus_monitoring.md`, `doc/mcp_integration.md` only |
| `doc/README.md` (user) | No dev link | Expected |

**Assessment (P2 — D-008):** Root README "## Development" lists Make targets but not
`doc/dev/README.md`.

---

## ai-tasks Artifact Quality

| Metric | Value |
| --- | ---: |
| Total `ai-tasks/PYPOST-*` folders | 595 |
| With `00-roadmap.md` | 590 |
| With `60-tech-debt.md` | 519 |
| Missing `60-tech-debt.md` | **76** |
| ≤2 markdown files | **95** |
| Code Audit full set (684–689) | 8 files each |
| PYPOST-40 (legacy audit) | 5 files (partial pattern) |

### Code Audit tasks (PASS)

PYPOST-684 through PYPOST-689 each contain: `00-roadmap`, `10-requirements`, `20-architecture`,
`30-audit-report`, `40-code-cleanup`, `50-observability`, `60-tech-debt`, `70-dev-docs`.

### Thin / stub folders (sample)

| Folder | Files |
| --- | --- |
| PYPOST-328, 333–350 (sample) | `00-roadmap.md` only |
| PYPOST-312 | `60-tech-debt.md` only |

**Assessment (P2 — D-009):** Roadmap-only stubs and missing Step 6 debt files make historical
task context harder to navigate. Not a blocker for current Code Audit quality.

---

## Findings Summary

| ID | Severity | Topic | Recommendation |
| --- | --- | --- | --- |
| D-001 | P1 | 50% of doc/dev missing from TOC | Expand README TOC by category |
| D-006 | P1 | No ADR index | Create `doc/adr/README.md` with decision index |
| D-007 | P2 | Inconsistent audit cross-links / Jira in summaries | Unified hub; standardize follow-up tables |
| D-002 | P2 | Stale solid_audit MainWindow narrative | Mark PYPOST-43 resolved; cite baseline-metrics |
| D-008 | P2 | Root README lacks dev docs link | Add link under Development |
| D-009 | P2 | tech_debt_inventory not in TOC | Add Tech Debt section to README |
| D-009b | P2 | 76 tasks missing 60-tech-debt | Document completion expectations in workflow |
| D-003 | P2 | testability.md composition gaps | Extend table per PYPOST-684 R-P2-001 |
| D-005 | P3 | User/dev MCP docs unlinked | Add mutual cross-links |
| D-004 | P3 | baseline-metrics snapshot drift | Regenerate via audit_baseline_metrics.py |
| D-010 | P3 | prometheus_monitoring not in dev TOC | Add entry (linked from root README) |
| D-011 | P3 | test_audit lacks sibling links | Add Related Audits section |

---

## Methodology Notes

Commands executed (2026-06-12):

```bash
find doc/dev -name '*.md' | wc -l
find pypost -name '*.py' | wc -l
wc -l pypost/ui/main_window.py
rg -l 'atlassian.net/browse' doc/dev/*_audit.md
```

Python TOC diff script documented in `50-observability.md`.

No application code modified.

## Out of Scope

- Rewriting all capability documentation
- Dependencies and supply-chain audit
- User guide (`doc/README.md`) content update
- Creating Jira tickets from findings
- Consolidating 595 ai-tasks folders into a single index
