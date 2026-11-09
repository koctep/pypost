# PYPOST-1530: Selector-only hidden field rows

## Research

The model currently stores `HiddenFieldRecord.enabled` and answers/writes `CheckStateRole`,
but its flags omit `ItemIsUserCheckable`. `get_data()` exports every non-empty selector
regardless of that state. Repository search found no callers of the activation state outside
this model. The widget delegates selector editing and forwards model change signals.

Qt models expose individual roles through `data()` and `setData()`; unsupported data has no
value, and successful changes explicitly emit `dataChanged`. See the official
[QAbstractItemModel documentation](https://doc.qt.io/qt-6/qabstractitemmodel.html).
The existing Qt model/view pattern remains appropriate for virtualized selector rows.

## Implementation Plan

1. Step 3: Add a focused test in `tests/test_hidden_fields_selector_only_repro.py` that loads
   selectors and verifies `CheckStateRole` reads return `None` and writes return `False`
   without data/change signals or selector mutation. Include the trailing blank row.
   Existing code fails these assertions on a populated row; no external service is needed.
2. Step 4: Remove the record's enabled field, the factory's enabled argument, and both
   check-state branches. Retain cached syntax and all selector edit roles and signals.
3. Run the new test until green, then the existing virtualization, selector syntax, and
   request hidden-fields persistence/UI suites through `make test` with targeted arguments.
4. Update developer documentation to describe selector-only rows and unsupported check state.
   Run applicable Make quality gates before completion.

The sequence is research, reviewed red verification, then the production change. The test
checks the model's unsupported-role contract; it does not require private field inspection.

## Architecture

```text
RequestWidget / saved RequestData.hidden_response_fields: list[str]
    <-> HiddenFieldsTable (QTableView facade, selector edit delegate, signal forwarding)
    <-> HiddenFieldsTableModel (ordered rows and trailing blank, Qt notifications)
        -> HiddenFieldRecord (selector and cached advisory syntax only)
        -> validate_field_selector (existing syntax feedback)
```

The change stays inside the model; persistence, masking engine, widget, and delegate need no
new dependency or format migration. The model retains `set_data(list[str])`,
`get_data() -> list[str]`, `add_row()`, `remove_rows()`, editable/display/syntax roles, and
`data_changed` / `changed` signals for supported mutations. `CheckStateRole` follows the
existing unsupported-role fallbacks: no value on read, `False` on write, and no signals.
Rows remain enabled, selectable, and editable in Qt flags, without user-checkable capability.

## Q&A

- Why removal? The ticket explicitly permits removal and there is no delivered disable
  control or saved activation state. Keeping all selectors active preserves masking coverage.
- What is outside scope? Deduplication, event-path additions, timing-budget changes, and new
  activation controls belong to their own sprint issues.
- How is acceptance gated? Independent review in the authorized autonomous runner.
