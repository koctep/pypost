# PYPOST-768: Refresh solid_audit MainWindow narrative

## Goals

Close documentation audit finding **R-P2-002 (D-002)** from PYPOST-690: remove stale MainWindow
LOC narrative in `solid_audit.md`, mark PYPOST-43 resolved, and cite
`baseline-metrics.md` as the authoritative regression snapshot.

## User Stories

- As an **audit reader**, I want the MainWindow finding to show resolved status and current
  caps without mixing audit-era 1040 LOC with outdated baseline numbers.
- As a **maintainer**, I want a single authoritative link to `baseline-metrics.md` so the dev
  summary does not drift from the CI snapshot.

## Definition of Done

- [x] Key Findings MainWindow bullet marks PYPOST-43 resolved and cites `baseline-metrics.md`.
- [x] Audit-era 1040 LOC retained only as historical context (not as current state).
- [x] P1 recommendations table marks MainWindow decomposition resolved.
- [x] Regression baseline table matches `ai-tasks/PYPOST-376/baseline-metrics.md` (393/353).
- [x] `make check` passes.

## Task Description

**Problem:** `solid_audit.md` Key Findings listed stale 282/246 baseline LOC alongside audit-era
1040 LOC, confusing readers about post-PYPOST-43 state.

**Business intent:** Keep the legacy SOLID audit dev summary accurate for onboarding and debt
triage without re-auditing the codebase.

**Source:** PYPOST-690 — R-P2-002.

**Scope:** `doc/dev/solid_audit.md` only.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | MainWindow Key Findings bullet links PYPOST-43 as resolved |
| AC-2 | Narrative cites `baseline-metrics.md` for current baseline and caps |
| AC-3 | Regression table baseline columns match `baseline-metrics.md` |
| AC-4 | No regression in `make check` |
