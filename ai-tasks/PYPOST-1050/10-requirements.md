# PYPOST-1050: Document Agile ≤50 backlog batch limit on jira_move_issues_to_backlog

## Programming Language

Python is the primary project language for test fixtures and validation. English Markdown is used for all workflow documentation.

## Goals

When managing project work, AI agents and automated planning tools reorganize work items by moving them from active or future sprint planning containers back to the project backlog (clearing their sprint membership). However, bulk movement operations are subject to platform batch size limits (a maximum of 50 issues per operation).

Without clear and prominent guidance on this operational batch limit, planning agents can attempt to move large sets of work items (more than 50) in a single action. This causes request rejection errors, failures during automated sprint replanning, and workflow interruptions.

**Business goal:** Ensure that AI planning agents and human operators are clearly informed about the 50-issue batch limit for backlog movement operations, enabling them to chunk or size their replanning batches correctly and prevent planning operation failures.

## User Stories

- As an **AI planning agent**, I want explicit guidance stating that moving issues to the backlog is limited to at most 50 issues per batch, so that I can partition large replanning workloads into valid batch sizes and prevent bulk action failures.
- As an **AI agent**, I want the backlog movement guidance to maintain its clear explanation that moving issues to the backlog removes them from sprint membership, so that I can continue using it safely for sprint removal needs.
- As a **developer / operator**, I want the example documentation for sprint and backlog operations to describe the 50-issue batch constraint, so that I understand operational limits when setting up or reviewing automated workflows.
- As a **product steward**, I want this documentation update to clarify operational batch boundaries without modifying existing operation schemas, parameters, or endpoints.

## Definition of Done

- [x] The description for the backlog movement operation (`jira_move_issues_to_backlog` / `jira-move-issues-to-backlog`) explicitly communicates the batch size limit of up to 50 issues per request.
- [x] The backlog movement operation guidance preserves all existing sprint-membership removal and replanning meaning (e.g., clearing sprint membership / remove-from-sprint semantics).
- [x] Companion example collection documentation describes the 50-issue batch limit for backlog movement alongside sprint membership capabilities.
- [x] No changes are made to the REST API request method, URL path, parameters, or data format for the backlog movement action.
- [x] Existing automated test suites and contract checks continue to validate and pass.

## Task Description

**Problem:** Moving work items to the backlog allows clearing sprint membership and resetting issues for future planning. The underlying service restricts this operation to at most 50 issues at a time. The current action description gives an example payload but does not mention the 50-issue upper bound. When an AI agent performs large backlog reallocations involving more than 50 items, it lacks the context to split the request, leading to preventable runtime errors.

**Scope (in):**
- Update the agent-facing description of the backlog movement action (`jira_move_issues_to_backlog` / `jira-move-issues-to-backlog`) in the curated example collection to explicitly document the batch limit (maximum 50 issues per request).
- Update the companion documentation (`examples/README.md`) to document the batch limit constraint for backlog movement operations.
- Preserve existing membership removal guidance and discoverability keywords.

**Scope (out):**
- Adding automatic client-side chunking, looping, or pagination code to application logic.
- Changing the operation method, URL endpoint, headers, or parameter names.
- Modifying other unrelated Jira MCP actions or tools.
- Altering the external Atlassian MCP server configuration.

**Constraints and assumptions:**
- The batch limit of <=50 issues is a fixed constraint of the underlying Jira Agile platform API.
- The action schema and serialized JSON payload format remain unchanged.
- Guidance must be concise, accurate, and readily understandable by AI agents.

## Main Entities and Interactions

- **Work Item (Issue):** A unit of work that belongs to a sprint or sits in the backlog.
- **Sprint:** A time-boxed planning container holding a set of work items.
- **Backlog:** The repository of unassigned or future work items not currently active in a sprint.
- **Backlog Movement Action:** The operation that transfers issues to the backlog, thereby clearing their sprint membership.
- **Batch Size Limit:** The maximum allowable number of work items (50) processed in a single backlog movement operation.
- **AI Planning Agent:** The consumer of the action that reads tool guidance to plan, batch, and execute work item management safely.

**Interactions:** An AI planning agent evaluates a set of work items to remove from sprints back to the backlog. By consulting the backlog movement action guidance, the agent identifies the 50-issue limit, chunks any larger set into batches of 50 or fewer, and executes each batch successfully without triggering platform limits.

## Non-Functional Requirements

- **Clarity & Discoverability:** The batch limit constraint must be stated clearly so that AI agents parsing tool descriptions understand the limit before submitting requests.
- **Preservation of Semantics:** Existing semantic cues (such as removing issues from sprint membership) must be preserved to prevent regressions in tool selection.
- **Scope Discipline:** Changes are limited strictly to documentation and fixture guidance; no alterations to request parameters or schemas.
- **Maintainability:** Guidance must remain consistent across tool descriptions, documentation, and contract tests.

## Q&A

**Q:** Why is documenting the batch limit necessary if the service already enforces it?
**A:** If an agent is unaware of the limit prior to issuing a command, it will attempt to send oversized batches, resulting in failed operations and interrupted replanning workflows. Documenting the limit enables the agent to plan and chunk requests proactively.

**Q:** Does this task introduce automated multi-batch splitting into the codebase?
**A:** No. This task is strictly focused on documenting the platform constraint in tool descriptions and reference documentation. Application code and request execution remain unchanged.

**Q:** Will the existing guidance regarding sprint membership removal be altered?
**A:** No. The guidance will retain the explanation that moving issues to the backlog removes sprint membership while adding the batch limit specification.
