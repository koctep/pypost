# PYPOST-451: Separate ownership of permitted template functions from rendering flow

## Goals

Template content can invoke a controlled set of functions. Today, the list of permitted
functions lives inside the same component that orchestrates template rendering. That
makes it harder to see, review, and evolve “what users may call in templates” without
wading through unrelated rendering concerns.

The business need is clearer **governance and maintainability**: one obvious place that
defines which template functions exist and are allowed, while the rendering path stays
focused on orchestration (validation, rendering, and related behavior). This work is a
follow-up to technical-debt findings from PYPOST-450
(`ai-tasks/PYPOST-450/60-tech-debt.md`).

## User Stories

- **As a maintainer**, I need the permitted template functions to be defined in one
  dedicated place so I can update or audit the catalog without mixing it with general
  template rendering logic.
- **As a maintainer**, I need the template rendering entry point to remain the boundary
  for how templates are processed, so user-visible behavior stays predictable while
  ownership of the function catalog improves.
- **As a stakeholder relying on templates**, I expect existing valid templates to keep
  working; this change is about structure of the codebase, not removing supported
  capabilities without an explicit product decision.

## Definition of Done

- There is a single, explicit home for the catalog of functions that may appear in
  templates (the allow-list / registry of permitted functions).
- Template rendering orchestration no longer embeds that catalog as an internal detail
  of the same unit; it uses the dedicated catalog instead.
- Behavior for end users and valid templates matches prior behavior for this scope
  (no unintended removal of allowed functions or silent widening of the surface).
- The outcome is traceable to Jira
  [PYPOST-451](https://pypost.atlassian.net/browse/PYPOST-451) and the PYPOST-450
  follow-up list.

## Task Description

**Problem (from ticket):** The component that handles template rendering currently owns
the allowed-function list directly (e.g. as an in-class constant). That couples “what
may run” with “how rendering runs.”

**Goal (from ticket):** Move ownership of the function catalog into a dedicated module
so the rendering component stays an orchestration boundary.

**Constraints and assumptions:**

- **Programming language:** Python (see roadmap).
- **Scope:** This ticket is the first slice of the sprint “Template expression engine”
  (Jira sprint id 200); related items PYPOST-452–454 cover resolver extraction, nested
  policy, and tests.
- **Dependencies:** Informed by PYPOST-450 technical-debt analysis; does not by itself
  resolve nested-call policy or add the full expression-resolver split (those are
  separate tickets).

**Non-functional requirements:**

- **Maintainability:** Future changes to the function catalog should be localized and
  reviewable.
- **Safety / clarity:** It should be obvious which functions are permitted in templates
  for governance and code review.

## Main entities (business view)

- **Permitted function catalog:** The authoritative set of functions users may invoke
  from template expressions.
- **Template rendering orchestration:** The flow that validates and renders templates
  using data and rules; it should consume the catalog rather than own its definition.

## Q&A

| Question | Answer |
| -------- | ------ |
| Source of truth for the problem? | Jira PYPOST-451; `ai-tasks/PYPOST-450/60-tech-debt.md`. |
| Which sprint? | Jira sprint **200**, “Template expression engine”. |

Sprint 200 goal also references PYPOST-450 and PYPOST-451–454 as related work.
