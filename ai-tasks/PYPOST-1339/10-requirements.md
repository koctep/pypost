# PYPOST-1339: Trustworthy surviving-template-marker checks for MCP collections

## Goals

Maintainers need MCP example-collection tests that detect real leftover template markers after
a full render, without failing on legitimate nested JSON that appears when a body ends with an
object field. The current check constrains fixture design (field order workarounds) and does
not inspect the rendered body text where an unrendered marker would actually appear.

## User Stories

- As a collection maintainer, I can rely on the GitHub and GitLab MCP full-render marker checks
  to fail only when template markers remain after rendering, not when a correctly rendered body
  ends with a nested object.
- As a collection author, I can order body fields for clarity (for example putting `ref` before
  `inputs` on workflow dispatch) without rearranging them solely to dodge a false positive.
- As a reviewer, I can see explicit coverage that a nested-object final field no longer trips
  the marker check, so a future tool with that shape does not reintroduce the same debt.

## Definition of Done

1. The GitHub and GitLab MCP full-render “no surviving template markers” checks judge the body
   by the text produced when the request body template is rendered, not by a re-serialized form
   of the already-parsed payload.
2. A correctly rendered request body whose last field is a nested object does not fail those
   checks solely because of that structure.
3. Real leftover template markers (`{{`, `}}`, `{%`, `%}`) in a rendered URL, header, query
   value, or body still cause the checks to fail.
4. Optional: the GitHub workflow-dispatch example body may use a natural field order with `ref`
   before `inputs` once the marker check no longer forces the workaround order.
5. Automated coverage includes a twin case that proves a nested-object final field no longer
   false-positives under the corrected check.
6. Changes stay within the test modules named in the debt item, plus the optional dispatch body
   field-order restoration in the GitHub example collection if chosen; no production runtime
   behavior change is required for this debt.
7. Existing MCP collection contract coverage, timeouts, and Make-driven quality gates remain
   effective for the touched suites.

## Task Description

### Problem and evidence

Parent debt: [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) TD-1, recorded in
`ai-tasks/PYPOST-1334/60-tech-debt.md`.

`tests/test_github_mcp_collection.py::test_github_mcp_full_render_leaves_no_template_markers`
and the matching check in `tests/test_gitlab_mcp_collection.py` currently include a
re-serialized form of the parsed request body when searching for template markers. Any body
whose last field is a nested object can therefore match a closing `}}` even when the rendered
template is correct. The GitHub `github_dispatch_workflow` body was ordered with `inputs`
before `ref` only to avoid that false positive; the order does not matter to GitHub, but the
test now constrains fixture design. The check also does not inspect the raw rendered body text,
which is where a surviving marker would show up.

### Business reason

Offline MCP collection tests are the gate that example collections are fully rendered and free
of leftover template markers before they ship. A check that false-positives on valid nested JSON
undermines that gate: authors rearrange payloads to silence the test, future tools with an
object as the last field hit the same trap, and genuine unrendered markers in the body template
are not what the body portion of the check actually examines. Fixing the check restores trust
in the gate and removes an artificial constraint on example body layout.

### Implementation language

Python.

### Scope

- Correct the surviving-marker verification for full renders in the GitHub and GitLab MCP
  collection test modules so body inspection uses the rendered body text.
- Add a twin proving that a nested-object final field no longer false-positives.
- Optionally restore a natural `ref`-before-`inputs` order on the GitHub workflow-dispatch
  example body once the check no longer requires the workaround.
- Keep the work test-suite (and optional example body field-order) scoped; no change to MCP
  request execution semantics is required.

### Out of scope

- Extracting shared MCP example-collection test helpers (tracked as PYPOST-1340 / TD-2).
- Other PYPOST-1334 follow-ups (API version migration, schema enum/`items`, type-preserving
  JSON helpers, empty-body success coverage, path-segment hardening, and related tickets).
- Changing how GitHub or GitLab interpret dispatch or other API payloads beyond optional
  restoration of field order that the API already treats as equivalent.
- Live GitHub/GitLab smoke tests or production MCP server behavior changes.

### Functional requirements

- Full-render marker checks for GitHub and GitLab MCP collections continue to cover URL,
  headers, query values, and body content for full and minimal argument sets.
- Body marker detection is based on the rendered body template output, not on re-serializing a
  parsed payload that can introduce structural `}}` unrelated to templates.
- Nested JSON objects as the last body field must not by themselves fail the marker check.
- Surviving template markers in rendered content must still fail the check.
- A dedicated twin case documents and guards the nested-object-final-field scenario.
- Optional restoration of dispatch body field order is allowed only as a clarity cleanup after
  the false positive is gone; API semantics must remain unchanged.

### Non-functional requirements and constraints

- Verification remains offline, repeatable, and bounded by existing test timeout rules.
- Repository build, analysis, test, dependency, and artifact-verification operations use Make.
- Preserve unrelated files, completed task records, and existing production quality coverage.
- Scope remains limited to this Jira debt issue (PYPOST-1339) and the TD-1 evidence above.
- Estimate context from Jira: approximately 2 story points; test-only change in two modules
  plus one twin test (optional example body reorder included when chosen).

### Main entities

- **Rendered request surface**: URL, headers, query values, and body text after template
  rendering for an MCP tool request.
- **Surviving template marker**: leftover `{{`, `}}`, `{%`, or `%}` that indicates incomplete
  rendering.
- **Nested final body field**: a correctly rendered JSON object that is the last field of a
  request body and must not be mistaken for a template marker.
- **Marker check**: the full-render verification that asserts no surviving markers remain.
- **Workflow-dispatch example body**: the GitHub dispatch request body whose field order was
  previously adjusted only to satisfy the faulty check.

## Q&A

- **Why not keep scanning the parsed-then-re-serialized body?** That form can end with `}}`
  from nested JSON even when rendering succeeded, so it both false-positives and misses checking
  the raw rendered body text where markers would appear.
- **Is restoring `ref` before `inputs` mandatory?** No. Jira marks it optional; it is a clarity
  cleanup once the check no longer forces the workaround. API behavior is unchanged either way.
- **Does this change runtime MCP behavior?** No. The debt is about trustworthy offline
  verification (and optional example field order), not request execution.
- **Why a twin test?** Without an explicit nested-object-final-field case, a future regression
  to the re-serialize approach could return unnoticed until another tool hits the same trap.
- **Who accepts these requirements?** The autonomous sprint orchestrator after independent
  review.
