# PYPOST-690: Audit — documentation and ADR alignment

## Goals

PyPost has grown to **60 developer markdown files**, **seven Code Audit summaries**, and **595
ai-tasks** folders, but there is no consolidated audit of whether documentation stays aligned
with code, whether architectural decisions are discoverable, and whether navigation (README TOC,
audit cross-links) supports onboarding.

This audit establishes an evidence-based picture of **documentation and ADR alignment** so the
team can prioritize TOC gaps, stale narratives, missing ADR index, and ai-tasks artifact drift.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up items).

## User Stories

- As a **new contributor**, I want a complete `doc/dev/README.md` table of contents, so I can
  find capability docs without ripgrep.
- As a **maintainer**, I want a central ADR index, so architectural decisions are not buried
  in closed `ai-tasks/` folders.
- As an **audit reader**, I want consistent cross-links between the seven Code Audit summaries,
  so I can navigate findings without hunting filenames.
- As a **tech-debt owner**, I want prioritized follow-ups (P1/P2/P3), so documentation work is
  schedulable.

## Definition of Done

- [x] An audit report is stored under `ai-tasks/PYPOST-690/` with summary, scope, methodology,
  findings, and recommendations.
- [x] Findings cover `doc/dev/` completeness vs README TOC.
- [x] Findings cover stale documentation vs current code (sampled capability and audit docs).
- [x] Findings cover missing ADR index and decision scatter in `ai-tasks/`.
- [x] Findings cover cross-links between audit developer summaries.
- [x] Findings cover root and dev README navigation.
- [x] Findings cover ai-tasks artifact quality (roadmap, tech-debt, thin folders).
- [x] Each significant finding includes impact and a recommended remediation direction.
- [x] Findings are prioritized (P1/P2/P3) for follow-up ticketing.
- [x] Developer summary added at `doc/dev/documentation_audit.md`.
- [x] Out-of-scope areas are explicitly listed.

## Task Description

**Problem:** Documentation grew organically with feature tasks and Code Audit epics without a
single pass over discoverability, ADR structure, and artifact consistency.

**Business intent:** Reduce onboarding friction and prevent stale audit narratives from
misleading refactors.

### In Scope

- `doc/dev/` markdown inventory and README TOC coverage.
- `doc/` user-facing docs vs `doc/dev/` developer docs.
- Stale-vs-code sampling for `architecture.md`, capability docs, and audit summaries.
- ADR presence and index (none exists today).
- Cross-links among `*_audit.md` files and `ai-tasks/PYPOST-684`–`689` reports.
- `ai-tasks/` artifact completeness patterns.
- Root `README.md` developer doc entry point.

### Out of Scope

- Application code fixes (audit only).
- Rewriting all 60 capability docs.
- Creating Jira tickets (deferred; `60-tech-debt.md` without links).
- Dependencies/supply-chain audit (separate Code Audit focus).
- User guide (`doc/README.md`) content rewrite.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Report documents doc/dev file count and TOC gap |
| AC-2 | Report documents ADR index absence and decision scatter |
| AC-3 | Report documents audit cross-link matrix |
| AC-4 | Report documents stale doc samples with evidence |
| AC-5 | Report documents ai-tasks artifact quality metrics |
| AC-6 | P1/P2/P3 follow-ups listed in `60-tech-debt.md` without Jira links |
