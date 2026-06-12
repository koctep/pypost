# Documentation and ADR Alignment Audit

This document summarizes the PyPost documentation and ADR alignment audit (PYPOST-690). It
complements the seven Code Audit summaries (PYPOST-684 through PYPOST-689) and the legacy SOLID
audit ([solid_audit.md](solid_audit.md), PYPOST-40).

## Audit Report

Full report:
[ai-tasks/PYPOST-690/30-audit-report.md](../../ai-tasks/PYPOST-690/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** `doc/dev/` completeness, stale docs vs code, ADR index,
audit cross-links, README TOC, ai-tasks artifact quality

## Executive Summary

PyPost has **strong capability documentation** (60 markdown files under `doc/dev/`) and seven
Code Audit developer summaries with links to full `ai-tasks/` reports. `architecture.md` was
refreshed in PYPOST-684 and module counts (141 Python files: 68 core, 61 ui, 6 models) match
the live tree.

**Three areas need attention:**

1. **Incomplete dev README TOC (P1)** — `doc/dev/README.md` lists 30 of 60 files. Critical
   guides (`request_execution.md`, `template_service.md`, `collection_loading.md`,
   `sensitive_data_masking_policy.md`) are absent from the table of contents.
2. **No ADR index (P1)** — No `doc/adr/` directory or central index. Architectural decisions
   live in scattered `ai-tasks/` artifacts and inline PYPOST references in dev docs.
3. **Audit doc fragmentation (P2)** — Seven audit summaries cross-link inconsistently; some
   embed Jira URLs in dev docs while others defer to `60-tech-debt.md` without links.

Findings use **P1** (onboarding blocker or missing structural doc), **P2** (discoverability or
consistency gap), **P3** (minor hygiene).

## Code Audit Hub

| Audit | Dev summary | Full report |
| --- | --- | --- |
| Architecture (684) | [architecture_audit.md](architecture_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-684/30-audit-report.md) |
| Security (685) | [security_audit.md](security_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-685/30-audit-report.md) |
| Tests (686) | [test_audit.md](test_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-686/30-audit-report.md) |
| Maintainability (687) | [maintainability_audit.md](maintainability_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-687/30-audit-report.md) |
| Observability (688) | [observability_audit.md](observability_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-688/30-audit-report.md) |
| Performance (689) | [performance_audit.md](performance_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-689/30-audit-report.md) |
| Documentation (690) | This file | [30-audit-report](../../ai-tasks/PYPOST-690/30-audit-report.md) |
| SOLID (legacy, 40) | [solid_audit.md](solid_audit.md) | [30-audit-report](../../ai-tasks/PYPOST-40/30-audit-report.md) |

## doc/dev Completeness

| Signal | Value |
| --- | ---: |
| Markdown files (excl. README) | 60 |
| README TOC entries | 30 |
| Missing from TOC | 30 (50%) |
| User docs (`doc/`) | 3 files |
| `ai-tasks/` task folders | 595 |

**High-value docs missing from TOC:** `request_execution.md`, `template_service.md`,
`collection_loading.md`, `state_manager.md`, `gui_testing.md`, `mcp_secrets_policy.md`,
`tech_debt_inventory.md`, and the `tech-debt/` subdirectory.

## Stale vs Current Code

| Document | Status | Notes |
| --- | --- | --- |
| `architecture.md` | **Current** | Refreshed PYPOST-684; counts match live tree |
| `request_execution.md` | Aligned | Pipeline matches `RequestService` / `HTTPClient` |
| `mcp_integration.md` | Aligned | Threading and transport verified PYPOST-684 |
| `template_service.md` | Aligned | Consumer matrix current |
| `solid_audit.md` | **Partially stale** | MainWindow narrative mixes audit-era 1040 LOC with post-PYPOST-43 baseline without resolved markers |
| `testability.md` | Minor gap | Omits `HistoryManager` / `RequestManager` in composition table (noted PYPOST-684) |
| ADR index | **Missing** | No `doc/adr/`; decisions in `ai-tasks/` only |

## ADR Alignment

PyPost does **not** maintain formal Architecture Decision Records. Decisions are implied by:

- `ai-tasks/PYPOST-*/20-architecture.md` and `70-dev-docs.md`
- Inline `PYPOST-N` references in capability docs
- Regression caps in `ai-tasks/PYPOST-376/baseline-metrics.md`

**Recommendation:** Add `doc/adr/README.md` as an index linking the highest-impact decisions
(composition root, presenter split, async env storage, MCP threading, metrics injection).

## ai-tasks Artifact Quality

| Signal | Value |
| --- | ---: |
| Folders with `00-roadmap.md` | 590 / 595 |
| Folders with `60-tech-debt.md` | 519 / 595 |
| Folders with ≤2 markdown files | 95 |
| Code Audit tasks with full 8-file set | 7 (684–689, partial 40) |

Audit tasks (684–689) follow the 8-artifact pattern consistently. Older tasks often have
roadmap-only stubs or missing Step 6 debt files.

## Follow-up Work

Twelve items in [60-tech-debt.md](../../ai-tasks/PYPOST-690/60-tech-debt.md) — P1: 2, P2: 6,
P3: 4. Prioritize dev README TOC expansion and ADR index creation.

## Related Commands

```bash
# TOC vs disk inventory
python3 -c "
import re
from pathlib import Path
readme = Path('doc/dev/README.md').read_text()
toc = {m for m in re.findall(r'\]\(([^)]+\.md)\)', readme)}
dev = {str(p.relative_to('doc/dev')) for p in Path('doc/dev').rglob('*.md') if p.name != 'README.md'}
print('missing:', len(dev - toc))
"

# Module counts
find pypost -name '*.py' | wc -l
```
