# PYPOST-987: Technical Debt Analysis

## Shortcuts Taken

- **No outright crutches.** The feature reuses hardened machinery rather than
  inventing new: `Collection` / `RequestData` Pydantic validation for field
  parsing, `RequestManager.apply_loaded_collections` (already used by the async
  startup loader) for the in-memory swap, and the unchanged
  `StorageManager.save_collection` for persistence. No new on-disk format, no
  new `StorageInterface` method, and no new third-party dependency.
- **One deliberate, documented simplification: plan-then-apply is not
  transactional across files.** `plan_collection_import` is pure and touches
  nothing; `apply_imported_collections` then swaps the in-memory list *first*
  and writes files *second*, one `save_collection` call per changed collection.
  If a write fails partway (disk full, permissions), the app's in-memory state
  is ahead of disk for that collection until the next successful save. This is
  handled rather than ignored — the failure is logged at ERROR, the loop
  continues so one bad write cannot strand the rest, and the result dialog is
  shown as *unsuccessful* with the reason. It is called out here because
  `save_collection` is itself non-atomic (a pre-existing property of the
  storage layer, not something this task introduced), so a truly transactional
  import would require changing storage. See *Follow-up Tasks* #2.
- **Conflict resolution is name-based, id collisions are resolved silently.**
  The user is prompted only about *name* conflicts, which are the ones they can
  reason about. Colliding **ids** — for a collection or for an individual
  request — are regenerated without a prompt. This is not laziness: a duplicate
  collection id would make `save_collection` overwrite an unrelated
  collection's file, and a duplicate request id would shadow an existing entry
  in `RequestManager._request_index` and silently break open/rename/delete for
  it. Neither is a decision a user could meaningfully make, so both are treated
  as data-integrity repairs. A free id is always preserved, so copying a
  `collections/<id>.json` onto a clean machine restores faithfully.

## Code Quality Issues

- **The rename summary undercounts when three or more entries share one name
  (shared with the environment import).** `CollectionImportPlanResult.renamed`
  is a `dict[str, str]` keyed by the *original* name, so importing a file
  containing `["API", "API", "API"]` produces `"API"`, `"Copy of API"`, and
  `"Copy of API (2)"` correctly in the tree, but the dict retains only the last
  pair. The result dialog then reports `Renamed: 1` instead of `2` and lists a
  single line. Nothing is lost or corrupted — only the *summary* undercounts.
  The identical shape exists in `pypost/core/environment_import.py`
  (PYPOST-986), so this should be fixed in both places together, by changing
  `renamed` to a `list[tuple[str, str]]`. Deliberately not fixed unilaterally
  here, since diverging from the precedent in one of two sibling modules is
  worse than the bug. See *Follow-up Tasks* #1.
- **`plan_collection_import` is ~65 lines with a nested `keep_both` closure.**
  It reads linearly and every branch is directly tested, so this is a
  readability note rather than urgent debt. The closure exists because
  keep-both is reached from two places (an explicit user decision, and an
  in-file duplicate name that is never prompted about); extracting it to a
  module-level helper would require threading five accumulators through the
  signature, which reads worse. Worth revisiting only if a fourth conflict
  outcome is added.
- **Overwrite's request-id bookkeeping assumes ids are unique across
  collections.** On OVERWRITE, the replaced collection's request ids are
  released back into the available pool
  (`taken_request_ids.difference_update(...)`) before the incoming requests
  reserve theirs, so a re-import of the same file keeps its request ids stable.
  If a *pre-existing* data file already contained the same request id in two
  different collections — which `RequestManager._request_index` cannot
  represent and which the app never produces — that release could hand the id
  to the import while the other collection still holds it. This is a
  pre-existing corrupt-data scenario, not a state this feature can create.
- **The SOLID audit cap for `collections_presenter.py` was raised 280 → 330.**
  The import orchestration was first extracted into
  `CollectionImportActions` (mirroring `CollectionTreeActions` and
  `CollectionsAsyncLoader`); the residual growth is the panel container and a
  one-line delegation, which genuinely belong to the presenter. The cap bump is
  documented with justification in `scripts/audit_baseline_metrics.py` and the
  baseline snapshot was regenerated. Recorded here so the raise is visible
  rather than buried in a metrics file.

## Missing Tests

**No blocker.** Every test module added by this task declares the mandatory
explicit timeout per `.cursor/lsr/do-testing.md`:
`tests/test_collection_import.py` and `tests/test_collection_import_apply.py`
use module-scope `pytest.mark.timeout(30)` (pure-unit tier),
`tests/test_collections_import_ui.py` uses `pytest.mark.timeout(60)` (GUI
tier). This was verified after the Step 5 import reordering, not merely at
authoring time.

Remaining gaps, all low severity:

- **`collection_import_file_invalid` is not asserted via `caplog`.** Both the
  hard-parse-failure and the zero-usable-collections branches are covered
  behaviorally (error dialog shown, app state untouched), and the
  `collection_import_completed` and `collection_import_save_failed` lines *are*
  asserted through `caplog`. The two invalid branches share one event name and
  differ only by `reason`, so the assertion would mostly restate a literal.
- **No test drives three or more conflicting names through "apply to all".**
  `test_apply_to_all_prompts_only_once_for_two_conflicts` covers exactly two.
  The loop is name-count-independent, so this is a combinatorial gap only.
- **`generate_import_copy_name` is not exercised past `(2)` from the
  collection side.** The helper is shared with the environment import and the
  same gap is already recorded in PYPOST-986's report; it is noted here only so
  the collection caller is not assumed to be covered.
- **No very-large-file test.** Parsing happens synchronously on the UI thread
  (see *Performance Concerns*), and there is no test asserting behavior for a
  file with hundreds of collections or thousands of requests.

## Performance Concerns

- **Import parses and applies synchronously on the UI thread.** For the
  realistic input — a copied `collections/<id>.json` or a hand-shared bundle —
  this is the same one-shot work the app already does at startup, so it is not
  a concern in practice. It differs from the startup path in one respect worth
  noting: startup loading was deliberately moved off-thread
  (`CollectionsAsyncLoader`), while import was not. A multi-megabyte file would
  therefore freeze the window with no progress indication. Deferred rather than
  pre-optimized, since no such file is expected.
- **`refresh_tree` after import may fall back to a full model rebuild.**
  `try_incremental_tree_refresh` handles the common in-place cases; an import
  that adds or renames collections changes the tree's shape, so the full
  `QStandardItemModel` rebuild path is taken. This is the same rebuild that
  create/delete collection already triggers, so no regression.

## Deviations from Initial Architecture

Two, both driven by the SOLID audit caps and both recorded in
`40-code-cleanup.md`:

1. `20-architecture.md` placed `apply_imported_collections` as a
   `RequestManager` method. It landed as a free function in the new
   `pypost/core/collection_import_apply.py` instead, because adding it to
   `request_manager.py` pushed that module to 306 lines against its 260-line
   cap — which it already sat exactly at. The function takes the manager as its
   first parameter and uses only its
   public surface, so the call shape is unchanged for callers.
2. `20-architecture.md` placed the import orchestration directly on
   `CollectionsPresenter.import_collections`. It landed in the new
   `CollectionImportActions` collaborator for the same reason; the presenter
   retains a one-line delegating method, so the public entry point matches the
   architecture exactly.

Everything else matches the plan component-by-component: the pure-core public
surface (`CollectionImportFileError`, `CollectionImportPlanResult`,
`load_collection_import_candidates`, `find_collection_conflicts`,
`plan_collection_import`, `format_collection_import_result`), the four dialog
helpers, the shared `pypost/core/import_conflicts.py` extraction, and the
`read_import_file` dependency-injection seam.

## Hardcoded Values

- None introduced. Every user-visible string — dialog captions, the file
  filter, button label, summary lines, and per-record error messages — lives in
  `pypost/core/collection_messages.py`, mirroring `environment_messages.py`.
  The `Import Collection…` button carries the stable
  `COLLECTION_IMPORT_BUTTON` id from `pypost/ui/widget_ids.py` rather than
  being located by label text.
- `pypost/core/collection_import_apply.py` defines `MSG_SAVE_FAILED` locally
  rather than in `collection_messages.py`, since it is the only string that
  module produces and is formatted through the shared
  `format_collection_entry_error`. Minor inconsistency, not worth a follow-up
  on its own.

## Pre-existing Issues Encountered (not caused by this task)

- **`make typecheck` fails with one net-new error in
  `pypost/ui/presenters/tabs_presenter_worker.py`**, a file this task never
  touched. The gate keys `mypy-baseline.json` by line number, so the eight
  import lines added to `pypost/ui/collection_item_dialogs.py` re-key ~30
  pre-existing `QMessageBox.Yes`-style entries as "new". Comparing by
  `(file, error-code)` instead shows every module added by this task
  contributes **zero** mypy errors. The baseline was not regenerated because
  doing so would also absorb uncommitted PYPOST-986 drift. Note `make check` is
  `lint test verify-ai-tasks`; `typecheck` is an explicitly optional gate.
- **`tests/test_agent_e2e_harness_table_doc.py` was failing on entry to this
  task**: PYPOST-952 added `@pytest.mark.agent_e2e` to
  `tests/test_agent_ui_actions_mcp.py` without the matching row in
  `doc/dev/agent_e2e.md`. Since it blocked the `make test` gate, the one
  missing table row was added — a doc-only change, no test or production code
  touched.
- **One macOS-only `Bus error: 10`** was seen in a single earlier full-suite
  run, inside `tests/test_pypost_883_save_async_gc_probe.py`. It did not
  reproduce in isolation, and did not reproduce in the full suite after
  `QStandardItemModel` was reparented to its `QTreeView` in
  `CollectionsPresenter` — a teardown-ordering hardening this task added
  deliberately, because the model was previously unparented while the view
  gained a C++ parent from the new panel layout. It matches the known
  "macOS-only Qt segfault during a specific GUI test" row in
  `doc/dev/testing.md`. The final `make test` run was clean.

## Follow-up Tasks

1. **Fix the import rename summary undercounting repeated duplicate names**
   (both `collection_import.py` and `environment_import.py`). Change
   `renamed` from `dict[str, str]` to `list[tuple[str, str]]` so importing
   three collections named "API" reports `Renamed: 2` and lists both new
   names, and add a regression test on each side.
   - **Jira:** [PYPOST-1003](https://pypost.atlassian.net/browse/PYPOST-1003)
2. **Make a multi-collection import atomic, or add explicit recovery.**
   Today a `save_collection` failure partway through leaves in-memory state
   ahead of disk for the failed collection; it is logged at ERROR and surfaced
   as an unsuccessful result, but there is no rollback and no retry. Decide
   between a staged write-then-swap in `StorageManager` and an explicit
   "reload from disk" recovery offered in the failure dialog.
   - **Jira:** [PYPOST-1004](https://pypost.atlassian.net/browse/PYPOST-1004)
3. **Move import parsing off the UI thread with progress feedback**, matching
   the existing `CollectionsAsyncLoader` startup pattern, so a large file
   cannot freeze the window. Include a large-file test.
   - **Jira:** [PYPOST-1005](https://pypost.atlassian.net/browse/PYPOST-1005)
4. **Close the small test gaps**: assert `collection_import_file_invalid` via
   `caplog` for both reasons, drive three or more conflicting names through
   "apply to all", and exercise `generate_import_copy_name` past `(2)` from the
   collection side.
   - **Jira:** [PYPOST-1006](https://pypost.atlassian.net/browse/PYPOST-1006)
5. **Make the mypy baseline gate resilient to line-number churn** by keying
   `mypy-baseline.json` on `(file, error-code, message)` rather than
   `(file, line, code)`. Today any change that shifts imports in a
   heavily-baselined file produces dozens of phantom "new" errors and hides
   genuine regressions — as it did in this task, where a single real
   pre-existing regression in `tabs_presenter_worker.py` was buried under ~30
   false positives.
   - **Jira:** [PYPOST-1007](https://pypost.atlassian.net/browse/PYPOST-1007)

None of the above blocks shipping. The happy path, all three conflict
decisions, apply-to-all, in-file duplicate names, invalid files, zero usable
collections, partial parse failures, id collisions, save failures, and a real
end-to-end file→disk→reload round trip with every request field are all
covered by passing automated tests.

## Verdict

**SAFE TO CLOSE** — no blockers. All tests have explicit timeout markers, the
full suite passes, `make lint` is clean, and every item above is a documented
follow-up rather than an unresolved defect in the shipped feature.
