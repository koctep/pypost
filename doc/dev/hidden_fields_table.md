# Virtualized Hidden Fields Table (PYPOST-1386 / PYPOST-1387)

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

[PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387) adds **advisory
inline syntax validation** so invalid or unsupported selectors are visible
while drafting, without blocking edits or silently rewriting text:

- Pure core `validate_field_selector` / `FieldSelectorSyntaxResult`
- Model `BackgroundRole` highlight and conditional `ToolTipRole` guidance
- Advisory `FieldSelectorDelegate` for as-you-type editor feedback

Persistence, MCP sanitization, and ResponseView click-to-reveal are unchanged.
Epic context lives in [Hidden Response Fields](hidden_response_fields.md).
Selector matching at mask time is documented in
[Unified JSON Selector Path Evaluation Engine](json_selector_engine.md).

## Architecture

| Component | Module | Role |
| --- | --- | --- |
| `validate_field_selector` | `pypost/core/field_selector_syntax.py` | Pure vocabulary check (no Qt); returns `FieldSelectorSyntaxResult` |
| `HiddenFieldRecord` | `pypost/ui/models/hidden_fields_table_model.py` | Dataclass row (`selector`, optional dormant `enabled`, cached `syntax`) |
| `HiddenFieldsTableModel` | same | Virtualized data source, trailing-row expand, batch mutate, role surfacing, DEBUG logs |
| `FieldSelectorDelegate` | `pypost/ui/delegates/field_selector_delegate.py` | Advisory live editor styling/tooltip; always commits typed text |
| `HiddenFieldsTable` | `pypost/ui/widgets/hidden_fields_table.py` | `QTableView` view, installs delegate, menus/shortcuts, API + facades |
| `_TableItemFacade` | same | `item(row, col).text()` compatibility for tests |

```mermaid
graph TD
  RW["RequestWidget"]
  HFT["HiddenFieldsTable (QTableView)"]
  FSD["FieldSelectorDelegate"]
  Facade["_TableItemFacade"]
  HFTM["HiddenFieldsTableModel"]
  Records["_records: list[HiddenFieldRecord]"]
  VFS["validate_field_selector"]
  RD["RequestData.hidden_response_fields"]

  RW -->|set_data / get_data / signals| HFT
  RW -->|load / save list[str]| RD
  HFT -->|setModel| HFTM
  HFT -->|setItemDelegate| FSD
  HFT -->|item facade| Facade
  FSD -->|textChanged / setModelData| VFS
  HFTM -->|cache on mutate| VFS
  HFTM --> Records
  Facade -.->|DisplayRole| HFTM
  HFTM -->|"BackgroundRole / ToolTipRole"| HFT
```

### Trailing blank row

`rowCount()` is always `len(_records)` and the last record is blank
(`selector == ""`). Committing non-empty text on that row updates the selector,
inserts a new blank trailer via `beginInsertRows` / `endInsertRows`, and emits
model + table change signals so dirty tracking stays live. Empty / whitespace
selectors are syntax-`ok` with `is_empty=True` — the trailer never shows an
error highlight.

### Virtualization characteristics

| Metric (≈1,000 selectors) | Pre-refactor `QTableWidget` | Model/View |
| --- | --- | --- |
| Off-screen cell items | One `QTableWidgetItem` per row | None |
| `set_data` cost | Per-item allocation | Single `beginResetModel` + list rebuild |
| Scroll paint cost | Layout over full `N` | `O(visible)` via `model.data()` |

Syntax results are **cached on each `HiddenFieldRecord`** so scroll/repaint
does not re-run the validator on every `data()` role query.

### Compatibility facades

Existing UI tests still call `rowCount()` and `item(row, col).text()`. The view
forwards counts to the model and returns `_TableItemFacade` with `.text()` only
(not a full `QTableWidgetItem`). Prefer model/`get_data` APIs in new code.

`HiddenFieldsTableModel` is defined under `pypost.ui.models` and re-exported from
`pypost.ui.widgets.hidden_fields_table` (`__all__`).
`FieldSelectorDelegate` is exported from `pypost.ui.delegates`.

## Inline syntax validation (PYPOST-1387)

Validation is **advisory**: invalid selectors stay in the model and are returned
unchanged by `get_data()`. There is no save hard-block and no silent rewrite.
Runtime masking still quietly no-ops unsupported forms; the UI validates against
the **documented supported vocabulary**, not against every string
`JsonSelectorEngine` happens to compile.

### Supported vocabulary

`validate_field_selector(text)` strips input, then classifies:

| Outcome | Rule | Examples |
| --- | --- | --- |
| Empty | `""` / whitespace → `ok=True`, `is_empty=True` | trailing blank row |
| Header | `(?i)^header:(.+)$` with non-empty name | `header:Authorization` |
| Simple key | Single identifier segment | `token`, `api_key` |
| Path | Identifier / `*` segments joined by `.`; surface `[*]` normalizes to `*` | `auth.token`, `users[*].email`, `[*].id` |
| Invalid | `$…` JSONPath, filters, numeric indexes, empty `header:`, bad punctuation, etc. | `$.users[0].name`, `header:` |

Invalid results carry a plain-language `message` plus short `suggestions`
listing the four supported families.

### Model roles

Committed cells surface validation through standard item roles (default styled
delegate paints them without a custom paint path):

| Role | Behavior |
| --- | --- |
| `BackgroundRole` | Soft warning `QBrush` (`VALIDATION_LINE_BACKGROUND`) when `not ok and not is_empty`; else `None` |
| `ToolTipRole` | `message` + `suggestions` when invalid; neutral help string for valid non-empty selectors; `None` for empty |

`setData` / bulk mutate paths refresh the cached `syntax` on the record and
include `DisplayRole`, `EditRole`, `BackgroundRole`, and `ToolTipRole` in
`dataChanged` payloads so highlights update immediately after commit.

### Live editor feedback (`FieldSelectorDelegate`)

`HiddenFieldsTable` installs `FieldSelectorDelegate` as its item delegate.

While the cell editor (`QLineEdit`) is open:

1. `textChanged` → `validate_field_selector`
2. Invalid (non-empty) → editor stylesheet uses `VALIDATION_LABEL_*` tokens and
   a guidance tooltip
3. Valid / empty → clear stylesheet and tooltip
4. `setModelData` **always** commits the typed text (including invalid drafts)

This differs intentionally from rejecting delegates such as
`EnvironmentNameDelegate`.

### Feedback flow

```
User types in editor
  → FieldSelectorDelegate.textChanged
      → style editor + set editor tooltip (invalid only)
  → (does not rewrite text; does not block keys)

User commits edit (Enter / focus leave)
  → delegate.setModelData → model.setData (always accepts stripped text)
      → validate_field_selector → cache on HiddenFieldRecord
      → dataChanged(..., Display|Edit|Background|ToolTip)
      → view paints soft error background; hover shows ToolTipRole
```

## API / Usage

### `validate_field_selector(text: str) -> FieldSelectorSyntaxResult`

Pure check in `pypost.core.field_selector_syntax`. No Qt dependency.

- **text**: raw selector string (stripped internally)
- **Returns**: frozen dataclass with `ok`, `is_empty`, `message`, `suggestions`

```python
from pypost.core.field_selector_syntax import validate_field_selector

assert validate_field_selector("auth.token").ok
assert not validate_field_selector("$.users[0].name").ok
assert validate_field_selector("  ").is_empty
```

### `HiddenFieldsTable(parent=None)`

Virtualized single-column editor. Object name:
`REQUEST_HIDDEN_FIELDS_TABLE` (`request_hidden_fields_table`).
Wires `FieldSelectorDelegate` in `__init__`.

### `set_data(data: list[str]) -> None`

Filters empty/whitespace selectors, rebuilds records (each with cached syntax),
appends one trailing blank row, emits `data_changed` and `changed`.

### `get_data() -> list[str]`

Non-empty selectors in row order (trailing/blank rows omitted). Invalid
selectors are included as authored — validation does not filter them out.

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
from PySide6.QtCore import Qt
from pypost.ui.widgets.hidden_fields_table import (
    HiddenFieldsTable,
    HiddenFieldsTableModel,
)

table = HiddenFieldsTable(parent)
table.set_data(["token", "$.bad"])
assert table.rowCount() == 3  # two selectors + trailing blank
assert table.get_data() == ["token", "$.bad"]  # invalid kept
model = table.model()
bad = model.index(1, 0)
assert model.data(bad, Qt.ItemDataRole.BackgroundRole) is not None
assert "Supported forms" in model.data(bad, Qt.ItemDataRole.ToolTipRole)
```

## Configuration

No environment variables. Column header is `"Field Selector"` with stretch
resize; default vertical section size is `26` px. Checkbox/`enabled` roles exist
on the model for future use but are not shown in the view.

Highlight colors come from UI tokens:

- Committed cell: `VALIDATION_LINE_BACKGROUND`
- Live editor: `VALIDATION_LABEL_BACKGROUND` / `VALIDATION_LABEL_FOREGROUND`

## Observability

Module logger: `pypost.ui.models.hidden_fields_table_model`. DEBUG events (counts
and lengths only — never selector text):

| Event | When |
| --- | --- |
| `hidden_fields_table_model_set_data` | Bulk `set_data` (includes `ok_count` / `invalid_count` / `empty_count`) |
| `hidden_fields_table_model_set_data_cell` | Committed cell edit (`ok` / `is_empty` / `selector_len`) |
| `hidden_fields_table_model_trailing_row_expanded` | Trailing-row auto-append |
| `hidden_fields_table_model_add_row` | `add_row` (`reuse_trailing` / `focus_trailing` / `insert`; includes `ok=`) |
| `hidden_fields_table_model_remove_rows` | Batch delete |

`validate_field_selector` and the delegate live `textChanged` path intentionally
log nothing (would flood DEBUG on every keystroke). No new Prometheus metrics;
masking/save counters stay on the response/MCP paths.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Tests expect `QTableWidget` / `QTableWidgetItem` | Assert `QTableView` + `HiddenFieldsTableModel`; use `item(...).text()` facade |
| Empty editor after load | `set_data([])` must leave `rowCount() == 1` blank trailer |
| Delete removes nothing while editing a cell | Delete/Backspace only remove rows when not in `EditingState` |
| Tab not dirty after edit | Wire both `data_changed` and `changed` (or one) to `on_data_changed` |
| Scroll lag with huge lists | Confirm view is `QTableView` with model set; do not reintroduce per-row widgets |
| Invalid selector has no highlight after commit | Inspect `model.data(index, BackgroundRole)` and cached `record.syntax`; confirm delegate is installed |
| Hover tooltip is only the static help string | Invalid rows must get `ToolTipRole` with errorish wording **and** a supported-form example (not just `"dot"`) |
| Live typing shows no red editor | `FieldSelectorDelegate` styles the `QLineEdit` only while editing; committed cells use model `BackgroundRole` |
| Expected save to reject bad selectors | By design advisory — `get_data()` returns invalid strings; fix UX, do not hard-block |

## Tests

```bash
make test PYTEST_ARGS="tests/test_hidden_fields_virtualization_repro.py"
make test PYTEST_ARGS="tests/test_request_hidden_fields_model_and_ui.py"
make test PYTEST_ARGS="tests/test_field_selector_syntax.py"
make test PYTEST_ARGS="tests/test_hidden_fields_syntax_validation_repro.py"
```

Virtualization suite covers hierarchy, 1,000-row `set_data` budget, trailing
expand, batch delete, signals, and facades. Syntax suite covers the pure
validator contract and model `BackgroundRole` / `ToolTipRole` guidance after
`set_data` (`pytestmark` timeout 30).

## References

- [Hidden Response Fields](hidden_response_fields.md)
- [Unified JSON Selector Path Evaluation Engine](json_selector_engine.md)
- Requirements: [`ai-tasks/PYPOST-1387/10-requirements.md`](../../ai-tasks/PYPOST-1387/10-requirements.md)
- Architecture: [`ai-tasks/PYPOST-1387/20-architecture.md`](../../ai-tasks/PYPOST-1387/20-architecture.md)
- Virtualization requirements: [`ai-tasks/PYPOST-1386/10-requirements.md`](../../ai-tasks/PYPOST-1386/10-requirements.md)
- Virtualization architecture: [`ai-tasks/PYPOST-1386/20-architecture.md`](../../ai-tasks/PYPOST-1386/20-architecture.md)
- Core validator: [`pypost/core/field_selector_syntax.py`](../../pypost/core/field_selector_syntax.py)
- Model: [`pypost/ui/models/hidden_fields_table_model.py`](../../pypost/ui/models/hidden_fields_table_model.py)
- Delegate: [`pypost/ui/delegates/field_selector_delegate.py`](../../pypost/ui/delegates/field_selector_delegate.py)
- View: [`pypost/ui/widgets/hidden_fields_table.py`](../../pypost/ui/widgets/hidden_fields_table.py)
