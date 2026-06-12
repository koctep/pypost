# PYPOST-684: Audit — architecture and package boundaries

## Goals

PyPost has grown across presentation, core business capabilities, and external tool integration
(MCP). Without a structured review of how those concerns are separated and how dependencies flow
between them, the team risks accidental coupling, harder testing, and drift from documented
architecture.

This audit establishes a shared, evidence-based picture of current layering and service
boundaries so maintainers can prioritize remediation work and future features stay within
intended boundaries.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up Jira issues).

## User Stories

- As a **maintainer**, I want a clear map of which parts of the application may depend on which
  others so I can avoid introducing cross-layer coupling when changing code.
- As a **developer**, I want to know where documented architecture and actual package structure
  disagree so I can make informed design choices during feature work.
- As a **reviewer**, I want audit findings with concrete examples and severity so pull requests
  that worsen boundary violations are easier to spot.
- As a **tech-debt owner**, I want prioritized follow-up Jira issues for boundary and dependency
  problems so remediation can be scheduled alongside feature work.
- As a **product owner**, I want assurance that critical capabilities (HTTP execution,
  templating, history, MCP tool exposure) have well-defined ownership boundaries so changes in
  one area do not unpredictably affect others.

## Definition of Done

- [ ] An audit report is stored under `ai-tasks/PYPOST-684/` and is readable without local
  checkout context (summary, scope, methodology note, findings, recommendations).
- [ ] Layer and package boundary findings cover the presentation layer, core business logic,
  data definitions, and MCP-related integration as scoped below.
- [ ] Dependency-direction findings identify inward/outward violations and any circular-import
  risks that could affect startup, testing, or maintainability.
- [ ] Service-boundary findings cover HTTP request execution, templating, request history, and
  MCP tool exposure — including whether responsibilities are duplicated or blurred across
  modules.
- [ ] Documented architecture in `doc/dev/` (including `architecture.md`, MCP integration
  notes, testability/composition-root guidance, and related dev docs) is compared against
  observed structure; gaps and stale documentation are called out.
- [ ] Each significant finding includes impact (why it matters for maintainability or change
  risk) and a recommended remediation direction at a high level (not implementation design).
- [ ] Findings are prioritized (e.g. by severity or change risk) so follow-up work can be
  ordered.
- [ ] Actionable follow-up Jira issues are created for remediation items that should not be
  deferred without explicit decision.
- [ ] Out-of-scope areas are explicitly listed in the audit report so readers know what was not
  reviewed.

## Task Description

**Problem:** The codebase spans user interface, core services, models, and MCP server components.
Prior work (e.g. PYPOST-40 SOLID audit) addressed design quality broadly; this task focuses
specifically on **layering, package boundaries, dependency direction, and service ownership**
across those areas. Undocumented or violated boundaries increase the cost of features, refactors,
and onboarding.

**Business intent:** Reduce structural risk before it blocks delivery — by making boundary
problems visible, traceable, and schedulable as debt rather than discovered ad hoc during
incidents or large refactors.

### In Scope

- Review of how presentation concerns are separated from core business logic and from external
  integration (MCP).
- Review of dependency direction across the Python package tree (what may depend on what).
- Assessment of risks from circular or inverted dependencies (including effects on testability
  and application startup).
- Review of service boundaries for:
  - HTTP request execution
  - Template and variable interpolation
  - Request/response history
  - MCP tool exposure to external clients
- Alignment check against architecture and integration documentation under `doc/dev/` and any
  existing architecture decision records referenced there.
- Written audit deliverables and follow-up Jira issues for remediation.

### Out of Scope

- Implementing refactors or code fixes (audit only).
- Full repetition of the PYPOST-40 SOLID maintainability audit unless a finding overlaps;
  this task does not replace SOLID-specific recommendations already tracked elsewhere.
- Performance profiling, security penetration testing, or UI/UX review.
- Changing build tooling, CI pipelines, or dependency versions.
- Defining the target future architecture (reserved for Step 2+ if remediation tasks require it).

## Functional Requirements

- The audit must produce a structured written report suitable for developers and maintainers.
- The audit must state the reviewed scope (packages, capability areas, and reference documents).
- The audit must document boundary and dependency findings with enough context to locate them in
  the repository.
- The audit must assess whether HTTP execution, templating, history, and MCP exposure each have
  a clear owning boundary or share responsibilities across layers in ways that increase change
  risk.
- The audit must compare observed structure to documented architecture and note mismatches or
  outdated documentation.
- The audit must include prioritized recommendations and create Jira follow-ups for items
  warranting tracked remediation.

## Non-Functional Requirements

- **Clarity:** Findings must be understandable to a developer new to the boundary rules.
- **Actionability:** Recommendations must be specific enough to become tickets; avoid vague
  "improve architecture" statements.
- **Traceability:** Report and follow-up issues link back to PYPOST-684 and reference relevant
  `doc/dev/` material where applicable.
- **Proportionality:** Depth should match risk — focus on boundaries that affect multiple features
  or integration surfaces (UI, HTTP, MCP).

## Constraints and Assumptions

- PyPost is a Python desktop application; audit artifacts are markdown under `ai-tasks/`.
- Documented layering expectations exist in `doc/dev/`; the audit treats those as the baseline
  for alignment checks unless the report explicitly notes undocumented conventions.
- MCP integration is a first-class integration surface; boundary review includes server lifecycle
  and tool exposure, not only GUI code paths.
- Step 1 captures business requirements only; audit methodology and technical analysis belong in
  later steps.
- Follow-up Jira issues are created in the project Debt or equivalent backlog per team practice
  (priority assigned when tickets are created in Step 6).

## Main Entities and Interactions (Business View)

| Entity | Description |
| --- | --- |
| Presentation layer | User-facing windows, widgets, and dialogs; orchestrates user actions. |
| Core business layer | Request lifecycle, execution coordination, persistence, configuration. |
| Data definitions | Shared structures for requests, responses, environments, settings. |
| External integration (MCP) | Exposure of collection-backed capabilities to external MCP clients. |
| Capability: HTTP execution | End-to-end sending of HTTP requests and handling responses. |
| Capability: Templating | Resolving variables and templates for URLs, headers, and bodies. |
| Capability: History | Recording and presenting past request/response activity. |
| Capability: MCP tools | Registering and serving tools derived from user collections. |
| Documented architecture | Authoritative dev docs describing intended structure and composition. |
| Audit finding | Documented gap, violation, or risk with impact and priority. |
| Remediation follow-up | Jira issue tracking a specific boundary or dependency fix. |

**Interaction overview (business):**

1. Users interact with the presentation layer to run requests and manage collections.
2. Presentation delegates execution and data access to core capabilities rather than owning
   business rules.
3. Core capabilities use shared data definitions; integration surfaces (MCP) reuse the same
   execution and templating concerns where intended.
4. Documented architecture describes intended separation; the audit verifies reality against that
   baseline.
5. Significant gaps become prioritized findings and optional Jira follow-ups for remediation.

## Acceptance Criteria (Audit Deliverables)

| ID | Criterion |
| --- | --- |
| AC-1 | Report exists under `ai-tasks/PYPOST-684/` with executive summary and detailed findings. |
| AC-2 | Layer boundary section addresses presentation vs core vs integration concerns. |
| AC-3 | Dependency-direction section addresses import/coupling risks across the package tree. |
| AC-4 | Service-boundary section covers HTTP execution, templating, history, and MCP tools. |
| AC-5 | Documentation alignment section references `doc/dev/` (and ADRs if cited there). |
| AC-6 | Recommendations are prioritized; each major finding has clear impact statement. |
| AC-7 | Follow-up Jira issues exist for remediation items agreed during audit closeout. |

## Q&A

| Question | Answer |
| --- | --- |
| Why audit boundaries now? | The app spans UI, core services, and MCP; boundary drift increases change cost and test friction as features accumulate. |
| How is this different from PYPOST-40? | PYPOST-40 focused on SOLID and maintainability broadly; this task focuses on package/layer boundaries, dependency direction, and named service ownership areas. |
| What is the primary deliverable? | A written audit report plus follow-up Jira issues — not code changes. |
| Who consumes the report? | Developers, reviewers, and tech-debt owners planning refactors and guarding new work. |
| Are ADRs required? | Alignment check includes ADRs only if referenced from `doc/dev/`; absence of a central ADR index is noted as a documentation gap if relevant. |
