# PYPOST-1235: Teach `_module_all_exports` the annotated `__all__` spelling

## Research

- **AST shapes** (Python `ast` docs). `ast.Assign` has `targets: list[expr]` and a
  mandatory `value`. `ast.AnnAssign` has a single `target`, an `annotation`, `value: expr | None`
  (`None` for the bare form `__all__: list[str]`), and `simple` (1 for a plain `Name` target).
  Widening `isinstance(node, ast.Assign)` to `(ast.Assign, ast.AnnAssign)` raises
  `AttributeError` on `node.targets`. The bare form then reaches `isinstance(None, ...)`, which is
  harmless but only by accident. So the reader needs one small target/value normaliser per node
  kind, not a wider `isinstance` (Q4).
- **Current reader** (`tests/test_display_role_scan_ownership.py:64-82`). It scans module-level
  statements only (`ast.iter_child_nodes`). A non-literal `ast.Assign` to `__all__` falls through
  to the next statement, so the first *literal* assignment wins. It returns `set()` both for
  "nothing readable" and for "empty literal". Element filtering keeps string constants only.
- **Single caller**. `test_flat_and_tree_share_display_role_match_helper` (`:551-559`) asserts
  `expected_exports.issubset(tree_exports)` with message
  `pypost.agent.tree_index.__all__ must export [...]; found [...]`.
- **Coupling checked concretely (AC-8):**
  - `_has_all_exports_check` (`tests/test_display_role_scan_ownership_repro.py:161`) needs a
    `Call` to the bare name `_module_all_exports` anywhere in the file, plus a `Set`, `List` or
    `Tuple` literal holding `display_role_equals` and `find_child_index_by_display_text`. The
    `expected_exports` set literal satisfies the second half. Both stay.
  - `_main_test_assertion_message` inspects only `assert <Compare>` whose left side is the local
    `find_tree` or `select_item`. A new `assert tree_exports is not None, ...` has left side
    `tree_exports`, so it is not matched and does not change the "exactly one" count.
  - Repro test 5 runs `__all__ = []`, and `pytest.raises(..., match=r"__all__.*export")` uses
    `re.search`. That case stays on the "missing names" message
    (`...__all__ must export [...]; found []`), so it still matches. Repro test 4 fails earlier, in
    `_assert_flat_*`, so it is unaffected.
  - **Discoverability** (`tests/test_display_role_scan_ownership_discoverability.py`). It cuts
    regions by substring line markers: `find_child` runs from `def _assert_flat_shared_ownership`
    (`:491`) to `def _assert_tree_shared_ownership` (`:511`). `find_tree` runs from `:511` to
    `def test_flat_and_tree_share_display_role_match_helper` (`:522`). `_select_item_view` runs
    from `:522` to the next `^(async )?def ` line, or EOF. Today the main test is the last function
    (EOF at `:588`). The proximity rule (12 nonblank lines) measures the distance from each
    `PYPOST-1239 <label>` comment to its assertion. In the main test the `select_item` assertions
    and their marker sit *below* the `__all__` block. Adding lines in the `__all__` block shifts
    them together, so their distance does not change. The in-suite validator
    (`_target_region`, AST `lineno..end_lineno`) behaves the same way (there the `find_child`
    region ends at `_assert_flat_no_duplicate_ownership`, not at `_assert_tree_shared_ownership`;
    the outcome is the same). **Constraint:** the helper
    stays above `:491`, and no new `def` goes between the three marker functions or inside them.
    New tests go in a separate file (below), so the EOF region is untouched.
- **mypy scope**. `MYPY_PATHS` covers `pypost/core`, `pypost/models` and `pypost/ui`. `tests/`
  is outside it, but the new return type is written to be strict-clean anyway.

## Implementation Plan

### Q1 resolution: how "no readable manifest" is signalled

| Option | Verdict |
| --- | --- |
| A. `_module_all_exports(tree) -> set[str] \| None`: `None` = no literal manifest | **Chosen.** One traversal, one source of truth, same name and call site, and mypy narrows it with `is not None`. |
| B. Keep `set[str]` and add a predicate `_module_has_literal_all(tree)` | Rejected: two traversals must agree on the same spelling rules, which invites drift. |
| C. A richer result (dataclass or enum: `LITERAL`, `BARE`, `COMPUTED`, `ABSENT`) | Rejected: no AC needs to tell the three unreadable spellings apart (Q2). Too much for 2 SP. |
| D. The reader raises `AssertionError` when it finds nothing readable | Rejected: mixes parsing with policy, and the AC-5 message belongs to the ownership test. |

### Helper contract (`tests/test_display_role_scan_ownership.py`, same name and location)

```text
_module_all_exports(tree: ast.AST) -> set[str] | None
```

- It scans `ast.iter_child_nodes(tree)` in source order (module level only, as today).
- For each statement it builds the pair `(targets, value)`:
  - `ast.Assign` gives `(node.targets, node.value)`.
  - `ast.AnnAssign` gives `([node.target], node.value)`, and `value` may be `None`.
  - Any other statement is skipped.
- A statement counts only if one of its targets is `ast.Name(id="__all__")`.
- If that statement's `value` is an `ast.List` or `ast.Tuple` literal, the reader returns
  `{elt.value for str constants}`. Elements that are not strings are dropped, as today. An empty
  literal returns `set()`.
- Otherwise the reader skips the statement. This covers a bare annotation (`value is None`) and a
  computed value. Scanning continues, so `__all__: list[str]` followed by `__all__ = [...]`
  reads the later literal (Q3, already true today and preserved). It also keeps today's
  "first literal
  wins" behaviour.
- If the scan ends without a literal, the reader returns `None`. Absent, bare-only and
  computed-only manifests all land here.
- It never raises for any parseable module (AC-3, AC-4).
- The docstring is updated to state the `None` versus `set()` meaning.

Augmented assignment (`+=`), `.extend()`, conditional manifests and star-import manifests are
still ignored, so they read as `None` when nothing else is present (out of scope, TD-1).

### Caller: two single-line diagnostics

`expected_exports` moves above the reader call, and stays the same set literal. Both messages
keep the owner prefix `pypost.agent.tree_index.__all__ must export [...]`. That keeps
NFR-3 and repro test 5's `__all__.*export` true for both failure kinds.

```text
assert tree_exports is not None, (
    f"pypost.agent.tree_index.__all__ must export {sorted(expected_exports)}; "
    "no statically readable literal __all__ found "
    "(absent, bare annotation, or computed value)"
)
assert expected_exports.issubset(tree_exports), (
    f"pypost.agent.tree_index.__all__ must export {sorted(expected_exports)}; "
    f"found {sorted(tree_exports)}"
)
```

- The unreadable message never says `found []`, so AC-5 holds.
- An empty or short literal keeps the current message, so AC-5 and AC-8 (repro test 5) hold.

Hoisting the message text into module constants is optional. If the text is hoisted, the
`expected_exports` set literal must stay a literal (`_has_all_exports_check`).

### Failing repro (Step 3): written before the helper changes

**New file** `tests/test_display_role_scan_ownership_all_exports.py`, with
`pytestmark = pytest.mark.timeout(10)`. A separate file keeps the ownership file's
discoverability regions and EOF boundary untouched. It also leaves every PYPOST-1041 and
PYPOST-1239 guard unedited.

The file reuses the existing seam and template by importing only underscore names, so pytest does
not re-collect the repro tests:
`from tests.test_display_role_scan_ownership_repro import _COMPLIANT_FIND_CHILD,
_MUTANT_TREE_INDEX_TEMPLATE, _patch_tree_index_source`.
It also does `import tests.test_display_role_scan_ownership as ownership_suite` for the reader
and the main test.

**E2E repro** (AC-7, AC-2..AC-5). Each test calls
`ownership_suite.test_flat_and_tree_share_display_role_match_helper()` against
`_MUTANT_TREE_INDEX_TEMPLATE.format(exports=..., find_child=_COMPLIANT_FIND_CHILD)`.

| Test | `exports` spelling | Asserted outcome | Today |
| --- | --- | --- | --- |
| annotated list passes | `__all__: list[str] = [3 names]` | returns normally | **red**: `AssertionError ... found []` |
| annotated tuple passes | `__all__: tuple[str, ...] = (3 names)` | returns normally | **red**: same |
| annotated literal missing a name | `__all__: list[str] = [2 names]` | `AssertionError`, match `found \['display_role_equals', 'find_child_index_by_display_text'\]` | **red**: regex mismatch (`found []`) |
| bare annotation (parametrized with computed `__all__ = list(_PUBLIC)` and absent) | as named | `AssertionError`, match `__all__.*no statically readable literal __all__`, and `"found []" not in str(exc)` | **red**: regex mismatch, message is `found []` |
| empty literal regression guard | `__all__ = []` | `AssertionError`, match `__all__ must export .*; found \[\]` | green (pins AC-5 second half) |

Today each red test fails because the reader cannot read the annotated form, or because the
message conflates unreadable with empty. Neither failure is an import or seam error. Step 3
checks this by reading the failure text.

**Unit tests of the reader** (AC-6). They are parametrized over `ast.parse(snippet)` and call
`ownership_suite._module_all_exports`:

| Case | Snippet | Expected | Today |
| --- | --- | --- | --- |
| plain list | `__all__ = ["a", "b"]` | `{"a", "b"}` | green |
| plain tuple | `__all__ = ("a", "b")` | `{"a", "b"}` | green |
| annotated list | `__all__: list[str] = ["a", "b"]` | `{"a", "b"}` | red (`set()`) |
| annotated tuple | `__all__: tuple[str, ...] = ("a",)` | `{"a"}` | red |
| computed | `__all__ = list(_PUBLIC)` | `None` | red (`set()`) |
| bare annotation | `__all__: list[str]` | `None`, no exception | red (`set()`) |
| empty literal | `__all__ = []` | `set()` | green |
| absent | `x = 1` | `None` | red (`set()`) |
| bare then literal (Q3) | `__all__: list[str]\n__all__ = ["a"]` | `{"a"}` | green (today's reader skips the `AnnAssign` and reads the next `Assign`) |

The plain, empty and bare-then-literal rows are regression guards. They pass today, and the
reviewer should not count them as repro evidence.

**Sequencing:** write the file, run `make test` and confirm the red set is exactly the rows marked
red above, for the stated reasons (Step 3). Then change the helper and the caller (Step 4), and run
`make test` and `make check` until everything is green, with the four PYPOST-1041/1239 files
unedited.

### Step 4 and Step 8 scope

- Code: only the `_module_all_exports` body and docstring, and the `__all__` block of the main
  test (`expected_exports` hoisted, plus one new `assert ... is not None`). Nothing changes under
  `pypost/` (AC-9).
- Docs: `doc/dev/ui_actions.md` `:252`, where the Enforcement paragraph describes the reader
  ("literal or annotated-literal `__all__`; `None` when unreadable"), and `:401-404`, the
  troubleshooting entry. That entry gets re-keyed to the two messages: `found [...]` means names are
  really missing, and `no statically readable literal __all__` means absent, bare or computed.

## Architecture

```text
tree_index.py source --(_parse / _patch_tree_index_source seam)--> ast.Module
        |
        v
_module_all_exports(tree) -> set[str] | None          [reader: syntax only]
        |
        v
test_flat_and_tree_share_display_role_match_helper    [policy + diagnostics]
   None        -> "…__all__ must export [...]; no statically readable literal __all__ found (…)"
   set lacks   -> "…__all__ must export [...]; found [...]"
        ^
        |  by name / AST shape, unedited
repro guards (_has_all_exports_check, mutant tests 4-5), discoverability regions
```

- **Reader** (`_module_all_exports`): a pure, static AST query that turns module-level spellings
  into a three-way result: names, empty set, or `None`. It holds no policy.
- **Ownership test**: owns the policy (the required names) and the single-line diagnostics.
- **Seam** (`_patch_tree_index_source`): the existing substitution of the `tree_index` AST, reused
  unchanged by the new tests.
- **Pattern**: an optional return used as an explicit "not found" sentinel. This is idiomatic
  Python, and it is the smallest change that keeps the helper's name, arity and call shape that
  the guards depend on.

Interfaces that change: only the reader's return type, which widens to `set[str] | None`. It has
one in-repo caller (`grep` over `tests/` and `doc/`), which is updated in the same change.

## Q&A

- **Q1 (from Step 1):** Use `set[str] | None`. `None` means no statically readable literal
  manifest. `set()` means a literal empty manifest. See the table above.
- **Q3:** Already supported today (the current reader skips non-`Assign` statements); the new
  reader keeps this by skipping a bare annotation and continuing the scan. Guarded by the
  green-today "bare then literal" unit row.
- **Q5:** Why must the unreadable message still contain `__all__ must export`?
  **A:** It keeps NFR-3 (owner named), and any future mutant test that uses the
  `__all__.*export` regex matches both failure kinds. AC-5 forbids only `found []` on that path.
- **Q6:** Why put the new tests in a new file and not the ownership file?
  **A:** The discoverability region for `_select_item_view` ends at the next top-level `def`
  after the main test, or EOF. A separate file leaves that region and the PYPOST-1041 guards
  untouched.
- **Risk:** Importing private names from `tests/test_display_role_scan_ownership_repro.py`
  couples the new file to that file. That is acceptable because those files are frozen by AC-8.
  If the reviewer objects, the fallback is a local copy of the 8-line seam.
