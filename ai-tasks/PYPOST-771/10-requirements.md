# PYPOST-771: Add tech debt inventory to dev README TOC

## Goals

Close documentation audit finding **R-P2-005 (D-009)** from PYPOST-690: the developer README
table of contents does not link to `tech_debt_inventory.md` or the eight developer-facing audit
debt summaries under `doc/dev/tech-debt/`.

## User Stories

- As a **contributor**, I want the dev README to list tech debt docs, so I can find consolidated
  debt and major audit follow-ups without searching the tree.
- As a **maintainer**, I want the Tech debt TOC section to mirror the Audits section style, so
  navigation stays consistent across documentation hubs.

## Definition of Done

- [x] `doc/dev/README.md` includes a **Tech debt** subsection in the table of contents.
- [x] Subsection links to `tech_debt_inventory.md`.
- [x] Subsection links to all eight `doc/dev/tech-debt/PYPOST-*.md` audit summaries.
- [x] `make check` passes.

## Task Description

**Problem:** Tech debt inventory and per-audit debt pages are absent from the dev README TOC
(R-P2-005).

**Business intent:** Improve discoverability of technical debt documentation for sprint planning
and onboarding.

**Source:** PYPOST-690 — R-P2-005.

**Scope:** `doc/dev/README.md` TOC only. No changes to debt file contents.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `doc/dev/README.md` has a `### Tech debt` TOC section |
| AC-2 | TOC includes a link to `tech_debt_inventory.md` |
| AC-3 | TOC includes individual links to all eight `tech-debt/PYPOST-*.md` files |
| AC-4 | No regression in `make check` |
