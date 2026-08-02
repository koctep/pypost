# PYPOST-1032: Developer Documentation

## Scope

This fixture-only task has no PyPost runtime API, external Atlassian MCP
configuration, or new product-documentation surface to describe. Developer
documentation records how the importable Jira examples supply a soft project
default and how to maintain its fixture contract.

## Coverage

| File | Developer-facing coverage |
| --- | --- |
| `doc/dev/jira_mcp_project_default.md` | Environment variable handling, board-list template binding, payload-guidance boundary, security limitation, and troubleshooting. |
| `doc/dev/README.md` | Makes the PYPOST-1032 reference discoverable from the MCP documentation index. |
| `tests/test_example_fixtures.py` | Native-import contract for the visible placeholder, hidden-secret boundary, supported board filter, soft-guidance wording, and board/sprint scope limits. |

The existing `examples/README.md` remains the end-user import reference. No
additional product documentation change is needed for this close-out step.

## Validation

- [x] Developer reference and its `doc/dev/README.md` index entry identify the
      shipped environment, collection, and test contract.
- [x] Focused fixture contract passed: `make test` with
      `PYTEST_ARGS="tests/test_example_fixtures.py -q"` (5 passed).
- [x] `make lint` passed for the implementation and test changes.
- [x] `git diff --check` passed with no whitespace errors.

## Worklog

tokens_used: 2600
role: fix
step: 8
step_name: Dev Docs
