# PYPOST-1033: MCP request templates must substitute tool arguments

## Goals

Operators and integrators use PyPost MCP to call collection tools (including the
jira-mcp example) by passing tool arguments. Those arguments must appear in the
outgoing HTTP request wherever the collection uses placeholders of the form
`{{ mcp.request.<param> }}` (path, query, or body).

Today those placeholders are left unsubstituted. Tools that need arguments fail
even when authentication and direct REST with the same credentials succeed. This
task restores reliable argument substitution for MCP-invoked tools so the
existing jira-mcp surface works end-to-end via `call_tool`.

**Programming language:** Python

## User Stories

- As an **MCP client user**, I want tool arguments I pass to `call_tool` to be
  applied to the request path, query, and body so Jira (and similar) tools
  receive real values instead of template text.
- As a **collection author**, I want plain dotted placeholders such as
  `{{ mcp.request.issue_key }}` to render when MCP supplies nested request
  variables, without rewriting every tool to a different placeholder style.
- As a **security-conscious operator**, I want unsafe attribute-style template
  expressions (for example attempts to reach privileged object internals) to
  remain rejected after the fix.
- As a **maintainer**, I want automated tests that prove MCP request placeholders
  render with nested variables and that jira-mcp example tools succeed via MCP
  `call_tool` after the fix.

## Definition of Done

- [ ] Placeholders of the form `{{ mcp.request.<param> }}` validate and render
      when MCP provides nested request arguments.
- [ ] Existing nested function / expression safety rules that reject unsafe
      attribute forms remain unchanged in behavior.
- [ ] Unit and/or integration tests cover rendering
      `{{ mcp.request.issue_key }}` (or equivalent) with nested MCP request
      variables.
- [ ] jira-mcp example tools that depend on MCP request placeholders succeed via
      MCP `call_tool` against a local MCP server after the fix (path, query, and
      body cases covered by the example).
- [ ] This bug does not expand the jira-mcp tool surface (no new Jira tools).

## Task Description

**Problem:** PyPost MCP exposes jira-mcp tools and env-based auth works for
tools that need no request parameters. Any tool that relies on
`{{ mcp.request.* }}` fails: path tools error, body tools send unsubstituted
template text (downstream 400), query tools leave keys unsubstituted
(downstream 404). Direct REST with the same credentials succeeds; the gap is
template substitution for MCP-supplied arguments.

**Business outcome:** MCP tool arguments must flow into collection templates so
published MCP tools behave as documented.

### In Scope

- Correct behavior so safe dotted MCP request paths used by the product
  (`mcp.request.<param>`) validate and render.
- Tests for template render and MCP `call_tool` with MCP request arguments.
- Re-verification of the existing jira-mcp example against local MCP.
- Preservation of current rejection behavior for unsafe attribute forms.

### Out of Scope

- Expanding the jira-mcp example tool set or adding new Jira capabilities.
- Changing MCP authentication or env credential wiring (already working).
- Redesigning the overall template language or collection format.
- Broader template features unrelated to MCP request argument substitution.

## Functional Requirements

- When an MCP tool is invoked with arguments, corresponding
  `{{ mcp.request.<param> }}` placeholders in the mapped request are
  substituted before the HTTP call.
- Substitution works for values used in URL path, query parameters, and
  request body as defined by the collection.
- Nested function / expression rules that already reject unsafe attribute
  access continue to reject those forms.
- Automated tests demonstrate successful render of MCP request placeholders
  with nested variables and successful `call_tool` for affected jira-mcp
  examples.

## Non-functional Requirements

- **Compatibility:** Existing collections and template expressions that already
  work must keep working; only the MCP dotted-path gap is closed.
- **Safety:** No regression that allows previously rejected unsafe attribute
  expressions to render.
- **Verifiability:** Fix is demonstrable via tests and local MCP re-check of
  the jira-mcp example (related: PYPOST-1026 collection; starter PYPOST-1017).

## Constraints and Assumptions

- Issue type: Bug; priority: High; labels: mcp, templates; story points: 5.
- Jira browse: https://pypost.atlassian.net/browse/PYPOST-1033
- Live repro context: local MCP on 127.0.0.1:1080 with jira-mcp tools; auth
  tools without request params already succeed.
- MCP merges call arguments into a nested request variable tree available to
  templates as `mcp.request.*` (business contract for authors; not a design
  prescription for how validation is implemented).
- Scope is limited to restoring that contract for safe dotted paths used by MCP.

## Main Entities

| Entity | Description |
| --- | --- |
| MCP tool call | Client invocation of a published tool with named arguments |
| MCP request arguments | Values supplied on the call, available to templates as nested request fields |
| Template placeholder | Author-written `{{ ... }}` expression in path, query, or body |
| Collection tool mapping | Example/collection binding of an MCP tool to an HTTP request |
| Unsafe attribute form | Template expression that must remain rejected for safety |

## Q&A

| Question | Answer |
| --- | --- |
| Why not only document a different placeholder style? | Authors and the jira-mcp example already use `mcp.request.*`; the product must honor that contract so MCP tools work without rewriting collections. |
| Why keep rejecting unsafe attribute forms? | Closing the MCP path gap must not weaken template safety guarantees operators rely on. |
| Are new Jira tools in scope? | No — only make the existing jira-mcp example tools work via MCP after substitution is fixed. |
| Is auth part of this bug? | No — env auth already works; failures are unsubstituted request arguments. |
