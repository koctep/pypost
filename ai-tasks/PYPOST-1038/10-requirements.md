# PYPOST-1038: Accept string-form numeric identifiers in the Jira MCP example

## Goals

Agents and other MCP clients commonly send identifiers as JSON strings, including values
that are numerically meaningful.  Existing Jira MCP example tools should remain usable in
that normal client situation instead of rejecting a valid identifier solely because it was
represented as a string.

This task improves the reliability of the Jira MCP example for real agent use while
preserving the example's existing tool surface.

**Programming language:** Python

## User Stories

- As an **MCP client user**, I want existing Jira tools to accept a numeric identifier when
  I provide it as a JSON string, so I can complete requests without manually changing how
  my client represents the value.
- As an **agent author**, I want the Jira MCP example to tolerate ordinary string-form
  identifiers, so agent requests do not fail due to a representation mismatch.
- As a **collection author**, I want the documented input contract to describe this
  tolerance, so I can understand what clients may supply.
- As a **maintainer**, I want automated evidence of the supported behavior, so regressions
  are detected before they affect MCP clients.

## Definition of Done

- [ ] Existing Jira MCP tools that require numeric identifiers accept valid string-form
      numeric input at every currently supported identifier location.
- [ ] The same tools retain their existing names, purposes, and client-visible behavior for
      valid inputs.
- [ ] Invalid or non-numeric identifier input continues to be rejected according to the
      established contract rather than being silently treated as a different identifier.
- [ ] The Jira MCP example documentation explains the supported string-form identifier
      behavior where users and collection authors need it.
- [ ] Automated validation demonstrates the behavior without relying on live Jira
      credentials or modifying a real Jira project.

## Task Description

**Problem:** MCP clients, especially agents and LLM-backed clients, often represent numeric
identifiers as JSON strings.  The Jira MCP example currently rejects these otherwise valid
values at some identifier locations, interrupting normal requests.

**Business outcome:** Users can provide a valid numeric identifier in the representation
their MCP client naturally produces and successfully use the existing Jira MCP example.
Maintainers have clear, automated protection for that client contract.

### In Scope

- Support for valid string-form numeric identifiers used by existing Jira MCP example tools.
- Consistent handling across all current locations where those existing tools require a
  numeric identifier.
- Documentation and automated validation of the client-visible contract.
- Preservation of the existing Jira MCP example tool count and public input names.

### Out of Scope

- Adding or removing Jira MCP tools.
- Changing the meaning of existing identifiers or accepting non-numeric identifiers where a
  numeric identifier is required.
- Changes to Jira authentication, external Jira configuration, or live Jira data.
- Implementing the underlying generic conversion capability, which is delivered by the
  completed dependency PYPOST-1037.

## Functional Requirements

- A valid numeric identifier supplied as a JSON string must be accepted by an existing Jira
  MCP example tool when that tool requires a numeric identifier.
- The user-provided identifier must be used for the requested Jira operation, not replaced
  with a default or a different value.
- Existing clients that already supply a numeric identifier in its native JSON numeric form
  must continue to receive the same behavior.
- Tools must continue to report an input error for a value that cannot represent a valid
  numeric identifier.

## Non-functional Requirements

- **Compatibility:** The existing Jira MCP example tool names, purposes, and argument names
  remain stable.
- **Reliability:** The supported input behavior is protected by routine automated checks.
- **Isolation:** Validation must not require live Jira credentials or mutate an external
  Jira project.
- **Maintainability:** User-facing documentation clearly distinguishes valid string-form
  numeric input from invalid identifier values.

## Constraints and Assumptions

- PYPOST-1037 is complete and provides the prerequisite conversion capability.
- This Story is part of the active MCP Jira Server Hardening sprint and is estimated at
  three story points.
- The repository implementation and validation language is Python.
- The task preserves the existing Jira MCP example rather than expanding its tool surface.

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow is explicitly autonomous and preauthorizes
continuing between workflow steps without a separate user approval.  An independent review
of these Step 1 artifacts is still required before this step is marked complete.

## Main Entities

| Entity | Description |
| --- | --- |
| MCP client | A user, agent, or application that invokes an existing Jira MCP tool |
| Identifier | A value that selects the Jira resource or operation the client requests |
| String-form numeric identifier | A client-supplied JSON string whose content represents a valid numeric identifier |
| Jira MCP tool | An existing published operation in the Jira MCP example |
| Jira operation | The client-requested action performed by an existing Jira tool |
| Collection author | A maintainer who relies on the example's documented client contract |
| Verification scenario | An automated check showing a supported client input produces the expected outcome |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed? | Agent and LLM clients often supply numeric identifiers as JSON strings; rejecting that normal representation prevents them from using existing Jira MCP tools. |
| What client value does this deliver? | Clients can use valid numeric identifiers in the string representation their request generators commonly produce. |
| Does this create new Jira functionality? | No. It improves the input tolerance of existing Jira MCP example tools while preserving their public surface. |
| Does this require live Jira access? | No. Verification must be isolated from live credentials and real Jira project changes. |
| Why is PYPOST-1037 excluded? | That dependency already provides the reusable conversion capability; this task applies its user-visible benefit to the Jira MCP example. |
