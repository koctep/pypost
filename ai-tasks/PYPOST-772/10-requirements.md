# PYPOST-772: Document ai-tasks artifact expectations

## Goals

Close documentation audit finding **R-P2-006 (D-009b)** from PYPOST-690: contributors lack a
single reference for minimum `ai-tasks/` artifacts when closing a Jira task. Historical folders
show roadmap-only stubs, missing Step 6 debt files, and inconsistent naming.

## User Stories

- As a **contributor**, I want a documented minimum artifact set per closed task, so I know what
  to create when following the top-down workflow.
- As a **maintainer**, I want legacy exceptions called out explicitly, so thin or oddly named
  older folders are not mistaken for the current standard.

## Definition of Done

- [x] `doc/dev/setup.md` includes a subsection defining minimum ai-tasks artifacts per closed task.
- [x] Subsection documents the 8-file Code Audit standard and legacy exceptions.
- [x] `make check` passes.

## Task Description

**Problem:** 76 `ai-tasks/PYPOST-*` folders lack `60-tech-debt.md`; 95 have ≤2 markdown files
(PYPOST-690 audit). No developer doc states completion expectations.

**Business intent:** Improve navigability of task history and onboarding for the top-down workflow.

**Source:** PYPOST-690 — R-P2-006.

**Scope:** `doc/dev/setup.md` subsection and `ai-tasks/PYPOST-772/` workflow artifacts. No CI
verifier script in this task (optional follow-up).

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `doc/dev/setup.md` has an ai-tasks artifact expectations subsection |
| AC-2 | Subsection lists the standard top-down workflow files per step |
| AC-3 | Subsection documents the 8-file Code Audit pattern |
| AC-4 | Subsection documents legacy exceptions (stubs, alternate filenames) |
| AC-5 | No regression in `make check` |
