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

## Intentional repeated assertions

The repeated assertions are intentional and must remain recognizable as two
parts of one ownership contract:

- `find_child` is checked by both `_assert_flat_shared_ownership` and
  `_assert_flat_no_duplicate_ownership`. The first assertion proves delegation
  to `display_role_equals`; the second proves that the flat lookup has no inline
  `ItemDataRole.DisplayRole` ownership. The checks intentionally remain in two
  helpers, even though the pair spans their boundary.
- `find_tree` is checked in `_assert_tree_shared_ownership` for both delegation
  to `display_role_equals` and the absence of inline `DisplayRole` ownership.
- `_select_item_view` is checked in
  `test_flat_and_tree_share_display_role_match_helper`. Its text branch must
  call `find_child_index_by_display_text`, and the view helper must not perform
  its own inline `DisplayRole` comparison.

Do not combine these assertions into a loop or a single generalized check
without re-evaluating the contract. The repetition preserves independent
regression signals for delegation and ownership. Simplifying it can make a
weakened check pass for the wrong reason, especially when runtime lookup
behavior still appears correct.

Each group has a local marker such as `# PYPOST-1239 find_child:` in the test
source. The marker's comment explains the delegation, the lack of inline
ownership, and the risk to ownership regression protection. Keep the rationale
where the assertions are maintained; a remote task artifact or this guide does
not replace the local explanation.

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

## Local discoverability contract

The PYPOST-1239 validator recognizes only lexical Python comments. A marker must
use the form `PYPOST-1239 <target>`, where `<target>` is `find_child`,
`find_tree`, or `_select_item_view`; marker text in a string literal or
docstring does not count.

The validator checks each required assertion within its target region:

- `find_child`: the inclusive span from `_assert_flat_shared_ownership`
  through `_assert_flat_no_duplicate_ownership`, including the boundary between
  those two helpers;
- `find_tree`: the `_assert_tree_shared_ownership` helper; and
- `_select_item_view`: the assertion cluster in
  `test_flat_and_tree_share_display_role_match_helper`.

Both assertions in a group must have a matching target marker within 12
nonblank source lines. The marker and its contiguous comment block must stay in
the same bounded region. A marker beside only one assertion, a marker for
another target, or a matching marker outside the local boundary is not enough.
The rationale must explicitly describe intentional repetition and cover the
target's delegation, no inline `DisplayRole` ownership, and regression risk.

## Validator API and results

The test-side API accepts the complete ownership-test source as text:

```text
validate_display_role_discoverability(source_text: str)
    -> DiscoverabilityValidationResult
```

It parses the supplied text and performs no imports, execution, file reads, or
source mutation. `DiscoverabilityValidationResult` contains `valid`, the fixed
ordered `checked_targets` tuple (`find_child`, `find_tree`, and
`_select_item_view`), and an ordered tuple of `diagnostics`. Each
`DiscoverabilityDiagnostic` has `target`, `code`, and `message`.

Diagnostics are emitted in target order, with at most one record per invalid
target. Messages have the stable prefix
`PYPOST-1239/<target>/<code>:` and do not include paths or line numbers. The
supported codes are:

| Code | Meaning |
| --- | --- |
| `MISSING_ASSERTION_PAIR` | One or both required assertions are absent. |
| `MISSING_EXPLANATION` | The pair exists but has no local rationale. |
| `MISSING_INTENTIONALITY` | The rationale does not state that repetition is intentional. |
| `INCOMPLETE_RATIONALE` | The rationale omits delegation, no inline ownership, or regression risk. |
| `WRONG_TARGET_EXPLANATION` | A nearby marker names a different target. |
| `DETACHED_EXPLANATION` | The correct marker exists, but not within the target's local boundary. |
| `INVALID_SOURCE` | The supplied source cannot be parsed as Python; target is `module`. |

The validator returns violations as data rather than relying on incidental
exceptions, keeping focused mutation tests deterministic and actionable.

## Ownership contract and mutant matrix

The following ownership checks and mutants pre-date PYPOST-1239. They are
legacy source-structure regression checks retained to protect the existing
DisplayRole ownership contract; they are not PYPOST-1239 acceptance criteria.
Each check has one isolated mutant and one condition-specific diagnostic:

- **Flat shared-ownership check (legacy)**
  - Mutant: The flat finder inlines the `DisplayRole` comparison and bypasses
    `display_role_equals`.
  - Expected diagnostic:
    <code>find_child_index_by_display_text must call display_role_equals instead of inlining
    DisplayRole comparison</code>
- **Flat no-duplicate-ownership check (legacy)**
  - Mutant: The flat finder delegates, then performs a second inline
    `DisplayRole` comparison.
  - Expected diagnostic:
    <code>find_child_index_by_display_text must not compare ItemDataRole.DisplayRole inline;
    use display_role_equals</code>
- **Tree shared-ownership check (legacy)**
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

PYPOST-1239 acceptance coverage is separate from these legacy ownership
mutants. AC-1 and AC-2 require locally discoverable, actionable explanations
for the three repeated assertion groups; AC-3 requires this developer guide;
AC-4 and AC-5 cover missing or detached explanations; AC-6 accepts a compliant
explanation; and AC-7 and AC-8 preserve existing behavior and the focused
scope. The discoverability validator and its focused tests cover those
criteria; they do not redefine or rename the legacy ownership checks above.

## Usage

Run the focused ownership regression coverage through the repository Makefile:

```sh
make test PYTEST_ARGS='tests/test_display_role_scan_ownership.py tests/test_display_role_scan_ownership_discoverability.py -q'
```

The two modules have explicit 10-second pytest timeouts. The focused run covers
the real source, compliant validation, missing/detached/wrong-target rationale,
missing intentionality, incomplete rationale, deterministic diagnostic order,
and protection against marker text in strings. It also preserves the existing
export and `_select_item_view` delegation checks.

## Configuration

No configuration, environment variables, services, or Qt display setup are
required. The tests read repository source files as UTF-8 and use the standard
Python `ast` module.

PYPOST-1239 made no production logging, metrics, or runtime observability
changes because it is test/documentation-only. The validator's stable
diagnostics and focused test output are test-side verification signals, not
production observability.

## Troubleshooting

### `MISSING_EXPLANATION`

Confirm that both assertions for the target still exist and that a lexical
comment marker names that target. Put the marker and its rationale within 12
nonblank source lines of each assertion and inside the target region. For
`find_child`, remember that the region intentionally spans both flat assertion
helpers.

### `DETACHED_EXPLANATION`

The marker text exists, but it is outside the target's bounded region or beyond
the 12-line nonblank proximity limit. Move the complete contiguous rationale
comment next to the matching assertion group. A developer-guide paragraph or a
remote summary cannot satisfy the local contract.

### `WRONG_TARGET_EXPLANATION`

Inspect the marker label immediately near the failing assertion. Replace a
copied or incorrect target name with the exact target: `find_child`,
`find_tree`, or `_select_item_view`. Do not reuse one target's rationale as a
generic marker for another group.

### `INCOMPLETE_RATIONALE`

Keep the target's named delegated lookup, the statement that it has no inline
`DisplayRole` ownership, and the regression-risk explanation in the contiguous
comment block. The warning should make clear that combining or simplifying the
repeated assertions can weaken ownership regression protection.

### `MISSING_INTENTIONALITY`

State explicitly that the assertions are intentionally repeated (or that the
repetition is intentional). Merely describing two assertions as duplicated is
not sufficient.

### `MISSING_ASSERTION_PAIR` or `INVALID_SOURCE`

Check that the validator input is the complete, parseable source of
`tests/test_display_role_scan_ownership.py`, and that each required `_calls_name`
and `_has_display_role_attr` assertion still matches the expected target. These
diagnostics indicate a source-shape problem, not a missing prose-only note.

### A flat shared-ownership check failure reports the delegation diagnostic

Inspect `find_child_index_by_display_text` and ensure its display match calls
`display_role_equals`. The helper must not replace that call with an inline
`ItemDataRole.DisplayRole` comparison.

### A flat no-duplicate-ownership check failure reports the duplicate diagnostic

Remove the second local display comparison from the flat lookup. Display-value
ownership belongs only to `display_role_equals`.

### A tree shared-ownership check failure reports the delegation diagnostic

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
