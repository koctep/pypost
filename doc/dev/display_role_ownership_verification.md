# DisplayRole Ownership Verification

## Overview

The display-value lookup helpers use one ownership rule for matching an item's
`DisplayRole` value. `display_role_equals` in `pypost.agent.tree_index` owns the
comparison. Both `find_child_index_by_display_text` (flat lookup) and
`find_tree_index_by_display_text` (depth-first tree lookup) delegate to it.

The ownership tests protect this source-structure contract. They are regression
coverage for maintainers: a lookup can continue returning the expected item
even after its comparison ownership has been weakened, so runtime examples alone
are not sufficient.

## Architecture

- `pypost.agent.tree_index` defines the shared matcher, flat lookup, tree lookup,
  and their explicit `__all__` exports.
- `pypost.agent.ui_actions` delegates text selection to the flat lookup and does
  not perform a second `DisplayRole` comparison.
- `tests/test_display_role_scan_ownership.py` parses the relevant source files
  and exposes three independent assertion helpers:
  `_assert_flat_shared_ownership`, `_assert_flat_no_duplicate_ownership`, and
  `_assert_tree_shared_ownership`.
- `tests/test_display_role_scan_ownership_aggregate_repro.py` supplies small
  synthetic source mutants through the ownership suite's `_parse(Path)` seam.
  It invokes `_validate_display_role_ownership` once across all fixtures and
  scopes so every violation is reported in one aggregate outcome.

The checks intentionally use Python AST inspection. They are hermetic, do not
import or execute the Qt lookup implementation, and do not require a display
server.

The ownership suite also provides `_validate_display_role_ownership(paths)` for
the aggregate guard. It parses each bounded fixture path in the supplied order,
collects every applicable violation, and raises one `AssertionError` when any
are found. Each diagnostic is prefixed with its fixture context, so a single
failure reports all ownership problems while preserving deterministic ordering.
A compliant collection of paths completes without an exception.

## Ownership contract and mutant matrix

Each acceptance condition has one isolated mutant and one condition-specific
diagnostic:

- **AC-1: flat shared ownership**
  - Mutant: The flat finder inlines the `DisplayRole` comparison and bypasses
    `display_role_equals`.
  - Expected diagnostic:
    <code>find_child_index_by_display_text must call display_role_equals instead of inlining
    DisplayRole comparison</code>
- **AC-2: flat no duplicate ownership**
  - Mutant: The flat finder delegates, then performs a second inline
    `DisplayRole` comparison.
  - Expected diagnostic:
    <code>find_child_index_by_display_text must not compare ItemDataRole.DisplayRole inline;
    use display_role_equals</code>
- **AC-4: tree shared ownership**
  - Mutant: The tree finder inlines the comparison while retaining its other
    tree checks.
  - Expected diagnostic:
    <code>find_tree_index_by_display_text must call display_role_equals instead of inlining
    DisplayRole comparison</code>

The compliant control source must pass all three helpers. The flat and tree
mutants must remain independent: do not combine violations or reuse a flat
diagnostic for the tree condition.

The aggregate repro covers a flat violation, a tree duplicate comparison, and
a tree delegation violation together. Its expected output demonstrates the
single-outcome contract and the stable context labels (`flat`,
`tree-duplicate`, and `tree-ownership`).

## Usage

Run the focused ownership regression coverage through the repository Makefile:

```sh
make test PYTEST_ARGS='tests/test_display_role_scan_ownership*.py'
```

The module-level timeout is 10 seconds. The full aggregate test also preserves
the existing export and UI-action delegation checks.

## Configuration

No configuration, environment variables, services, or Qt display setup are
required. The tests read repository source files as UTF-8 and use the standard
Python `ast` module.

## Troubleshooting

### An AC-1 failure reports the flat delegation diagnostic

Inspect `find_child_index_by_display_text` and ensure its display match calls
`display_role_equals`. The helper must not replace that call with an inline
`ItemDataRole.DisplayRole` comparison.

### An AC-2 failure reports the duplicate-ownership diagnostic

Remove the second local display comparison from the flat lookup. Display-value
ownership belongs only to `display_role_equals`.

### An AC-4 failure reports the tree delegation diagnostic

Inspect `find_tree_index_by_display_text`, including its recursive walk. Every
tree match must delegate to `display_role_equals`; retain the existing depth-first
traversal and validity checks.

### The synthetic repro cannot find an assertion helper

Keep the helper names and `_parse(Path)` seam stable. The repro monkeypatches
that seam only for the `tree_index.py` path and delegates all other paths to the
real parser.

### Several ownership violations appear in one failure

This is expected for the aggregate guard. Read the context prefix on each line
to identify the fixture and fix every reported ownership violation before
rerunning the focused command. The validator deliberately does not stop at the
first violation.
