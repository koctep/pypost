# PYPOST-767: Maintain Code Audit hub doc

## Goals

Close documentation audit finding **R-P2-001 (D-007)** from PYPOST-690: keep the Code Audit hub
current as new audit summaries land and give readers consistent navigation between sibling audit
developer docs without hunting filenames.

## User Stories

- As an **audit reader**, I want a single hub listing all Code Audit summaries with report links,
  so I can jump between focus areas quickly.
- As a **maintainer**, I want each `*_audit.md` to link its seven siblings plus the hub, so new
  audits only require hub-table and footer updates.

## Definition of Done

- [x] `documentation_audit.md` hub table includes Dependencies (PYPOST-691).
- [x] Eight sibling `*_audit.md` files (684–691) each have a standardized `## Related Audits`
  footer linking the other seven summaries and the hub anchor.
- [x] Introductory copy in `documentation_audit.md` reflects eight Code Audit summaries.
- [x] `make check` passes.

## Task Description

**Problem:** PYPOST-690 created a hub table for seven audits; PYPOST-691 added
`dependencies_audit.md` without a hub row. Sibling cross-links were inconsistent (zero to two
links per file).

**Business intent:** Reduce onboarding friction when navigating Code Audit findings across
architecture, security, tests, maintainability, observability, performance, documentation, and
dependencies.

**Source:** PYPOST-690 — R-P2-001.

**Scope:** `doc/dev/documentation_audit.md` and eight sibling `*_audit.md` files (684–691).
`solid_audit.md` (legacy PYPOST-40) is out of scope for footer standardization.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Hub table row for Dependencies (691) with dev summary and full report links |
| AC-2 | Each of eight siblings has `## Related Audits` with seven sibling links + hub reference |
| AC-3 | Hub page lists all eight audits and includes its own Related Audits section |
| AC-4 | No regression in `make check` |
