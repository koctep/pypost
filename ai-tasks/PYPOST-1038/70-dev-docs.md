# PYPOST-1038: Developer Documentation

## Scope

PYPOST-1038 publishes a narrow, fixture-specific MCP input contract for Jira
board and sprint path identifiers. It does not add a Jira tool, alter a tool or
argument name, or relax unrelated MCP parameter schemas. The documentation
explains the `integer_or_string` schema type, strict `to_int` rendering, the
complete six-request mapping, and the offline regression boundary.

## Documentation updates

| File | Update |
| --- | --- |
| `doc/dev/mcp_integration.md` | Defines `integer_or_string`, lists all six Jira request/argument/path mappings, describes strict template conversion, and gives the loopback-focused test command. |
| `doc/dev/template_expression_functions.md` | Updates `to_int` to document true-`int` pass-through as well as strict decimal strings; records rejected booleans, floats, and invalid strings. |
| `doc/dev/jira_mcp_project_default.md` | Records the client-facing board/sprint dual-form contract, the six affected request IDs, and identifier troubleshooting without changing project-default security guidance. |
| `doc/dev/testing.md` | Adds the six-path valid/invalid real-MCP loopback coverage to the integration-test boundary and focused commands. |
| `doc/dev/README.md` | Makes the PYPOST-1038 MCP contract and expanded conversion page discoverable. |
| `examples/README.md` | Gives collection importers the six tool/argument mappings, dual valid forms, and invalid-input boundary. |

## Contract summary

The following request arguments alone use `integer_or_string`:

| Request id | Argument | HTTP path destination |
| --- | --- | --- |
| `jira-list-board-sprints` | `board_id` | board sprint list |
| `jira-get-sprint` | `sprint_id` | sprint |
| `jira-update-sprint` | `sprint_id` | sprint |
| `jira-delete-sprint` | `sprint_id` | sprint |
| `jira-add-issues-to-sprint` | `sprint_id` | sprint issues |
| `jira-get-sprint-issues` | `sprint_id` | sprint issues |

The schema permits JSON `42` and decimal JSON string `"42"`. Each matching
path template calls `to_int(mcp.request.<argument>)`, so accepted forms render
to the same decimal path component. Invalid strings, booleans, and floats fail
before an outbound HTTP call. Existing scalar MCP parameter schemas and all
other Jira arguments retain their established contracts.

## Validation

- [x] Documentation names the exact six fixture mappings asserted by
  `tests/test_example_fixtures.py`.
- [x] Documentation matches `to_int` behavior: true `int` and ASCII decimal
  strings accepted; bool, float, and malformed/non-decimal values rejected.
- [x] Documentation describes the isolated Streamable HTTP MCP plus loopback
  tests, not a live Jira dependency.
- [x] `git diff --check` reports no whitespace errors.
- [x] Independent documentation review passed after the importer-guide
  correction.

## Approval basis

The sprint runner's autonomous workflow authorizes continuation without a
separate user gate. The user's standing instruction requires an independent
subagent review before this Step 8 artifact and the roadmap are finalized. An
initial review correctly blocked completion because `examples/README.md` lacked
the importer-facing contract. That guide was updated, and a fresh independent
review passed with no remaining findings.

## Worklog

```text
role: execution
step: 8
step_name: Dev Docs
actions: documented the integer_or_string schema, true-int and decimal-string
  to_int contract, six Jira fixture mappings, offline test boundary, developer
  index, and importer-facing guidance; resolved the review finding and updated
  the roadmap artifact
time_spent: 20m
tokens_used: 7500

role: independent_docs_reviewer
step: 8
step_name: Dev Docs Review
verdict: PASS — no findings after importer-guide correction
actions: checked requirements and architecture against all developer/importer
  docs, the six fixture mappings, schema/conversion behavior, test node ids,
  offline boundary, and tool-name versus request-id terminology
time_spent: 8m
tokens_used: 2250
```
