# Virtualized Hidden Fields Table (PYPOST-1386)

## Overview

The Request Editor **Hidden Fields** tab manages the ordered list of response
field selectors stored on `RequestData.hidden_response_fields`. Early delivery
([PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377)) used a concrete
`QTableWidget` with one `QTableWidgetItem` per row. That approach is fine for
small lists but allocates off-screen items for every selector, which hurts load
time, memory, and scroll fluidity once catalogs grow past hundreds of paths.

[PYPOST-1386](https://pypost.atlassian.net/browse/PYPOST-1386) refactors the
editor table to Qt Model/View virtualization:

- **`HiddenFieldsTableModel`** (`QAbstractTableModel`) owns lightweight
  `HiddenFieldRecord` rows and the trailing blank-row invariant.
- **`HiddenFieldsTable`** (`QTableView`) paints only visible rows and keeps the
  public editor/test API (`get_data`, `set_data`, `add_row`,
  `remove_selected_rows`, `data_changed` / `changed`, plus `rowCount` /
  `item` facades).

Persistence, MCP sanitization, and ResponseView click-to-reveal are unchanged.
Epic context lives in [Hidden Response Fields](hidden_response_fields.md).

## Architecture

| Component | Module | Role |
| --- | --- | --- |
| `HiddenFieldRecord` | `pypost/ui/models/hidden_fields_table_model.py` | Dataclass row (`selector`, optional dormant `enabled`) |
| `HiddenFieldsTableModel` | same | Virtualized data source, trailing-row expand, batch mutate, DEBUG logs |
| `HiddenFieldsTable` | `pypost/ui/widgets/hidden_fields_table.py` | `QTableView` view, menus/shortcuts, API + facades |
| `_TableItemFacade` | same | `item(row, col).text()` compatibility for tests |

```mermaid
graph TD
  RW["RequestWidget"]
  HFT["HiddenFieldsTable (QTableView)"]
  Facade["_TableItemFacade"]
  HFTM["HiddenFieldsTableModel"]
  Records["_records: list[HiddenFieldRecord]"]
  RD["RequestData.hidden_response_fields"]

  RW -->|set_data / get_data / signals| HFT
  RW -->|load / save list[str]| RD
  HFT -->|setModel| HFTM
  HFT -->|item facade| Facade
  HFTM --> Records
  Facade -.->|DisplayRole| HFTM
```

### Trailing blank row

`rowCount()` is always `len(_records)` and the last record is blank
(`selector == ""`). Committing non-empty text on that row updates the selector,
inserts a new blank trailer via `beginInsertRows` / `endInsertRows`, and emits
model + table change signals so dirty tracking stays live.

### Virtualization characteristics

| Metric (≈1,000 selectors) | Pre-refactor `QTableWidget` | Model/View |
| --- | --- | --- |
| Off-screen cell items | One `QTableWidgetItem` per row | None |
| `set_data` cost | Per-item allocation | Single `beginResetModel` + list rebuild |
| Scroll paint cost | Layout over full `N` | `O(visible)` via `model.data()` |

### Compatibility facades

Existing UI tests still call `rowCount()` and `item(row, col).text()`. The view
forwards counts to the model and returns `_TableItemFacade` with `.text()` only
(not a full `QTableWidgetItem`). Prefer model/`get_data` APIs in new code.

`HiddenFieldsTableModel` is defined under `pypost.ui.models` and re-exported from
`pypost.ui.widgets.hidden_fields_table` (`__all__`).

## API / Usage

### `HiddenFieldsTable(parent=None)`

Virtualized single-column editor. Object name:
`REQUEST_HIDDEN_FIELDS_TABLE` (`request_hidden_fields_table`).

### `set_data(data: list[str]) -> None`

Filters empty/whitespace selectors, rebuilds records, appends one trailing blank
row, emits `data_changed` and `changed`.

### `get_data() -> list[str]`

Non-empty selectors in row order (trailing/blank rows omitted).

### `add_row(selector: str = "") -> None`

Reuses or fills the trailing blank row; focuses the row and opens the editor when
`selector` is empty.

### `remove_selected_rows() -> None`

Deletes selected non-trailing rows (context menu / Delete / Backspace outside
edit mode). Always leaves exactly one blank trailer.

### Compatibility

- `rowCount() -> int` / `columnCount() -> int`
- `item(row, column) -> _TableItemFacade | None` with `.text() -> str`

### Signals

- `data_changed = Signal()`
- `changed = Signal()`

Both are forwarded from the model; `RequestWidget` connects them to dirty
tracking.

```python
from pypost.ui.widgets.hidden_fields_table import (
    HiddenFieldsTable,
    HiddenFieldsTableModel,
)

table = HiddenFieldsTable(parent)
table.set_data(["token", "user.email"])
assert table.rowCount() == 3  # two selectors + trailing blank
assert table.get_data() == ["token", "user.email"]
assert table.item(0, 0).text() == "token"
```

## Configuration

No environment variables. Column header is `"Field Selector"` with stretch
resize; default vertical section size is `26` px. Checkbox/`enabled` roles exist
on the model for future use but are not shown in the view.

## Observability

Module logger: `pypost.ui.models.hidden_fields_table_model`. DEBUG events (counts
and lengths only — never selector text):

| Event | When |
| --- | --- |
| `hidden_fields_table_model_set_data` | Bulk `set_data` |
| `hidden_fields_table_model_trailing_row_expanded` | Trailing-row auto-append |
| `hidden_fields_table_model_add_row` | `add_row` (`reuse_trailing` / `focus_trailing` / `insert`) |
| `hidden_fields_table_model_remove_rows` | Batch delete |

No new Prometheus metrics; masking/save counters stay on the response/MCP paths.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Tests expect `QTableWidget` / `QTableWidgetItem` | Assert `QTableView` + `HiddenFieldsTableModel`; use `item(...).text()` facade |
| Empty editor after load | `set_data([])` must leave `rowCount() == 1` blank trailer |
| Delete removes nothing while editing a cell | Delete/Backspace only remove rows when not in `EditingState` |
| Tab not dirty after edit | Wire both `data_changed` and `changed` (or one) to `on_data_changed` |
| Scroll lag with huge lists | Confirm view is `QTableView` with model set; do not reintroduce per-row widgets |

## Tests

```bash
make test PYTEST_ARGS="tests/test_hidden_fields_virtualization_repro.py"
make test PYTEST_ARGS="tests/test_request_hidden_fields_model_and_ui.py"
```

Repro suite covers hierarchy, 1,000-row `set_data` budget, trailing expand,
batch delete, signals, and facades (`pytestmark` timeout 30).

## References

- [Hidden Response Fields](hidden_response_fields.md)
- Requirements: [`ai-tasks/PYPOST-1386/10-requirements.md`](../../ai-tasks/PYPOST-1386/10-requirements.md)
- Architecture: [`ai-tasks/PYPOST-1386/20-architecture.md`](../../ai-tasks/PYPOST-1386/20-architecture.md)
- Model: [`pypost/ui/models/hidden_fields_table_model.py`](../../pypost/ui/models/hidden_fields_table_model.py)
- View: [`pypost/ui/widgets/hidden_fields_table.py`](../../pypost/ui/widgets/hidden_fields_table.py)
