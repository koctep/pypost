# PYPOST-1003: Fix import rename summary undercount for duplicate names

## Research

- **Root cause (confirmed by reading both modules directly, not just the
  tech-debt note):**
  - `pypost/core/collection_import.py`:
    - `CollectionImportPlanResult.renamed: dict[str, str]` (line 64).
    - `plan_collection_import`'s local `renamed: dict[str, str] = {}` (line
      231) is written only inside the nested `keep_both` closure via
      `renamed[name] = new_name` (line 242), where `name` is always the
      *original* incoming name, never the freshly generated one. `keep_both`
      is invoked from two paths that both key on the same original `name`:
      the in-file duplicate branch (line 248, for every incoming record whose
      name was already seen) and the explicit `KEEP_BOTH` decision branch
      (line 277). For three incoming records sharing name `"API"`, the first
      is added normally (`added`), and the second and third both hit
      `keep_both(source, "API")` — the second call's
      `renamed["API"] = "Copy of API"` is silently overwritten by the third
      call's `renamed["API"] = "Copy of API (2)"`, leaving one dict entry
      where two rename pairs actually occurred.
    - `format_collection_import_result` reports `len(result.renamed)` (line
      297, used for the `SUMMARY_COLLECTIONS_RENAMED` count) and iterates
      `result.renamed.items()` (line 303) to print the `"original" ->
      "new_name"` lines. Both read the same under-populated dict, so both the
      count and the list are wrong together — this is a single-cause defect,
      not two independent ones.
  - `pypost/core/environment_import.py`: structurally identical bug.
    - `ImportPlanResult.renamed: dict[str, str]` (line 46).
    - `plan_import` writes `renamed[name] = new_name` at two call sites: the
      in-file duplicate branch (line 141) and the `KEEP_BOTH` decision branch
      (line 167) — both keyed on the original `name`, so the same
      last-write-wins collapse happens for 3+ duplicates.
    - `format_import_result` reads `len(result.renamed)` (line 185) and
      `result.renamed.items()` (line 190), same coupled count+list defect.
  - Both `plan_collection_import` and `plan_import` already produce the
    *correct* set of entries in their primary output lists (`collections` /
    `environments`) — every duplicate is renamed and appended with a distinct
    generated name via `generate_import_copy_name`. The defect is confined to
    the separate `renamed` summary accumulator; nothing about conflict
    resolution, id reservation, or persistence changes.

- **Downstream readers audited directly (not just per the task's claim):**
  - `pypost/ui/presenters/collection_import_actions.py`:
    - Line 93: `len(result.renamed)` — logging `renamed_count`.
    - Line 97: `bool(result.added or result.updated or result.renamed)` —
      truthiness only, for the `success` flag.
    - No `.items()`, `.keys()`, `.values()`, `[key]` lookup, or `in` key
      membership check anywhere in the file for `result.renamed`. A
      `list[tuple[str, str]]` is a drop-in: `len()` and truthiness (empty
      list is falsy, non-empty is truthy, same as a dict) behave identically.
  - `pypost/ui/widgets/environments/environment_list_widget.py`:
    - Line 334: `len(result.renamed)` — same logging pattern.
    - Line 338: `bool(result.added or result.updated or result.renamed)` —
      same truthiness-only usage.
    - Same conclusion: no change needed at either call site.
  - No other production module references `.renamed` on either result type
    (confirmed by grepping `pypost/` for `\.renamed\b` — the only writers are
    `collection_import.py` / `environment_import.py`, and the only readers
    are the two formatter functions plus the two UI call sites above).

- **Existing tests that assert the old dict shape (confirmed, not just
  taken on faith):**
  - `tests/test_collection_import.py:275` —
    `self.assertEqual(result.renamed, {"My API": "Copy of My API"})` in
    `test_appends_renamed_copy_and_leaves_existing_untouched`.
  - `tests/test_collection_import.py:354` —
    `self.assertEqual(result.renamed, {"Billing": "Copy of Billing"})` in
    `test_second_duplicate_is_renamed_without_a_decision`.
  - `tests/test_environment_import.py:194` —
    `self.assertEqual(result.renamed, {"Dev": "Copy of Dev"})` in
    `test_appends_renamed_copy_and_leaves_existing_untouched`.
  - All three exercise exactly one rename pair per name (2 duplicates, not
    3+), so today's dict shape happens to pass them — they do not currently
    catch this bug. They will need their expected values changed from a dict
    literal to a single-element `list[tuple[str, str]]` literal
    (`[("My API", "Copy of My API")]` etc.) once the field type changes; no
    behavioral change is needed in these three cases since 2-duplicate
    behavior is already correct per the Definition of Done ("no regression"
    for 0/1/2 duplicates).

- **Language guide (`do-python.md`):** type hints via PEP 484 are mandatory,
  and `typing`/built-in generics are the expected vocabulary. `list[tuple[str,
  str]]` is a plain built-in generic alias (the module already uses
  `from __future__ import annotations` plus lowercase built-in generics like
  `list[Collection]` and `dict[str, ImportConflictDecision]` throughout), so
  it is idiomatic in this codebase — no new import needed.

- **No external research needed.** This is a pure in-repo data-shape bug with
  no third-party library, framework, or protocol involved; nothing to look up
  externally.

## Implementation Plan

1. **`pypost/core/collection_import.py`**
   - Change `CollectionImportPlanResult.renamed` field type from
     `dict[str, str]` to `list[tuple[str, str]]` (line 64).
   - In `plan_collection_import`, change the local accumulator from
     `renamed: dict[str, str] = {}` to `renamed: list[tuple[str, str]] = []`
     (line 231).
   - In the `keep_both` closure, change `renamed[name] = new_name` to
     `renamed.append((name, new_name))` (line 242). This is the only write
     site for this module (both the in-file-duplicate branch at line 248 and
     the `KEEP_BOTH` decision branch at line 277 call through `keep_both`, so
     one change covers both).
   - In `format_collection_import_result`:
     - Line 297, `len(result.renamed)` — no change; `len()` on a list counts
       every element, which is exactly the fix.
     - Line 303, change `for original, new_name in result.renamed.items():`
       to `for original, new_name in result.renamed:` — a list of 2-tuples
       unpacks the same way a dict's `.items()` view does, so the loop body
       (line 304) is untouched.

2. **`pypost/core/environment_import.py`**
   - Change `ImportPlanResult.renamed` field type from `dict[str, str]` to
     `list[tuple[str, str]]` (line 46).
   - In `plan_import`, change the local accumulator from
     `renamed: dict[str, str] = {}` to `renamed: list[tuple[str, str]] = []`
     (line 130).
   - Change both write sites from `renamed[name] = new_name` to
     `renamed.append((name, new_name))`: the in-file-duplicate branch
     (line 141) and the `KEEP_BOTH` decision branch (line 167). Unlike the
     collection module, this module does not factor keep-both into a shared
     closure, so both sites are edited directly (consistent with the existing
     structure — see `60-tech-debt.md`'s note that the collection module's
     `keep_both` closure exists for a different reason and is not something
     this task should introduce here).
   - In `format_import_result`:
     - Line 185, `len(result.renamed)` — no change, same reasoning as above.
     - Line 190, change `for original, new_name in result.renamed.items():`
       to `for original, new_name in result.renamed:`.

3. **UI-layer call sites — confirm no change required (do not edit):**
   - `pypost/ui/presenters/collection_import_actions.py` lines 93 and 97: both
     `len(result.renamed)` and `bool(... or result.renamed)` work unchanged on
     a list.
   - `pypost/ui/widgets/environments/environment_list_widget.py` lines 334 and
     338: same.
   - These files are explicitly out of scope for editing; Step 4 should touch
     only the two `pypost/core/*_import.py` modules and their tests.

4. **Existing tests — update expected value shape (Step 4, not this step):**
   - `tests/test_collection_import.py:275` →
     `self.assertEqual(result.renamed, [("My API", "Copy of My API")])`.
   - `tests/test_collection_import.py:354` →
     `self.assertEqual(result.renamed, [("Billing", "Copy of Billing")])`.
   - `tests/test_environment_import.py:194` →
     `self.assertEqual(result.renamed, [("Dev", "Copy of Dev")])`.
   - These are shape-only edits (dict literal → single-element list-of-tuple
     literal); the asserted rename pair itself does not change, since these
     tests cover the already-correct 1-duplicate and 2-total-with-one-rename
     cases.

5. **New regression tests (Step 4, per Definition of Done):** add one test to
   `tests/test_collection_import.py` and one to `tests/test_environment_import.py`
   that each import 3 (or more) entries sharing one name and assert both the
   full ordered list of rename pairs and, by extension, `len(...)` — see the
   failing-repro section below, since these are the same tests that must
   start red in Step 3 and turn green in Step 4.

**Mandatory — Failing Repro (next Step 3):**

The bug is identical in cause (last-write-wins on a `dict` keyed by the
original name) and in current test coverage shape (both sibling modules have
a passing 1-rename test but no 3-plus-duplicate test) on both the collection
and environment sides. The Definition of Done requires *both* sides fixed and
*both* to carry regression coverage ("A regression test exists for both
collection import and environment import confirming the corrected count and
listing for 3+ duplicate names"), so Step 3 must add **one red test per
module**, not just one:

- **`tests/test_collection_import.py`** — new test, e.g.
  `test_three_duplicate_names_report_two_renames_each`. Build `incoming` as
  three `Collection` instances all named `"API"` (distinct ids, empty
  requests is enough — no request-field content is relevant to this bug), no
  pre-existing `existing` collections, empty `decisions` dict (the in-file
  duplicate path never consults `decisions`, per the existing
  `test_second_duplicate_is_renamed_without_a_decision` precedent at line
  341). Call `plan_collection_import(existing=[], incoming=[...], decisions={})`
  and assert:
  - `result.renamed == [("API", "Copy of API"), ("API", "Copy of API (2)")]`
    (order matches import order, both pairs present).
  - `len(result.renamed) == 2` (this line is what actually fails today: the
    current dict implementation collapses to `{"API": "Copy of API (2)"}`,
    length 1).
  - Optionally also assert `result.added == ["API"]` and the three resulting
    collection names in `result.collections` to pin the already-correct
    non-summary behavior as a guard against a future regression in the
    unrelated code path.
  - This test is pure-unit (`Collection` model construction only, no Qt, no
    storage, no filesystem), so it belongs in the existing
    `pytest.mark.timeout(30)` module-scope marker already declared in this
    test file, per `.cursor/lsr/do-testing.md`. No live external
    dependencies either way.

- **`tests/test_environment_import.py`** — new test, e.g.
  `test_three_duplicate_names_report_two_renames_each`, mirroring the above:
  three `Environment` instances all named `"Dev"` (or any shared name),
  `existing=[]`, `decisions={}`, call `plan_import(...)`, assert
  `result.renamed == [("Dev", "Copy of Dev"), ("Dev", "Copy of Dev (2)")]` and
  `len(result.renamed) == 2`. Same pure-unit, no-live-dependency approach as
  `test_collection_import.py`, but using the `pytest.mark.timeout(60)`
  module-scope marker already declared in `tests/test_environment_import.py`
  (that file's existing tier, not the 30s tier used in the collection-side
  test file).

Sequencing for Step 3: write both tests against the *current* (buggy) `dict`
implementation first and run them to confirm they fail exactly on the
rename-list/count assertion (not on an unrelated error, e.g. a
`Collection`/`Environment` constructor signature mistake) — this proves the
red test reproduces the real defect before Step 4 touches production code.
Step 4 then applies the two-file change from the Implementation Plan above
and re-runs both tests (plus the three updated existing tests and the full
suite) to confirm green.

## Architecture

### Module Diagram

No new modules and no dependency changes. Both affected modules remain leaf,
Qt-free, storage-free planning/formatting modules; only the internal shape of
one field changes.

```text
pypost/core/collection_import.py            pypost/core/environment_import.py
  CollectionImportPlanResult.renamed           ImportPlanResult.renamed
    dict[str, str]  -->  list[tuple[str, str]]   dict[str, str]  -->  list[tuple[str, str]]
        |                                             |
        v                                             v
  format_collection_import_result()            format_import_result()
  (drop .items(), iterate tuples)              (drop .items(), iterate tuples)
        |                                             |
        v                                             v
  pypost/ui/presenters/                        pypost/ui/widgets/environments/
  collection_import_actions.py                 environment_list_widget.py
  (len()/truthiness only — no change)          (len()/truthiness only — no change)
```

- **Module boundaries are unchanged; this is a pure data-shape fix inside two
  already-pure modules.** Both `pypost/core/collection_import.py` and
  `pypost/core/environment_import.py` are documented as having "No Qt and no
  storage dependency" (collection) / "No Qt dependency" (environment) for
  their planning and formatting logic — `plan_collection_import`,
  `plan_import`, `format_collection_import_result`, and `format_import_result`
  are all deterministic functions over in-memory values. Changing the
  `renamed` field's type does not introduce, remove, or reroute any
  dependency: no new import, no I/O, no Qt widget, no `StorageInterface`
  method. The change is entirely internal to each module's existing planning
  function plus a one-line loop-shape change in each module's existing
  formatting function.

- **Why `list[tuple[str, str]]` and not, e.g., `dict[str, list[str]]` or a
  small dataclass:** The task's job is only to report every rename pair that
  occurred, in order, without loss — it does not need key-based lookup by
  original name (nothing reads `result.renamed[name]`), doesn't need
  grouping by original name (the summary prints a flat list, one line per
  rename, and the Definition of Done's examples are already flat: "lists both
  renamed collections with their new names"), and doesn't need named fields
  beyond the pair itself. A `list[tuple[str, str]]`:
  - **Preserves every pair.** A `dict` keyed by the original name can hold at
    most one value per key by definition — that structural property *is* the
    bug, not an implementation slip. Two entries that happen to share a
    `name` are, from the summary's point of view, two distinct events (two
    separate collections/environments got renamed), and only a sequence type
    can represent "N events sharing one key" without collapsing them.
  - **Preserves import order.** Appending to a list in the same loop that
    performs the rename keeps the printed order matching the order entries
    appeared in the import file, matching how `added`, `updated`, and
    `skipped` are already tracked (`list[str]`, appended in loop order) —
    `renamed` was the only one of the four summary accumulators using a
    `dict`, so this change also makes `renamed`'s shape consistent with its
    three siblings in the same dataclass.
  - **Keeps `len()` and iteration idiomatic.** `len(list)` counts elements
    (fixing the count bug automatically, with no separate counter to
    introduce or keep in sync), and `for original, new_name in result.renamed:`
    unpacking a list of 2-tuples reads identically to today's
    `.items()` loop at the call site, so the formatter functions need a
    one-token change (drop `.items()`) rather than a rewrite.

- **Why the two UI-layer call sites need no change:** Both
  `pypost/ui/presenters/collection_import_actions.py` and
  `pypost/ui/widgets/environments/environment_list_widget.py` consume
  `result.renamed` only through `len(...)` (for a logged count) and
  `bool(...)` via `or` in a `success` expression (for a truthiness check).
  Both operations are defined identically for `dict` and `list`: `len()`
  returns the element count for either container, and both are falsy exactly
  when empty and truthy otherwise. Neither call site indexes by key, calls
  `.items()`/`.keys()`/`.values()`, or otherwise depends on dict-specific
  behavior — confirmed by grep across both files, not merely assumed from the
  task description. This is precisely why the fix is a safe, localized
  data-shape change rather than a wider refactor touching the UI layer: the
  two pure-core modules are the only place that both defines and consumes the
  *shape* of `renamed` (via `.items()`), while every other consumer only
  cares about its size/emptiness.

- **No new interfaces, no new modules, no new dependencies between modules.**
  `CollectionImportPlanResult` and `ImportPlanResult` remain frozen
  dataclasses with the same field count and same field names; only one field's
  type annotation changes per dataclass. No public function signature changes
  (`plan_collection_import`, `plan_import`, `format_collection_import_result`,
  `format_import_result` all keep their existing parameter and return types).
  No caller outside the four files identified above (two core modules, two
  UI files) references `.renamed`, so the blast radius is exactly: 2
  production files edited, 2 UI files audited-and-confirmed-unchanged, 2 test
  files with 3 existing assertions updated, 2 new regression tests added.

## Q&A

- **Q: Should the fix use a `dict[str, list[str]]` (original name → list of
  new names) instead of `list[tuple[str, str]]`, to keep some form of
  key-based grouping?**
  A: No. Nothing in the codebase reads `renamed` by key (confirmed by
  grepping every reader), and grouping by original name would require every
  reader that currently does `for original, new_name in ...` to add a nested
  loop for no behavioral benefit. `list[tuple[str, str]]` is simpler and is
  what the Jira description, the tech-debt follow-up item, and the task
  instructions all specify directly.

- **Q: Does changing `renamed`'s type risk breaking anything relying on dict
  ordering guarantees (e.g., insertion order in Python 3.7+) or key
  uniqueness?**
  A: No production code relies on key uniqueness of `renamed` today (that
  reliance is the bug), and no production code relies on dict *ordering*
  either — the only iteration is the `.items()` loop in each formatter, which
  becomes a direct list iteration that preserves the same append-time order.

- **Q: Is a single shared helper/type (e.g. a `RenamedPair` NamedTuple or a
  shared summary dataclass) worth introducing across both modules given how
  similar they are?**
  A: Out of scope for this task per `10-requirements.md`'s explicit
  exclusions ("The other follow-up items noted alongside this one in the
  PYPOST-987 technical debt report ... are tracked separately and are not
  part of this task") and per the Definition of Done, which only requires the
  count/list to be correct, not a structural refactor. A plain
  `tuple[str, str]` matches the existing style in both files (neither module
  uses `NamedTuple` elsewhere) and keeps the diff minimal. Not introducing a
  shared type between the two modules is also consistent with
  `60-tech-debt.md`'s own note that the two modules are deliberately parallel
  but separate implementations ("this should be fixed in both places
  together" — together in effect, not merged into one shared module).

- **Q: Does this task change what gets imported, renamed, or saved?**
  A: No — confirmed by reading both `plan_collection_import` and `plan_import`
  in full. The primary output lists (`result.collections` /
  `result.environments`, and `result.persisted` for collections) are already
  populated correctly for every duplicate today; only the separate `renamed`
  summary accumulator undercounts. This task touches only that accumulator's
  type and the two write sites (per module) that populate it, plus the read
  sites in the two formatter functions.

- **Q: Are there live external dependencies (network, real filesystem,
  real Qt event loop) needed for the Step 3 red tests?**
  A: No. Both `plan_collection_import` and `plan_import` are pure functions
  over in-memory `Collection`/`Environment` model instances; the existing
  tests in both files already construct inputs directly and call the planner
  functions with no file I/O, no `QApplication`, and no storage backend. The
  new regression tests follow the same pattern.
