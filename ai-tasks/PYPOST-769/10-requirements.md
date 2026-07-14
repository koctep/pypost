# PYPOST-769: Standardize audit dev-doc follow-up tables

## Goals

Close documentation audit finding **R-P2-003 (D-007)** from PYPOST-690: align
`architecture_audit.md` and `security_audit.md` with the follow-up pattern used by sibling audit
summaries (observability, performance, maintainability) — defer Jira links to parent
`60-tech-debt.md` instead of embedding them in dev-doc tables.

## User Stories

- As an **audit reader**, I want a consistent follow-up section across Code Audit summaries, so
  I know where to find ticketed remediation without duplicated Jira URLs in dev docs.
- As a **maintainer**, I want a single source of truth for Jira links (`60-tech-debt.md`), so
  ticket status updates do not require editing multiple dev-doc tables.

## Definition of Done

- [x] `architecture_audit.md` has `## Follow-up Work` linking to PYPOST-684 `60-tech-debt.md`
  without inline Jira in a recommendations table.
- [x] `security_audit.md` has `## Follow-up Work` linking to PYPOST-685 `60-tech-debt.md`
  without inline Jira in a recommendations table.
- [x] Pattern matches sibling audits (`observability_audit.md`, `maintainability_audit.md`).
- [x] `make check` passes.

## Task Description

**Problem:** `architecture_audit.md` and `security_audit.md` embed Jira URLs in
`## Prioritized Recommendations` tables while PYPOST-688/689 defer to `60-tech-debt.md` only.

**Business intent:** Reduce documentation fragmentation and maintenance drift when audit debt is
ticketed separately from dev summaries.

**Source:** PYPOST-690 — R-P2-003.

**Scope:** `doc/dev/architecture_audit.md` and `doc/dev/security_audit.md` follow-up sections
only. Key Findings severity tables and parent `60-tech-debt.md` files are out of scope.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | No `## Prioritized Recommendations` table with Jira column in either target file |
| AC-2 | Each file has `## Follow-up Work` with link to its parent audit `60-tech-debt.md` |
| AC-3 | Follow-up copy includes priority counts and sprint-orchestrator Jira note |
| AC-4 | No regression in `make check` |
