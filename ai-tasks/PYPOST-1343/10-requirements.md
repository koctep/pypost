# PYPOST-1343: Type-preserving JSON serialization for request body templates

## Programming Language

Python is the implementation language for the application runtime, curated example
collections, and automated test suites. English Markdown is used for workflow
documentation and technical artifacts.

## Goals

Request body templates today can only emit JSON **strings** through `to_json_string`.
Curated GitHub (and similar) MCP tools must hand-build arrays, objects, and booleans with
Jinja loops and literals. Workflow-dispatch input values are always forced to strings, and
authors are told that inputs are "scalar values only".

**Business goal:** Give collection authors a template helper that serializes lists, dicts,
booleans, and numbers with their native JSON types so curated MCP request bodies stay
correct and readable without hand-rolled Jinja structure, and dispatch inputs can carry
typed scalars instead of stringified ones.

## User Stories

- As an **API collection author**, I want a template function that emits JSON with correct
  types for arrays, objects, booleans, and numbers, so that I do not hand-build those
  structures with loops and literals.
- As an **AI agent calling GitHub MCP tools**, I want `labels` / `assignees` arrays,
  `draft` / `enable_debug_logging` booleans, and dispatch `inputs` objects to keep their
  JSON types on the wire, so that the remote API receives well-typed bodies.
- As an **AI agent dispatching a workflow**, I want boolean and numeric input values to
  remain JSON booleans/numbers (not `"true"` / `"3"`), so that typed workflow inputs are
  not silently stringified by the template layer.
- As a **contributor / maintainer**, I want locked offline tests and user/dev docs updated
  so the old "scalar values only / always strings" contract is no longer asserted or
  documented as required by PyPost.
- As a **collection author using GitLab MCP examples**, I want the same helper available
  for future typed body fields; existing string-only GitLab bodies must keep working.

## Definition of Done

- [ ] A registered template function (for example `to_json`) serializes lists, dicts,
  booleans, numbers, strings, and null with their JSON types (not always as strings).
- [ ] Existing `to_json_string` behavior is unchanged (still string-literal escaping).
- [ ] GitHub MCP example bodies no longer hand-build arrays/objects/booleans with Jinja
  loops or `true`/`false` literals where the new helper applies (`labels`, `assignees`,
  `inputs`, `draft`, `enable_debug_logging`).
- [ ] Locked GitHub body/template tests expect type-preserving serialization (including
  dispatch inputs that keep bool/number types).
- [ ] User-facing and developer docs that said "scalar values only" / "values are sent as
  strings" for dispatch inputs are updated to match the new contract.
- [ ] GitLab MCP examples remain valid; no regression in string body fields.
- [ ] PYPOST-1342 enum/items schema work is not broken.
- [ ] Offline automated tests cover the helper and updated collection contracts.

## Task Description

**Problem:**
Follow-up from PYPOST-1334 TD-6 (architecture risks R4, R5). `to_json_string` always
stringifies. GitHub MCP bodies compensate with Jinja `{% for %}` loops and boolean
literals; dispatch inputs are coerced to strings; docs warn authors about scalars only.

**Scope (in):**
- Type-preserving JSON template helper, registered for Jinja templates.
- Simplify GitHub MCP example request bodies that currently hand-build non-string JSON.
- Update locked template/body tests and docs that encode the old string-only contract.
- Confirm GitLab MCP examples still pass (string labels remain strings).

**Scope (out):**
- Changing MCP param schema shape (`enum` / `items` — PYPOST-1342).
- Live GitHub/GitLab network tests.
- A generic "build JSON object from present args" helper beyond `to_json`.
- Rewriting every string field from `to_json_string` to `to_json` (optional for strings;
  required only where types must be preserved).

**Constraints and assumptions:**
- Verification is offline and deterministic.
- Non-JSON-serializable values may fail closed at render time (same class of failure as
  other bad template outputs).
- Do not break PYPOST-1342 enum/items contracts on GitHub/GitLab params.

## Main Entities and Interactions

- **Template helper catalog:** Allow-listed functions authors call inside request templates.
- **JSON string literal helper:** Existing helper that always emits a quoted JSON string.
- **Type-preserving JSON helper:** New helper that emits JSON text with native types.
- **Curated MCP collections:** GitHub (primary simplification) and GitLab (compatibility).
- **Locked offline tests:** Prove helper registration, type preservation, and body render
  contracts.

**Interaction Flow:**
1. An author writes `"labels": {{ to_json(mcp.request.labels) }}` (or equivalent) in a body.
2. An agent supplies a list/dict/bool/number argument.
3. The rendered body contains a JSON array/object/boolean/number, not a stringified form.
4. Offline tests assert the rendered payload types and updated docs match that contract.

## Non-Functional Requirements

- **Compatibility:** `to_json_string` and existing string-only templates keep working.
- **Safety:** String values still get proper JSON escaping when passed through the helper.
- **Deterministic offline verification:** No live provider credentials required.
- **Clarity:** Docs distinguish "always a JSON string" (`to_json_string`) from
  "preserve JSON type" (`to_json`).

## Q&A

**Q: Why is this a business need and not just template cleanup?**
**A:** Hand-built Jinja arrays/objects are hard to maintain, easy to get wrong for
escaping, and force dispatch inputs into strings — agents and APIs then fight the
template layer instead of sending typed JSON.

**Q: Must GitLab bodies be rewritten?**
**A:** GitLab curated write bodies today are string fields only (labels are
comma-separated strings). They must keep working; rewriting them is optional. The helper
must still be available for authors.

**Q: Does GitHub's workflow_dispatch API require string input values?**
**A:** PyPost previously stringified for safety under `to_json_string` limits. This task
intentionally preserves JSON types for inputs; remote acceptance of typed scalars is an
upstream concern documented in the collection notes if needed.
