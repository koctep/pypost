# PYPOST-1038: Technical Debt Analysis

## Review Scope

Reviewed the explicit `integer_or_string` MCP schema, its request-editor
authoring option, native-integer `to_int` support, the six Jira fixture path
mappings, and the isolated real-MCP/loopback coverage for accepted and
rejected identifier forms.

## Shortcuts Taken

None. The change introduces one constrained reusable schema type and applies
it only to the six existing Jira board/sprint identifier locations. The tests
load the shipped collection, preserve each path template, and replace only the
network destination with a local loopback server; no hand-written surrogate
tool contract or live Jira dependency is used.

## Code Quality Issues

None identified. `integer_or_string` maps to a precise JSON Schema `anyOf`:
native JSON integer or an ASCII decimal string with an optional sign. Existing
scalar MCP parameter schemas retain their original output. `_to_int` accepts a
true `int` while continuing to reject `bool`, floats, and all non-decimal
strings, so the strict HTTP boundary remains fail-closed.

## Missing Tests

None for the agreed scope. Coverage proves:

- importer and schema publication of the union while preserving legacy scalar
  schemas;
- native-integer acceptance and bool/float rejection in `to_int`;
- all and only the six fixture mappings use the union and strict path template;
- both `"42"` and `42` dispatch successfully through a real MCP server to a
  loopback HTTP boundary for every affected path; and
- invalid string and float inputs produce no outbound HTTP request.

The integration module retains its explicit module-level timeout marker and
bounded server-thread joins. Live Jira validation is intentionally out of
scope because it would require credentials and mutate external state without
adding coverage beyond the isolated boundary tests.

## Performance Concerns

None. The schema union is built when tool metadata is published; `to_int`
performs one bounded type check or regex match while preparing an already
templated request. No background work, storage, new dependency, or external
network call is introduced.

## Follow-up Tasks

No PYPOST-1038 follow-up issue is required. The low-priority resolver
provenance refactor recorded by PYPOST-1037 remains separate pre-existing
technical debt; this task uses its established strict-conversion boundary and
does not extend that coupling.

## Independent Blocker Review

**PASS — safe to proceed to Step 8.** An independent reviewer found no
actionable blocker. The review confirmed that the union schema, strict
conversion, all six Jira path mappings, and fail-closed invalid-input behavior
match the architecture. The focused suite passed with **114 tests**, including
real MCP-to-loopback checks for both `"42"` and `42` across every affected
path. `git diff --check` is clean.

The autonomous sprint workflow and the user's standing requirement for an
independent subagent on every review provide the approval basis for completing
this step.

## Worklog

```text
role: execution
step: 7
step_name: Review and Technical Debt
actions: reviewed union schema, strict conversion, fixture wiring, test scope,
  and prior cleanup/observability evidence; recorded debt assessment and roadmap status
time_spent: 12m
tokens_used: 6200

role: independent reviewer
step: 7
step_name: Blocker Review
verdict: PASS — no blocker; no follow-up technical debt
actions: verified requirements/architecture alignment, union schema, all six
  path mappings, fail-closed behavior, and focused-test evidence
time_spent: 8m
tokens_used: 1800
```
