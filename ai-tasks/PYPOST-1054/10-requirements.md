# PYPOST-1054: Add safe defaults for optional Jira MCP pagination query args

## Programming Language

Python is the implementation language for the application runtime, collection tooling, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

In the curated Jira MCP tools, list operations (such as listing boards, listing board sprints, and listing sprint issues) support pagination so agents can inspect collections across large Jira instances. Currently, pagination parameters (page size `maxResults` and offset `startAt`) are strictly required. AI agents must explicitly specify `maxResults=50` and `startAt=0` even when they only desire the standard, initial page of results.

If an AI agent omits these arguments, the tool invocation fails or cannot execute properly. Requiring repetitive pagination inputs for standard list requests adds unnecessary boilerplate to agent tool calls, increases prompt/token overhead, and degrades the ergonomics of curated tools.

**Business goal:** Make pagination parameters optional for curated Jira MCP list operations by automatically applying safe, standard defaults (`maxResults=50` and `startAt=0`) when omitted by the caller, while still honoring custom values when explicitly provided. This provides an intuitive, ergonomic tool interface for AI agents while preserving full paging control and backward compatibility.

## User Stories

- As an **AI agent calling Jira list tools**, I want pagination parameters (`maxResults` and `startAt`) to be optional, so that I can quickly retrieve standard first-page results without providing boilerplate arguments on every call.
- As an **AI agent querying large datasets**, I want to provide explicit custom `maxResults` and/or `startAt` values when needed, so that I can page through large result sets or request specific page sizes.
- As an **AI agent inspecting tool documentation**, I want the published tool schemas and descriptions to clearly indicate that pagination parameters are optional and describe their default values (`50` for page size, `0` for start offset), so that I understand expected behavior without trial and error.
- As an **API collection author / tool designer**, I want exposed MCP tools to support ergonomic default values for optional query arguments, so that agent-facing interfaces remain clean and user-friendly.
- As a **contributor / maintainer**, I want deterministic, credential-free offline automated tests that verify optional pagination parameter contracts and safe default behaviors across all curated list tools, preventing regressions.
- As a **product steward**, I want this enhancement to preserve existing functionality, scoping rules, authentication conventions, and security boundaries without introducing breaking changes.

## Definition of Done

- [ ] Curated Jira MCP list tools (`jira-list-boards`, `jira-list-board-sprints`, and `jira-get-sprint-issues`) advertise `maxResults` and `startAt` as optional parameters in their published MCP tool contracts and input schemas.
- [ ] When an AI agent invokes any of the curated Jira list tools and omits `maxResults`, `startAt`, or both, the system executes the request using safe standard defaults (`maxResults=50` and `startAt=0`).
- [ ] When an AI agent invokes any of the curated Jira list tools with explicit custom values for `maxResults`, `startAt`, or both (supplied as integers or valid numeric strings), the system honors the provided values during execution.
- [ ] Tool descriptions and parameter metadata clearly document that pagination arguments are optional and specify the default values applied when omitted.
- [ ] Curated Jira list tools that require mandatory scoping identifiers (such as `board_id` and `state` for listing board sprints, or `sprint_id` for listing sprint issues) continue to enforce those required inputs.
- [ ] Offline fixture and contract tests deterministically verify that pagination parameters are optional, safe defaults apply when omitted, custom values are honored, and contracts match the published schemas without requiring network access or live Jira credentials.
- [ ] Existing capabilities, project-scoping behaviors, authentication conventions, and environment variable protections remain intact.
- [ ] Developer documentation is updated to describe the optional pagination parameter conventions and safe default behavior.

## Task Description

**Problem:**
Follow-up from PYPOST-1029 (TD-1). In PYPOST-1029, pagination parameters (`maxResults` and `startAt`) were added to curated Jira MCP list tools (`jira-list-boards`, `jira-list-board-sprints`, `jira-get-sprint-issues`). However, because omitting these arguments caused runtime execution failures, both parameters were marked as mandatory, requiring agents to always pass `maxResults=50` and `startAt=0` for standard first-page listings. This creates an unergonomic developer/agent experience and increases boilerplate.

**Scope (in):**
- Make `maxResults` and `startAt` optional on curated Jira MCP list tools:
  - `jira-list-boards`
  - `jira-list-board-sprints`
  - `jira-get-sprint-issues`
- Apply safe standard defaults (`maxResults=50`, `startAt=0`) when pagination parameters are omitted by the caller.
- Support explicit custom pagination arguments (integers and decimal strings) when provided by the caller.
- Update agent-facing parameter descriptions to reflect optionality and documented defaults.
- Update offline contract tests and integration suites to validate optionality and default application.
- Update relevant developer documentation.

**Scope (out):**
- Adding new Jira API capabilities or altering non-list Jira tool interfaces.
- Migrating Agile list endpoints to token-based pagination (`nextPageToken`), which is tracked separately as TD-2 (PYPOST-1055).
- Live Jira network or credentialed integration tests.
- Changing mandatory status for non-pagination tool inputs (e.g. `board_id`, `sprint_id`, `state`).

**Constraints and assumptions:**
- Curated default page size is 50 items per page; curated default starting offset is 0.
- Custom inputs must continue to accept native integers and decimal numeric strings.
- All verification must be deterministic, fast, and completely offline without live external services.
- Sensitive environment variables and secret isolation policies must be strictly maintained.

## Main Entities and Interactions

- **AI Agent Caller:** The automated agent invoking MCP tools to query Jira resources.
- **Curated Jira List Tool:** A standardized MCP tool definition for retrieving paginated collections of Jira entities (boards, sprints, issues).
- **Pagination Arguments:** The optional input parameters (`maxResults` for maximum items per page, `startAt` for 0-based starting offset) passed by the caller or populated by defaults.
- **Safe Defaults:** The baseline values (`50` for page size, `0` for offset) automatically applied when the caller does not supply pagination arguments.
- **Tool Contract & Schema:** The published MCP tool specification advertising available parameters, parameter types, descriptions, and optionality.
- **Request Execution Pipeline:** The component that resolves inputs, applies default values for omitted optional parameters, and executes the underlying HTTP request.

**Interaction Flow:**
1. An AI agent inspects the available Jira list tools and sees that `maxResults` and `startAt` are optional parameters with documented defaults (50 and 0).
2. Scenario A (Default Listing): The agent calls `jira-list-boards` without specifying `maxResults` or `startAt`. The execution pipeline applies the safe defaults (50 and 0) and executes the request for the first 50 boards.
3. Scenario B (Custom Pagination): The agent calls `jira-list-board-sprints` specifying `board_id=123`, `state="active"`, `maxResults=10`, and `startAt=20`. The execution pipeline uses the explicitly provided pagination values.
4. The system executes the request and returns the resulting data to the agent.

## Non-Functional Requirements

- **Ergonomics & Agent Usability:** Reduces required input complexity for agents calling list tools, improving reliability and reducing token consumption.
- **Backward Compatibility:** Existing workflows and agents that already supply explicit `maxResults` and `startAt` values continue to function without changes.
- **Robustness & Failure Prevention:** Omission of optional parameters never results in unhandled errors, invalid query strings, or broken executions.
- **Deterministic Offline Verification:** All contract checks, default resolution, and request preparation must be verifiable locally without network access or secrets.
- **Security & Secret Safety:** Parameter defaulting must not bypass secret masking, sensitive variable exclusions, or environment boundaries.

## Q&A

**Q: Why should pagination arguments be optional if agents could just pass 50 and 0?**
**A:** Forcing agents to always supply boilerplate pagination arguments degrades agent usability, increases token cost, and leads to unnecessary execution errors when agents naturally expect list tools to have sensible defaults.

**Q: What are the safe default values for Jira list endpoints?**
**A:** `maxResults=50` (matching the standard curated page size) and `startAt=0` (starting from the first item/offset).

**Q: Does this change affect required non-pagination parameters like `board_id` or `sprint_id`?**
**A:** No. Resource identifiers and filtering criteria necessary to identify the target resource remain strictly required.

**Q: Does this task migrate Jira list endpoints to token-based pagination (`nextPageToken`)?**
**A:** No. Token-based pagination migration is tracked separately under technical debt item TD-2 (PYPOST-1055).

**Q: Is a live Jira instance or network connection required for testing?**
**A:** No. All contracts, default values, and parameter bindings are tested completely offline using deterministic test suites.
