# PYPOST-1034: MCP request templates must substitute query and body arguments

## Goals

PyPost users need confidence that an MCP tool applies the arguments they provide
wherever the corresponding collection requires them.  Existing coverage proves
this outcome for a path value, but not for values used as query parameters or in
a request body.  This task provides evidence that the existing Jira MCP example
honors supplied arguments in those two remaining request locations.

**Programming language:** Python

## User Stories

- As an **MCP client user**, I want an argument I pass to an existing Jira MCP
  tool to be reflected in its query criteria, so I receive results for the
  requested value.
- As an **MCP client user**, I want an argument I pass to an existing Jira MCP
  tool to be reflected in its request body, so the requested operation uses my
  supplied value.
- As a **collection author**, I want the Jira MCP example's request templates
  to be verified for path, query, and body value locations, so I can rely on
  the documented argument contract when creating similar tools.
- As a **maintainer**, I want automated coverage for the two unverified
  locations, so a future change cannot silently leave an MCP argument as
  template text.

## Definition of Done

- [ ] Automated MCP-level coverage demonstrates that a supplied tool argument
      is used in an outgoing query parameter for an existing Jira MCP example
      shape.
- [ ] Automated MCP-level coverage demonstrates that a supplied tool argument
      is used in an outgoing JSON request body for an existing Jira MCP example
      shape.
- [ ] The covered tool calls report their normal successful outcomes when the
      expected argument values are supplied.
- [ ] The coverage complements the existing path-argument proof without
      changing the set of Jira MCP tools or their public argument contract.
- [ ] Tests remain bounded and suitable for the project's automated test suite.

## Task Description

**Problem:** The prior correction established that MCP tool arguments can fill
path values, but users and maintainers do not yet have equivalent automated
proof for query parameters and JSON bodies.  Without that proof, a regression
could cause an existing Jira MCP tool to search or submit using literal template
text rather than the client's intended argument.

**Business outcome:** Existing Jira MCP tools reliably honor user-supplied
arguments across the request locations used by the example.  Maintainers can
detect a broken argument-to-request flow before it reaches MCP clients.

### In Scope

- Automated end-to-end evidence for argument use in query parameter and JSON
  body locations of existing Jira MCP example request shapes.
- Assertions that each covered tool call receives the client-supplied value and
  completes successfully under the test scenario.
- Preservation of the current public Jira MCP example tool set and argument
  names.

### Out of Scope

- Adding, removing, or renaming Jira MCP tools or arguments.
- Changes to Jira authentication, credentials, or external Jira service setup.
- A redesign of collection authoring or the template language.
- Broader changes to request behavior beyond the two unverified locations.

## Functional Requirements

- A caller-provided MCP argument used by an existing Jira MCP query operation
  must reach the query sent on that caller's behalf.
- A caller-provided MCP argument used by an existing Jira MCP body operation
  must reach the JSON body sent on that caller's behalf.
- The verification must cover the request shapes already represented by the
  Jira MCP example, rather than inventing a new public use case.
- The expected client-visible result of each covered operation must be
  confirmed.

## Non-functional Requirements

- **Reliability:** The coverage must make regressions in query/body argument
  handling visible in routine automated validation.
- **Compatibility:** Existing MCP users and collection authors retain the same
  tools and argument contract.
- **Isolation:** Verification must not depend on live Jira credentials or
  mutate a real Jira project.
- **Maintainability:** Scenarios should clearly identify the user-supplied
  argument and the request location whose behavior they protect.

## Constraints and Assumptions

- Issue type: Debt; priority: Medium; labels: `mcp`, `tech-debt`, `templates`;
  story points: 3.
- Jira browse: https://pypost.atlassian.net/browse/PYPOST-1034
- This is the follow-up TD-1 from PYPOST-1033; path argument behavior is
  already covered there.
- The Jira MCP example defines the existing query and body request shapes to
  protect.
- Python is the repository's implementation and test language.

## STEP 1 Approval Basis

The applicable `sprint-runner` workflow explicitly runs its phases in
autonomous mode and preauthorizes continuing without a separate confirmation
between phases. That explicit autonomous preapproval is the approval basis for
this completed requirements step.

## Main Entities

| Entity | Description |
| --- | --- |
| MCP client | User or agent that calls a published MCP tool with named arguments |
| MCP tool call | A client request to perform an existing Jira-related operation |
| Supplied argument | The value the client expects the operation to use |
| Query operation | An existing tool operation whose result is selected using a query value |
| Body operation | An existing tool operation whose requested action includes a structured value |
| Collection template | Author-maintained request description that maps an MCP tool call to its destination request |
| Verification scenario | Automated evidence that records the client value and confirms the resulting operation used it |

## Q&A

| Question | Answer |
| --- | --- |
| Why is this task needed after PYPOST-1033? | PYPOST-1033 demonstrated safe argument handling and an MCP path scenario. This follow-up closes the remaining automated evidence gap for query and body locations. |
| What user value does this deliver? | MCP users can trust that existing Jira tools use the values they provide, while maintainers receive early warning if that contract regresses. |
| Does this add Jira functionality? | No. It verifies the behavior of existing Jira MCP tool scenarios and preserves their public contract. |
| Does this require access to a live Jira project? | No. The required verification is isolated from live credentials and real-project changes. |
| Why are template mechanics not specified here? | This document states the observable user contract. The later architecture step will decide the appropriate test arrangement. |
