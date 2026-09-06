# Dual-Mode (GUI + MCP) Example Requests (PYPOST-1283)

## Overview

A bundled example request can be usable two ways at once:

- **GUI**: a human edits the request's Body JSON editor directly and clicks Send.
- **MCP**: an agent calls the tool with structured arguments (`mcp.request.*`),
  and the same Body template renders the request from those arguments instead.

`examples/collections/jira_mcp.json`'s `jira-create-issue` request is the first
(and, as of PYPOST-1283, only) request in the bundled examples built this way.
It is the reference pattern for any future dual-mode example request. This doc
exists so a future author of a *second* dual-mode request does not have to
reverse-engineer the pattern (or its one sharp edge) from the JSON alone.

## The pattern

The request `body` is a single Jinja template with two branches, picked with
`{% if %}` guards at render time:

1. **MCP structured-fields branch** (default): builds the JSON body field by
   field from `mcp.request.issue_type` / `mcp.request.summary` /
   `mcp.request.description`, each falling back to a literal default (e.g.
   `"Task"`, `"New issue created from PyPost"`, `""`) when the agent didn't
   supply it. This is also what a **GUI** user gets, since `mcp` is undefined
   during a manual GUI send — every `has_x` guard evaluates false and every
   `*_value` falls back to its literal default, which the GUI user can then
   edit directly in the Body editor.
2. **MCP verbatim-payload fallback branch**: if the caller supplies
   `mcp.request.issue_payload` (a full serialized Jira JSON body), it is
   substituted verbatim, bypassing the structured fields entirely. Kept for
   callers that need full control of the payload shape.

Simplified skeleton (see `examples/collections/jira_mcp.json` for the exact,
single-line JSON-escaped form):

```jinja
{% set has_payload = mcp is defined and mcp.request is defined and mcp.request.issue_payload is defined and mcp.request.issue_payload %}
{% set has_issue_type = mcp is defined and mcp.request is defined and mcp.request.issue_type is defined %}
{% set has_summary = mcp is defined and mcp.request is defined and mcp.request.summary is defined %}
{% set has_description = mcp is defined and mcp.request is defined and mcp.request.description is defined %}
{% set issue_type_value = mcp.request.issue_type if has_issue_type else "Task" %}
{% set summary_value = mcp.request.summary if has_summary else "New issue created from PyPost" %}
{% set description_value = mcp.request.description if has_description else "" %}
{% if has_payload %}
{{ mcp.request.issue_payload }}
{% else %}
{"fields": {"project": {"key": {{ to_json_string(jira_project_key) }}}, "issuetype": {"name": {{ to_json_string(issue_type_value) }}}, "summary": {{ to_json_string(summary_value) }}, "description": {{ to_adf(description_value) }}}}
{% endif %}
```

Why the guards look like this rather than idiomatic Jinja
(`{{ mcp.request.issue_type | default("Task") }}`): `FunctionExpressionResolver`
(pre-existing, not part of this task) only allows a bare safe variable path or
a single-argument allow-listed-function call inside `{{ ... }}` — no filters,
ternaries, or method calls (see
[Template Expression Functions](template_expression_functions.md)). Jinja's
default `Undefined` also raises immediately on `mcp.request.x` attribute
access when `mcp` itself is absent, rather than silently stringifying to
`""`. The `{% set has_x = ... is defined %}` / `{% if has_x %}` guard style
works around both constraints.

## Constraint: keep every `{% set %}` unconditional

**This is the one rule a future dual-mode template must not break.**

`McpSecretsPolicy.extract_environment_variable_names`
(`pypost/core/mcp_secrets_policy.py`) discovers which top-level names in a
request template are *environment variables* (as opposed to `mcp.request.*`
agent inputs) by parsing the template to a Jinja AST and calling
`jinja2.meta.find_undeclared_variables(ast)`. That Jinja helper returns every
name the template *reads* without first defining it in a `{% set %}` — which
is exactly the heuristic PyPost relies on to decide "this name must come from
the environment, so factor it into hidden-key/override visibility."

`find_undeclared_variables` only excludes a name if the `{% set %}` that
defines it is **unconditional** — i.e. not nested inside an `{% if %}` block.
If a `{% set %}` is moved inside an `{% if %}`, Jinja considers the name
*possibly* undeclared (since the `{% if %}` might not execute) and reports it
as undeclared again — at which point `extract_environment_variable_names`
mistakes a purely local template variable (like `has_issue_type` or
`issue_type_value` above) for a real environment variable. Concretely, that
would make the local name eligible for hidden-key filtering and MCP-override
schema advertisement, neither of which is meaningful for it, and would
silently corrupt the set of names PyPost believes are environment-sourced —
a security-relevant path, since that same discovery feeds hidden-key
visibility filtering (see [MCP Secrets Policy](mcp_secrets_policy.md)).

Rule for any future dual-mode request body:

- Every `{% set %}` statement must sit at the top level of the template
  (never inside `{% if %}` / `{% for %}` / etc.), even when the value being
  assigned is itself conditional (`{% set x = a if cond else b %}` is fine —
  the *assignment* is unconditional; only the *value expression* is
  conditional).
- Only the branch selection itself (`{% if has_payload %}...{% else %}...{%
  endif %}`) may be conditional.
- There is no test today that fails loudly if this rule is broken — it
  degrades silently into wrong hidden/override visibility for the local
  names, not a template render error. Verify manually against
  `McpSecretsPolicy.extract_environment_variable_names` (or the existing
  `tests/test_example_fixtures.py` / `tests/test_mcp_collection_e2e.py`
  suites, which exercise the real bundled template) when adding or modifying
  a dual-mode request body.

## `to_adf(text)` and `to_json_string(text)`

Both are Jinja globals registered in `pypost/core/function_registry.py`
(`pypost/core/adf.py`, `pypost/core/json_string.py`). Each returns an
already-quoted-or-structured JSON fragment, so both are called **unquoted**
inside the JSON template — e.g. `"description": {{ to_adf(description_value) }}`,
never `"description": "{{ to_adf(description_value) }}"`.

### `to_adf(text) -> str`

Converts plain text into a JSON-serialized Atlassian Document Format (ADF) v1
document, e.g. `{"version": 1, "type": "doc", "content": [...]}`. Jira Cloud's
REST API v3 requires rich-text fields (such as an issue description) to be
submitted as ADF rather than a plain string. Blank-line-separated (`"\n\n"`)
blocks of the input become separate paragraphs; a single line becomes one
paragraph; an empty string produces a valid document with one empty
paragraph. Use it whenever a template field must be a real ADF document, most
commonly `description`-shaped Jira fields.

### `to_json_string(text) -> str`

Returns `json.dumps(str(text))` — a JSON string literal, quotes included, with
every character JSON requires escaped (double quotes, backslashes, control
characters). Use it for **any** other plain string value being interpolated
into a JSON string literal position inside a template, e.g.
`"summary": {{ to_json_string(summary_value) }}`.

### Why raw `{{ variable }}` into a JSON string literal is unsafe

Before PYPOST-1283 Iteration 7, `jira-create-issue`'s structured fields were
interpolated raw: `"summary": "{{ summary_value }}"`. `{{ }}` substitution is
a plain string paste with no JSON-awareness. A value containing a double
quote (e.g. `Test "quoted" summary`) produced invalid JSON; worse, a
deliberately crafted value could break out of the string literal entirely and
inject additional JSON fields into the request body (a JSON-injection bug,
not just a malformed-request bug). `to_json_string`/`to_adf` close this by
routing the value through `json.dumps` before it reaches the template output,
so the result is always a syntactically valid, correctly escaped JSON
fragment regardless of the input's content.

**Rule for any JSON-bodied template**: never write `"field": "{{ value }}"`.
Either write `"field": {{ to_json_string(value) }}` (for a plain string
field) or `"field": {{ to_adf(value) }}` (for an ADF-shaped rich-text field),
and leave the surrounding quotes out of the template — the function supplies
them.

## See also

- [MCP Secrets Policy](mcp_secrets_policy.md) — hidden-key and
  `mcp_overridable_keys` visibility rules that
  `extract_environment_variable_names` feeds into.
- [Template Expression Functions](template_expression_functions.md) — the
  `{{ ... }}` expression grammar (`FunctionExpressionResolver`) and the full
  allow-listed function catalog, including `to_adf` and `to_json_string`.
- [Jira MCP Example Project Default](jira_mcp_project_default.md) — the
  `jira_project_key` convention this same collection uses, and how it
  interacts with per-key MCP override.
