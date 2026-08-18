# PYPOST-1056: Clear diagnostics for Jira MCP path-catalog drift

## Programming Language

Python is the implementation language for the automated validation. Markdown
documents record the task's requirements and progress.

## Goals

Maintainers depend on the curated Jira MCP collection to keep its critical
REST-path relationships aligned with the locked catalog. The existing
freshness check identifies drift, but its diagnostic quality is not protected:
a future change could make a mismatch difficult to identify even while the
check still fails.

**Business goal:** ensure contributors receive a precise, actionable failure
when a critical collection-to-catalog path relationship drifts, so stale or
incomplete catalogs cannot silently erode confidence in the Jira MCP example.

## User Stories

- As a contributor changing the curated Jira MCP collection or its locked
  critical-path catalog, I want a deliberate path mismatch to produce a clear
  rejection, so I can identify the affected critical relationship promptly.
- As a maintainer reviewing a failed freshness check, I want the diagnostic to
  distinguish the affected request and the missing or unexpected path
  relationship, so I can correct the right catalog or collection entry without
  guesswork.
- As a release steward, I want this diagnostic behavior protected by routine,
  offline validation, so CI continues to prevent ambiguous regressions without
  requiring Jira access or credentials.

## Definition of Done

- [x] Automated validation deliberately exercises a critical REST-path
      mismatch between the curated Jira MCP collection and its locked catalog.
- [x] That validation confirms the freshness check rejects the mismatch.
- [x] The confirmed rejection clearly identifies the affected critical request
      and the path relationship that no longer matches the locked catalog.
- [x] The validation remains deterministic, offline, and free of Jira
      credentials, tenant data, and external network dependencies.
- [x] The existing valid collection-to-catalog comparison remains accepted.
- [x] The task does not broaden the catalog's intentional critical-path scope
      or alter the curated Jira MCP tool surface.

## Task Description

### Problem

PYPOST-1030 introduced an offline freshness guard for a focused catalog of
critical Jira MCP REST paths. The related technical-debt review identified a
gap: no deliberate-drift validation currently guarantees that a rejected
catalog comparison tells maintainers exactly what relationship has changed.

### Functional Requirements

1. Demonstrate that a critical REST-path relationship that differs from the
   locked catalog is rejected.
2. Preserve an understandable diagnostic for that rejection, including the
   identity of the affected critical relationship and the expected-versus-found
   path condition.
3. Keep the validation focused on the existing locked critical-path catalog
   and curated Jira MCP collection.
4. Keep successful catalog comparisons valid when no drift is present.

### Non-Functional Requirements

- **Clarity:** failure feedback must be specific enough for a contributor to
  locate the drifted relationship without broad manual inspection.
- **Reliability:** the validation must deterministically demonstrate the
  rejection and diagnostic behavior.
- **Security:** routine validation must not access, require, or disclose Jira
  credentials, tenant data, or other sensitive configuration.
- **Maintainability:** the protected diagnostic must remain useful as the
  intentional critical-path catalog evolves.
- **Compatibility:** existing valid Jira MCP collection and catalog behavior
  remains unchanged.

### Scope and Boundaries

**In scope**

- Diagnostic quality for a deliberately introduced mismatch in an existing
  critical Jira MCP REST-path relationship.
- Offline validation of rejection behavior and its explanatory failure text.
- Preservation of the currently valid comparison behavior.

**Out of scope**

- Expanding the catalog beyond its existing critical-path set.
- Revising the Jira MCP collection's supported tool surface or normal REST
  path choices.
- Live Jira, Atlassian documentation, OpenAPI, or network comparisons.
- Jira credentials, tenant data, and production-service validation.

### Constraints and Assumptions

- The existing locked catalog remains the approved source of expected critical
  relationships for this task.
- The task protects diagnostic behavior only; it does not redefine which paths
  are considered critical.
- Routine repository validation must stay safe for contributors who lack Jira
  access.

## Main Entities and Interactions

- **Curated Jira MCP collection** — the maintained set of Jira MCP requests
  whose critical REST-path relationships must remain trustworthy.
- **Locked critical-path catalog** — the approved reference set used to judge
  those relationships.
- **Freshness validation** — the repository safeguard that accepts aligned
  relationships and rejects drift.
- **Drift diagnostic** — the actionable explanation presented when the
  validation detects a mismatch.
- **Contributor or maintainer** — the person who uses the diagnostic to locate
  and correct unintended catalog or collection drift.

## Q&A

**Why is this needed if the freshness check already fails on drift?**

A failure alone is insufficient if it cannot reliably identify the drifted
relationship. This task protects the usefulness of the failure feedback.

**Does this change the approved critical-path catalog?**

No. It verifies diagnostic behavior for the existing focused catalog.

**Does routine validation contact Jira or Atlassian services?**

No. The task remains an offline repository check and requires no credentials.

**What prompted this follow-up?**

PYPOST-1030 technical debt TD-1 identified missing validation for a deliberate
catalog/collection path drift and its diagnostic quality.
