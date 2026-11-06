# PYPOST-1346: Reject `.` and `..` as rendered URL path segments in MCP
collection requests

## Goals

When an AI agent calls a PyPost MCP tool that builds an HTTP URL from path placeholders
(for example GitHub owner, repository, or workflow identifier, or the GitLab equivalents),
a value that is exactly `.` or `..` must not be allowed to change which path on the
configured API host is actually requested.

Today those values survive path encoding as literal segments. The HTTP stack then
normalises them (for example a URL whose path contains `/repos/../user` is resolved to
`/user`). The outbound call still uses the tool's HTTP method and the collection's
authenticated token. An MCP caller can therefore steer a request onto a different same-host
API path than the collection author intended.

Business goal: **fail closed** before any network request when a rendered URL path
segment is exactly `.` or `..`, so MCP tools cannot be used to traverse or rewrite the
intended path on the same host. Operators and agents get a clear, local failure instead of
a silent redirect to another endpoint. GitHub and GitLab example collections must keep
offline proof that this rejection holds.

**Implementation language**: Python.

## User Stories

- **US1 (security-conscious operator)**: As an operator exposing GitHub or GitLab MCP tools
  with a scoped token, I want path placeholders that resolve to `.` or `..` to be rejected
  before dispatch, so an agent cannot reach unintended same-host API paths with that token
  and method.
- **US2 (AI agent)**: As an AI agent, when I supply `.` or `..` (or a value that renders as
  such) for a path segment, I want a clear MCP error and no HTTP call, so I can correct the
  argument instead of interpreting an unrelated API response.
- **US3 (collection maintainer)**: As a maintainer of the GitHub and GitLab MCP example
  collections, I want offline automated checks that demonstrate rejection for representative
  path-segment arguments in both collections, so regressions are caught without credentials
  or network access.
- **US4 (contributor)**: As a contributor, I want this protection to apply whenever MCP
  collection requests render URL path segments (not only one vendor), so adding similar
  collections does not reintroduce the same traversal gap.

## Definition of Done

Each criterion must be verifiable by offline automated checks run through `make` targets,
or by inspection of tracked documentation where noted.

1. **Fail closed on dot segments**: After placeholders and encoding are applied, if any
   path segment of the rendered request URL is exactly `.` or exactly `..`, the runtime
   must not send the HTTP request. The MCP caller receives a clear error indicating the
   path segment was rejected.
2. **Same-host traversal prevented**: A concrete case equivalent to substituting `..` for a
   GitHub path argument (owner, repository, or workflow identifier) or a GitLab path
   argument that participates in the URL path must not result in a resolved request to a
   different path on the same host. Rejection happens locally; no outbound call.
3. **Legitimate segments unchanged**: Ordinary non-dot path segment values (including
   values that contain dots as part of a longer name, such as a workflow file name like
   `ci.yml`, or encoded multi-part paths that are not the entire segment `.` / `..`)
   continue to work as today.
4. **GitHub offline coverage**: Offline tests covering the GitHub MCP collection show that
   representative path-segment tools reject `.` and `..` for the relevant arguments,
   without contacting GitHub or requiring real credentials.
5. **GitLab offline coverage**: Offline tests covering the GitLab MCP collection show the
   same rejection for representative path-segment arguments, without contacting GitLab or
   requiring real credentials.
6. **Documentation honesty**: User-facing notes that currently describe `.` / `..` as an
   unsupported limitation are updated so they match the fail-closed behaviour (rejection,
   not silent normalisation), or an explicit follow-up is recorded if docs are deferred.
7. **Quality gates**: New and existing checks required by this task pass via `make`
   targets; no new failures attributable to this work.

## Task Description

### Problem

Path encoding used for MCP collection URL placeholders leaves a segment that is exactly
`.` or `..` unchanged. Downstream HTTP clients resolve those segments, so the request that
leaves PyPost can target a different path on the same API host than the collection template
described. MCP arguments such as GitHub owner, repository, and workflow identifier (and
GitLab path counterparts) are attacker- or agent-controlled inputs into that path. Token
scope remains a boundary, but it does not stop same-host path rewriting within what the
token can already call.

This was recorded as TD-17 in
[PYPOST-1334 technical debt](../PYPOST-1334/60-tech-debt.md) and ticketed as PYPOST-1346.
Related debt [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332) covers blank
rendered path segments; both are path-safety gaps, but blank and dot-segment failures are
distinct acceptance concerns.

### Business reason

PyPost turns curated collections into MCP tools that run with the operator's API token.
Operators must be able to trust that tool URLs stay on the paths the collection author
defined. Silent path normalisation of `.` / `..` breaks that trust and can surface
unrelated API data or side effects under the same credentials. Fail-closed rejection
restores the intended tool contract for GitHub, GitLab, and any similar MCP collections.

### Scope

In scope:

- Runtime behaviour: reject rendered request URLs whose path contains a segment exactly
  equal to `.` or `..`, before any network dispatch, with a clear error to the MCP caller.
- Offline automated proof for representative GitHub and GitLab MCP collection path-segment
  cases.
- Aligning user-facing documentation that currently calls out the `.` / `..` limitation
  with the new fail-closed behaviour (or explicitly deferring that doc update).

Out of scope:

- Blank / empty rendered path segments (owned by PYPOST-1332), except that Step 2 may note
  whether the two guards share a delivery if that does not expand product scope.
- Changing which characters are percent-encoded for ordinary path segments (already
  covered for `/`, spaces, and other reserved characters in collection encoding rules).
- Host, scheme, or port rewriting; open redirects to other hosts; or token-scope reduction.
- Live calls to GitHub, GitLab, or any external host; tests that need real credentials.
- Broad redesign of MCP protocol, auth types, or collection format.
- Rejecting every string that merely contains a dot (only whole-segment `.` and `..`).

### Constraints and assumptions

- Valid GitHub owner/repository/workflow names and valid GitLab path segment values are
  not exactly `.` or `..`; rejection does not remove a supported legitimate identifier.
- Existing encoding already prevents `/` and many reserved characters from splitting or
  escaping a segment; this task closes the remaining whole-segment dot case.
- All repository build, test, lint, and verification operations run through `make`
  (AGENTS.md).
- Implementation language is Python.

### Main entities

- **MCP caller**: agent or client invoking a collection-backed tool with argument values.
- **Path segment placeholder**: collection argument or variable intended as one URL path
  segment (for example owner, repository, workflow identifier, project path, file path,
  branch, or SHA when used in the path).
- **Rendered request URL**: the concrete URL after template substitution and encoding,
  before dispatch.
- **Dot path segment**: a path segment whose entire value is `.` or `..`.
- **Fail-closed rejection**: local refusal to dispatch, surfaced as a clear MCP error.
- **GitHub / GitLab MCP collections**: example collections whose offline tests must prove
  the rejection for representative path-segment tools.
- **Operator token**: credential attached to the collection environment; must not be used
  on an unintended same-host path because of dot-segment normalisation.

### Functional requirements

- FR1: Detect whole-segment `.` and `..` in the rendered URL path after substitution and
  encoding.
- FR2: Do not dispatch the HTTP request when such a segment is present.
- FR3: Return a clear, actionable error to the MCP caller (not an opaque transport failure
  from a rewritten path).
- FR4: Leave behaviour for non-dot whole segments unchanged.
- FR5: Provide offline regression coverage for GitHub and GitLab example collections on
  representative path-segment arguments.

### Non-functional requirements

- NFR1: Rejection is local and deterministic; no external network dependency.
- NFR2: Offline tests use bounded timeouts per repository testing standards.
- NFR3: Security posture is fail-closed: when in doubt for exact `.` / `..` segments,
  refuse the request.
- NFR4: Change remains narrowly scoped to this path-safety gap and related docs/tests.

## Q&A

- **Q: Why is this a product fix rather than only documentation?** A: The README already
  notes that `.` / `..` are unsupported, but the runtime still dispatches and the HTTP
  client may rewrite the path. Documentation alone does not stop an MCP caller from
  reaching another same-host path with the tool token.
- **Q: Why not rely on token scope alone?** A: Token scope limits *which* APIs the token
  may call, but does not keep a tool on its *declared* path. Same-host rewriting stays
  inside what a broad token can already access.
- **Q: How does this relate to PYPOST-1332 (blank segments)?** A: Both are fail-closed
  path-safety gaps. Blank segments and `.` / `..` segments are separate acceptance
  criteria. Delivering them together is optional and decided in architecture; neither
  ticket absorbs the other's DoD.
- **Q: Must every GitHub/GitLab tool be tested individually?** A: Representative
  path-segment arguments that participate in the URL path are required (at least covering
  the argument classes called out in TD-17: GitHub owner/repo/workflow-style segments and
  analogous GitLab path segments). Exhaustive per-tool matrices are not required if Step 2
  shows the guard is shared for all rendered paths.
- **Q: Are values like `ci.yml` or `foo.bar` rejected?** A: No. Only a segment whose
  entire value is `.` or `..` is in scope.
- **Q: Who accepts these requirements?** A: The autonomous sprint orchestrator after
  independent review.

### References

- Source debt: [PYPOST-1334 TD-17](../PYPOST-1334/60-tech-debt.md)
- Related: [PYPOST-1332](https://pypost.atlassian.net/browse/PYPOST-1332) (blank path
  segment)
- Context: GitHub collection [PYPOST-1334](../PYPOST-1334/10-requirements.md); GitLab
  collection PYPOST-1316; `examples/README.md` current `.` / `..` limitation notes
