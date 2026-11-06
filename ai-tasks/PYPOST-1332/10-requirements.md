# PYPOST-1332: Fail closed when a rendered request path segment is blank

## Goals

When an AI agent calls a PyPost MCP tool that builds an HTTP URL from path placeholders
(for example GitLab `gitlab_project`, or analogous GitHub / Jira path variables), a blank
value must not be allowed to produce a different or unintended API path.

Today an empty path variable can render URLs such as `/projects//…` or a trailing
`/projects/` that some hosts treat as a different endpoint (for example GitLab “list
projects”) instead of failing. The outbound call still uses the tool’s HTTP method and the
collection’s authenticated token.

Business goal: **fail closed** before any network request when a rendered URL path
contains a blank segment (after ignoring the synthetic empty piece from an absolute path’s
leading `/`), so MCP tools cannot dispatch malformed or wrong-endpoint URLs. Operators and
agents get a clear, local MCP error instead of an unintended API response. GitLab and
GitHub example collections must keep offline proof that this rejection holds for
representative blank path arguments.

**Implementation language**: Python.

## User Stories

- **US1 (security-conscious operator)**: As an operator exposing GitLab or GitHub MCP tools
  with a scoped token, I want blank path placeholders to be rejected before dispatch, so an
  agent cannot hit a different same-host endpoint (or a double-slash malformed path) with
  that token and method.
- **US2 (AI agent)**: As an AI agent, when I omit or blank a path segment value, I want a
  clear MCP error and no HTTP call, so I can correct the argument instead of interpreting
  an unrelated API response.
- **US3 (collection maintainer)**: As a maintainer of the GitLab and GitHub MCP example
  collections, I want offline automated checks that demonstrate rejection for blank
  representative path-segment arguments, so regressions are caught without credentials or
  network access.
- **US4 (contributor)**: As a contributor, I want this protection to apply whenever MCP
  collection requests render URL path segments (not only one vendor), so adding similar
  collections does not reintroduce the same blank-segment gap.

## Definition of Done

Each criterion must be verifiable by offline automated checks run through `make` targets,
or by inspection of tracked documentation where noted.

1. **Fail closed on blank segments**: After placeholders and encoding are applied, if the
   rendered request URL path contains a blank segment (other than the synthetic empty from
   a leading `/` on an absolute path), the runtime must not send the HTTP request. The MCP
   caller receives a clear error indicating the path segment was rejected.
2. **Wrong-endpoint / double-slash prevented**: Concrete cases equivalent to a blank
   `gitlab_project` (mid-path `//` or trailing blank after `/projects/`) must not dispatch.
   Rejection is local; no outbound call.
3. **Legitimate non-blank segments unchanged**: Ordinary non-empty path segment values
   (including values that contain dots as part of a longer name, and already-rejected `.` /
   `..` behaviour from PYPOST-1346) continue to work as today.
4. **GitLab offline coverage**: Offline tests covering the GitLab MCP collection show that
   representative blank path-segment tools/args are rejected without contacting GitLab or
   requiring real credentials.
5. **GitHub offline coverage**: Offline tests covering the GitHub MCP collection show the
   same rejection for representative blank path-segment arguments, without contacting
   GitHub or requiring real credentials.
6. **Documentation honesty**: Developer / collection notes that currently describe blank
   path segments as an open risk or deferred check are updated to match fail-closed
   rejection (or an explicit follow-up is recorded if docs are deferred).
7. **Quality gates**: New and existing checks required by this task pass via `make`
   targets; no new failures attributable to this work.

## Task Description

### Problem

Path placeholders that render to an empty string produce empty path segments. That can
yield `//` inside a path or a trailing blank segment. Some APIs then answer a different
resource than the collection author intended (for example listing projects instead of
fetching one). MCP arguments such as GitLab project (and GitHub owner/repo-style segments)
are agent-controlled inputs into that path. Soft environment defaults and README
placeholders reduce accidents but do not stop an explicit blank override.

This was recorded as TD-2 in
[PYPOST-1316 technical debt](../PYPOST-1316/60-tech-debt.md) and ticketed as PYPOST-1332.
Related [PYPOST-1346](https://pypost.atlassian.net/browse/PYPOST-1346) already rejects
whole-segment `.` / `..` at the HTTP prepare seam; blank-segment fail-closed is the
remaining acceptance concern on that same seam.

### Business reason

PyPost turns curated collections into MCP tools that run with the operator's API token.
Operators must be able to trust that tool URLs stay on the paths the collection author
defined. Dispatching with blank path segments breaks that trust and can surface unrelated
API data under the same credentials. Fail-closed rejection restores the intended tool
contract for GitLab, GitHub, and any similar MCP collections.

### Scope

In scope:

- Runtime behaviour: reject rendered request URLs whose path contains a blank segment
  (ignoring only the synthetic leading empty from an absolute path), before any network
  dispatch, with a clear TEMPLATE-category error to the MCP caller.
- Offline automated proof for representative GitLab and GitHub MCP collection blank
  path-segment cases.
- Aligning developer / collection documentation that currently calls blank segments an
  open risk with the new fail-closed behaviour.

Out of scope:

- Dot-segment `.` / `..` rejection (already owned by PYPOST-1346), except that both guards
  share the same HTTP prepare checkpoint.
- Changing which characters are percent-encoded for ordinary path segments.
- Host, scheme, or port rewriting; open redirects to other hosts; or token-scope reduction.
- Live calls to GitLab, GitHub, or any external host; tests that need real credentials.
- Broad redesign of MCP protocol, auth types, or collection format.
- A separate per-variable “required” manifest flag as the sole mechanism (optional design
  note only); product acceptance is fail-closed on blank **rendered path segments**.
- Rejecting whitespace-only segments that are not empty after split (unless they render as
  an empty segment).

### Constraints and assumptions

- Valid GitLab project paths and valid GitHub owner/repository names are non-empty;
  rejection does not remove a supported legitimate identifier.
- Empty query parameter values are already dropped at prepare time; this task is about
  **path** segments only.
- All repository build, test, lint, and verification operations run through `make`
  (AGENTS.md).
- Implementation language is Python.

### Main entities

- **MCP caller**: agent or client invoking a collection-backed tool with argument values.
- **Path segment placeholder**: collection argument or variable intended as one URL path
  segment (for example project, owner, repository, file path).
- **Rendered request URL**: the concrete URL after template substitution and encoding,
  before dispatch.
- **Blank path segment**: a path segment whose entire value is empty after the URL path is
  split on `/`, other than the synthetic empty from a leading `/`.
- **Fail-closed rejection**: local refusal to dispatch, surfaced as a clear MCP error.
- **GitLab / GitHub MCP collections**: example collections whose offline tests must prove
  the rejection for representative blank path-segment tools.
- **Operator token**: credential attached to the collection environment; must not be used
  on an unintended same-host path because of blank-segment rendering.

### Functional requirements

- FR1: Detect blank path segments in the rendered URL path after substitution and encoding.
- FR2: Do not dispatch the HTTP request when such a segment is present.
- FR3: Return a clear, actionable TEMPLATE-category error to the MCP caller.
- FR4: Leave behaviour for non-blank whole segments unchanged (and keep PYPOST-1346
  `.` / `..` rejection).
- FR5: Provide offline regression coverage for GitLab and GitHub example collections on
  representative blank path-segment arguments.

### Non-functional requirements

- NFR1: Rejection is local and deterministic; no external network dependency.
- NFR2: Offline tests use bounded timeouts per repository testing standards.
- NFR3: Security posture is fail-closed: when a blank path segment is present, refuse the
  request.
- NFR4: Change remains narrowly scoped to this path-safety gap and related docs/tests;
  reuse the PYPOST-1346 checkpoint rather than inventing a second transport gate.

## Q&A

- **Q: Why not only document soft defaults / placeholders?** A: Defaults reduce accidents
  but an explicit blank override still dispatches today. Runtime fail-closed is required.
- **Q: Why not only a manifest `required: true` flag?** A: A required flag helps at the
  argument layer for one collection, but blank segments can also arise from env overrides
  and templates. Rejecting blank **rendered path segments** at the shared HTTP seam covers
  all collections; a required-flag-only design is optional later, not the DoD.
- **Q: How does this relate to PYPOST-1346?** A: Same prepare checkpoint and TEMPLATE
  error category. Dot vs blank are separate acceptance criteria; this ticket extends the
  seam without changing the `.` / `..` policy.
- **Q: Must every GitLab/GitHub tool be tested?** A: Representative blank path arguments
  (at least project / owner / repo style) are required. Exhaustive per-tool matrices are
  not required if the guard is shared for all rendered paths.
- **Q: Who accepts these requirements?** A: The autonomous orchestrator after independent
  review (reviews are separate from this execution).

### References

- Source debt: [PYPOST-1316 TD-2](../PYPOST-1316/60-tech-debt.md)
- Related seam: [PYPOST-1346](../PYPOST-1346/20-architecture.md) (dot path segments)
- Context: GitLab collection PYPOST-1316; design risk R2; `doc/dev/gitlab_mcp_collection.md`
  current blank-segment notes
