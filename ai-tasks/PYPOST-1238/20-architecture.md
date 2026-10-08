# PYPOST-1238: Exact flat finder reference recognition

## Research

The current `_refers_to_find_child` helper in
`tests/test_display_role_scan_ownership_repro.py` accepts any bare name containing `child`
case-insensitively. Its fallback also matches the full function name anywhere in the AST
dump, including an unrelated bare name with that substring. PYPOST-1041 TD-4 demonstrates
that a tree-finder-only loop using `child_fn` satisfies the delegation guard incorrectly.

The current ownership suite binds the flat finder to `find_child`. Two predicates share
the recognition helper: delegation coverage and duplicate-display-role coverage. Preserve
their boolean interfaces and their existing traversal behavior.

Python's AST represents bare identifiers as `Name` nodes with an `id` attribute, while
`ast.parse` builds trees and `ast.dump` renders their structure. These standard facilities
support isolated source-string probes without executing the source.
See [Python AST documentation](https://docs.python.org/3/library/ast.html).

## Implementation Plan

1. Step 3 adds self-contained tests in `tests/test_display_role_scan_ownership_repro.py`
   before changing its recognition helper. Parse a source string containing
   `for child_fn in (find_tree,):` with a `_calls_name(child_fn, "display_role_equals")`
   assertion. Assert `_has_find_child_delegation_check` returns `False`; the current helper
   returns `True`, producing the required red result.
2. Add focused parameterized coverage for supported and unsupported first arguments through
   both ownership predicates. The duplicate-display-role probe uses
   `_has_display_role_attr` in a negative assertion. These source snippets are parsed only.
3. Step 4 changes only `_refers_to_find_child` and its description. Every `ast.Name` returns
   exact membership in `{"find_child", "find_child_index_by_display_text"}` immediately.
   All other expression nodes retain the existing full-function-name-in-`ast.dump` fallback.
4. Verify the regression turns green and existing ownership/repro suites remain green using
   `make test` with `PYTEST_ARGS` selecting the two ownership files named above.
   Run the required repository quality gate later in the workflow.

### Regression cases

| First argument | Expected recognition | Purpose |
| --- | --- | --- |
| `find_child` | True | Current ownership suite compatibility |
| `find_child_index_by_display_text` | True | Supported exact full name |
| `tree_defs.get("find_child_index_by_display_text")` | True | Existing lookup fallback |
| `child_fn` in a tree-finder-only loop | False | TD-4 reported false green |
| `CHILD_FN` | False | Reject case-insensitive substring matches |
| `find_tree` | False | Reject unrelated finder |
| `prefix_find_child_index_by_display_text_suffix` | False | Prevent bare-name fallback leak |
| `tree_defs.get("find_tree_index_by_display_text")` | False | Unrelated lookup |

Exercise the table through both predicates. Tests inherit the existing ten-second module
timeout. They require no Qt application, live service, production import, or source mutation.
The existing ownership suite's source-level checks remain the compatibility evidence for
its real bindings. This focused recognition coverage does not expand PYPOST-1236's broader
mutation matrix.

## Architecture

```text
Parsed ownership assertion source
  -> _has_find_child_delegation_check(tree) -> _refers_to_find_child(first_argument)
  -> _has_find_child_forbids_display_role_check(tree) -> same recognition helper
  -> boolean evidence of flat finder coverage
```

### Responsibilities and interfaces

- `_refers_to_find_child(arg: ast.expr) -> bool`: classify a reference according to the two
  supported exact bare names or the preserved non-name expression fallback.
- `_has_find_child_delegation_check(tree: ast.AST) -> bool`: retain existing `_calls_name`
  discovery and `display_role_equals` argument checks; use the shared classifier.
- `_has_find_child_forbids_display_role_check(tree: ast.AST) -> bool`: retain existing
  `_has_display_role_attr` discovery; use the same classifier.
- Focused regression tests: supply ASTs for representative accepted/rejected references and
  assert the ownership predicates' observable decisions.

### Decisions and boundaries

Keep the existing pure-function design and signatures. An early return for every bare name
prevents the lookup fallback from defeating strict membership. No new abstraction or
dependency is needed. No alias resolution is introduced: the guard remains a deliberately
limited source-shape check. The fallback remains broad for non-name expressions because
preserving that compatibility is required; semantic lookup validation is outside this task.

Production modules, Qt interactions, and application behavior remain outside the change.

## Q&A

- Why not only replace the positive substring condition? A rejected bare name could still
  contain the full function name and pass the existing fallback; every bare name must finish
  in the exact-membership branch.
- Why keep the fallback? AC-4 explicitly preserves supported lookup-expression references.
- Why test both consumers? AC-5 requires consistent recognition in both ownership checks.
