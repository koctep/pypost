# PYPOST-1386: Technical Debt Analysis

## Shortcuts Taken

1. **Minimal `_TableItemFacade` for test/API compatibility**:
   - `HiddenFieldsTable.item(row, col)` returns a lightweight object with only
     `.text() -> str`, not a full `QTableWidgetItem` surface (no `setText`,
     flags, roles, or ownership semantics).
   - Sufficient for current callers and
     `tests/test_request_hidden_fields_model_and_ui.py`; broader facade growth
     is deferred until a real consumer needs it.

2. **Unused per-row `enabled` / `CheckStateRole` scaffolding**:
   - Architecture reserved `HiddenFieldRecord.enabled` and
     `CheckStateRole` read/write for a possible future checkbox column
     (see `20-architecture.md` Q4).
   - The view never sets `ItemIsUserCheckable`, does not paint checkboxes, and
     `get_data()` still returns only `list[str]` — so `enabled` is never
     persisted or shown. This is intentional future-proofing left as dormant
     model code rather than a delivered feature.

3. **Dual change signals preserved verbatim**:
   - Both `data_changed` and `changed` remain on model and view and are
     forwarded 1:1; `RequestWidget` still connects both to the same
     `on_data_changed` handler (PYPOST-1377 contract).
   - No consolidation into a single signal was attempted, to avoid breaking
     any external listeners.

4. **Wall-clock load budget instead of allocator/FPS instrumentation**:
   - Virtualization is asserted via hierarchy (`QTableView` +
     `QAbstractTableModel`), zero `QTableWidgetItem` facade type, and
     `set_data(1000)` elapsed time `< 100 ms`.
   - There is no tracemalloc/RSS probe and no automated 60 FPS scroll
     measurement (NFR1 scroll fluidity relies on Qt viewport virtualization
     plus the load/type assertions above).

5. **Hardcoded default row height `26`**:
   - `verticalHeader().setDefaultSectionSize(26)` is a fixed pixel value,
     not derived from font metrics or style hints.

## Code Quality Issues

1. **Dormant checkbox API without UI flags**:
   - `data()` / `setData()` honor `CheckStateRole`, but `flags()` never
     includes `ItemIsUserCheckable`. Dead paths add review noise until either
     checkboxes ship or the scaffolding is removed.

2. **`remove_rows` removes one index at a time**:
   - Each selected row uses its own `beginRemoveRows` / `endRemoveRows` pair
     (descending). Correct and fine for typical selector counts; contiguous
     range coalescing would reduce view churn only for very large multi-select
     deletes.

3. **No selector deduplication**:
   - Carried forward from PYPOST-1377: whitespace is stripped and empties are
     dropped, but duplicate selector strings can still coexist in the model /
     persisted `hidden_response_fields` list.

4. **Stale developer docs still describe `QTableWidget`**:
   - `doc/dev/hidden_response_fields.md` still documents
     `HiddenFieldsTable` as a `QTableWidget`. Updating that doc is owned by
     STEP 8 of this task (not skipped — scheduled next).

## Missing Tests

1. **Timeout markers**:
   - **Not a blocker.** Module-level
     `pytestmark = pytest.mark.timeout(30)` covers every test in
     `tests/test_hidden_fields_virtualization_repro.py`. Related suite
     `tests/test_request_hidden_fields_model_and_ui.py` likewise uses
     module `pytestmark = pytest.mark.timeout(30)`.

2. **Keyboard Delete / Backspace and context-menu paths**:
   - Repro suite covers `remove_selected_rows()` via selection model + direct
     API call, not `keyPressEvent` / `contextMenuEvent` dispatch.
   - Behavior is implemented and unchanged in intent from PYPOST-1377; automated
     QTest-style coverage for those event paths was not added here.

3. **`add_row("")` focus / `edit()` interaction**:
   - Signal emission for `add_row("…")` is covered; empty `add_row()` that
     focuses and opens the trailing-row editor is not asserted.

4. **Observability / caplog**:
   - DEBUG mutation logs have no dedicated caplog assertions. Acceptable under
     do-testing (no new ERROR paths; C1/C2 apply to error-path tests).

5. **Scroll FPS / memory RSS**:
   - No automated 60 FPS or process-memory regression probe for the 1,000-row
     NFR claims (see Performance Concerns).

## Performance Concerns

1. **CI-sensitive wall-clock assertion**:
   - `set_data(1000)` `< 100 ms` can flake on heavily loaded shared runners
     even when algorithmic cost is fine. Threshold is generous relative to
     typical local timings (~ms), but remains environment-dependent.

2. **NFR1 60 FPS not machine-verified**:
   - Qt Model/View virtualization implies O(visible) paint cost; the suite
     does not drive a scroll loop or measure frame times. Residual risk is
     low given zero per-cell widget allocation and standard `QTableView`
     painting.

3. **Batch delete view notifications**:
   - Per-row remove notifications (above) are negligible for expected selector
     list sizes; only relevant if users multi-select thousands of rows and
     delete in one action.

## Follow-up Tasks

1. **Remove or productize dormant `enabled` / `CheckStateRole` scaffolding**:
   - Priority: Low
   - Either drop unused checkbox fields/roles until needed, or wire
     `ItemIsUserCheckable` + persistence if per-selector enable/disable becomes
     a product requirement.
   - Classification: `NON-BLOCKER`
   - Jira: [PYPOST-1530](https://pypost.atlassian.net/browse/PYPOST-1530)

2. **Event-path UI tests for Delete/Backspace and context menu**:
   - Priority: Low
   - Add QTest (or equivalent) coverage that dispatches key/context events on
     `HiddenFieldsTable` and asserts row removal / add actions.
   - Classification: `NON-BLOCKER`
   - Jira: [PYPOST-1531](https://pypost.atlassian.net/browse/PYPOST-1531)

3. **Harden large-list performance assertion**:
   - Priority: Low
   - Prefer relative/structural guards (already present) and optionally raise
     the wall-clock budget or mark the timing check as a soft/benchmark-only
     assertion if CI flakes appear.
   - Classification: `NON-BLOCKER`
   - Jira: [PYPOST-1532](https://pypost.atlassian.net/browse/PYPOST-1532)

4. **Selector deduplication policy**:
   - Priority: Low
   - Decide whether `set_data` / edits should uniquify selectors; track as a
     small UX/data-quality follow-up if product wants it.
   - Classification: `NON-BLOCKER` (pre-existing from PYPOST-1377)
   - Jira: [PYPOST-1533](https://pypost.atlassian.net/browse/PYPOST-1533)

5. **Live selector syntax validation**:
   - Priority: Medium (product backlog)
   - Already ticketed: [PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387)
   - Classification: `NON-BLOCKER` — explicitly out of scope for PYPOST-1386

6. **Developer documentation refresh for Model/View + facades**:
   - Priority: Medium (workflow)
   - Owned by STEP 8 of this task (`doc/dev/hidden_response_fields.md`).
   - Classification: `NON-BLOCKER` — not a separate Debt ticket unless STEP 8
     is deferred

### Blocker Classification

- **BLOCKER items**: 0 (all new/edited tests declare explicit
  `pytest.mark.timeout` via module `pytestmark`)
- **NON-BLOCKER items**: 6 follow-ups listed above
- **Conclusion**: No blockers prevent closing PYPOST-1386 after STEP 8 docs and
  commit. STEP 7 left `[/]` for orchestrator acceptance.
