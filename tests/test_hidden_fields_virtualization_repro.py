"""Automated repro / regression suite for PYPOST-1386.

Refactor HiddenFieldsTable to QAbstractTableModel for large selector datasets.
Asserts that:
- HiddenFieldsTableModel exists and inherits from QAbstractTableModel.
- HiddenFieldsTable inherits directly from QTableView (not QTableWidget).
- Zero QTableWidgetItem allocations when loading large selector datasets (1,000 items).
- Fast dataset load performance (< 100 ms).
- Auto-expanding trailing empty row behavior on editing.
- Multi-row batch deletion while preserving the trailing empty row.
- Signal emissions (data_changed, changed) on edits and removals.
- Backward compatibility facades (rowCount, columnCount, item(row, col).text(),
  get_data, set_data).
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from PySide6.QtCore import QAbstractTableModel, QItemSelectionModel, Qt
from PySide6.QtWidgets import (
    QTableView,
    QTableWidget,
    QTableWidgetItem,
)

from pypost.ui.models.hidden_fields_table_model import HiddenFieldsTableModel
from pypost.ui.widgets.hidden_fields_table import HiddenFieldsTable

pytestmark = pytest.mark.timeout(30)

_SELECT_ROWS = (
    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
)


def test_hidden_fields_table_model_inherits_qabstracttablemodel() -> None:
    """Assert HiddenFieldsTableModel exists and inherits from QAbstractTableModel."""
    assert issubclass(HiddenFieldsTableModel, QAbstractTableModel), (
        "HiddenFieldsTableModel must inherit from QAbstractTableModel"
    )


def test_hidden_fields_table_inherits_qtableview(qapp: Any) -> None:
    """Assert HiddenFieldsTable inherits directly from QTableView and not QTableWidget."""
    assert issubclass(HiddenFieldsTable, QTableView), (
        "HiddenFieldsTable must inherit from QTableView"
    )
    assert not issubclass(HiddenFieldsTable, QTableWidget), (
        "HiddenFieldsTable must not inherit from QTableWidget "
        "(must be virtualized QTableView)"
    )
    assert HiddenFieldsTable.__mro__[1] is QTableView, (
        "Direct base class of HiddenFieldsTable must be QTableView"
    )
    table = HiddenFieldsTable()
    try:
        assert isinstance(table.model(), QAbstractTableModel), (
            "table.model() must be an instance of QAbstractTableModel"
        )
        assert isinstance(table.model(), HiddenFieldsTableModel), (
            "table.model() must be an instance of HiddenFieldsTableModel"
        )
    finally:
        table.close()
        table.deleteLater()


def test_model_virtualization_1000_selectors_zero_qtablewidgetitem_allocations(
    qapp: Any,
) -> None:
    """Assert virtualization handles 1,000 selectors with zero QTableWidgetItem allocations."""
    table = HiddenFieldsTable()
    try:
        assert not issubclass(HiddenFieldsTable, QTableWidget), (
            "HiddenFieldsTable must be refactored away from QTableWidget "
            "for virtualization"
        )
        selectors = [f"field.selector.item_{i}" for i in range(1000)]
        start = time.perf_counter()
        table.set_data(selectors)
        elapsed = time.perf_counter() - start

        # Load time budget < 100 ms (< 0.1 s)
        assert elapsed < 0.1, (
            f"set_data(1000 items) took {elapsed * 1000:.2f} ms; expected < 100 ms"
        )

        # 1,000 items + 1 trailing empty row = 1,001 rows
        assert table.rowCount() == 1001, (
            f"Expected 1,001 rows (1,000 items + 1 trailing blank), "
            f"got {table.rowCount()}"
        )

        # Compatibility facade item(row, col) must not be a heavy QTableWidgetItem
        first_item = table.item(0, 0)
        assert first_item is not None, "table.item(0, 0) must return an item facade"
        assert not isinstance(first_item, QTableWidgetItem), (
            f"Expected lightweight item facade, got QTableWidgetItem: {type(first_item)}"
        )
        assert first_item.text() == "field.selector.item_0"

        last_data_item = table.item(999, 0)
        assert last_data_item is not None
        assert last_data_item.text() == "field.selector.item_999"

        trailing_item = table.item(1000, 0)
        assert trailing_item is not None
        assert trailing_item.text() == ""
    finally:
        table.close()
        table.deleteLater()


def test_auto_expanding_trailing_empty_row_on_editing(qapp: Any) -> None:
    """Assert editing the trailing blank row automatically appends a new empty row."""
    table = HiddenFieldsTable()
    try:
        assert not issubclass(HiddenFieldsTable, QTableWidget), (
            "HiddenFieldsTable must use QAbstractTableModel for auto-expanding "
            "trailing row"
        )
        table.set_data(["initial.selector"])
        assert table.rowCount() == 2  # ["initial.selector", ""]

        model = table.model()
        assert model is not None, "table.model() must not be None"

        # Edit trailing empty row at index 1
        trailing_index = model.index(1, 0)
        success = model.setData(
            trailing_index, "user.password", Qt.ItemDataRole.EditRole
        )
        assert success, "model.setData on trailing row must return True"

        # Should now have 3 rows: ["initial.selector", "user.password", ""]
        assert table.rowCount() == 3, (
            f"Expected rowCount to auto-expand to 3, got {table.rowCount()}"
        )
        assert table.item(0, 0).text() == "initial.selector"
        assert table.item(1, 0).text() == "user.password"
        assert table.item(2, 0).text() == ""

        # Whitespace-only edit on trailing row should NOT expand
        last_index = model.index(2, 0)
        model.setData(last_index, "   ", Qt.ItemDataRole.EditRole)
        assert table.rowCount() == 3, (
            f"Whitespace-only edit should not expand rows, got {table.rowCount()}"
        )
    finally:
        table.close()
        table.deleteLater()


def test_multi_row_batch_deletion(qapp: Any) -> None:
    """Assert multi-row batch deletion removes selected rows while preserving trailing blank row."""
    table = HiddenFieldsTable()
    try:
        table.set_data(["alpha", "bravo", "charlie", "delta", "echo"])
        assert table.rowCount() == 6  # 5 items + 1 trailing empty row

        sel_model = table.selectionModel()
        assert sel_model is not None, "table.selectionModel() must not be None"

        # Select rows 1 ("bravo") and 3 ("delta")
        model = table.model()
        assert model is not None
        sel_model.clearSelection()
        for row in (1, 3):
            idx = model.index(row, 0)
            sel_model.select(idx, _SELECT_ROWS)

        table.remove_selected_rows()

        assert table.get_data() == ["alpha", "charlie", "echo"], (
            f"Expected ['alpha', 'charlie', 'echo'], got {table.get_data()}"
        )
        assert table.rowCount() == 4
        assert table.item(3, 0).text() == ""

        # Select all remaining rows including trailing row and delete
        for row in range(table.rowCount()):
            idx = model.index(row, 0)
            sel_model.select(idx, _SELECT_ROWS)

        table.remove_selected_rows()

        # Invariant: table never has 0 rows; exactly 1 blank trailing row remains
        assert table.rowCount() == 1, (
            f"Expected exactly 1 trailing row remaining after deleting all, "
            f"got {table.rowCount()}"
        )
        assert table.get_data() == []
        assert table.item(0, 0).text() == ""
    finally:
        table.close()
        table.deleteLater()


def test_signals_emission(qapp: Any) -> None:
    """Assert data_changed and changed signals are emitted on modifications."""
    table = HiddenFieldsTable()
    try:
        assert hasattr(table, "data_changed"), "table must expose data_changed signal"
        assert hasattr(table, "changed"), "table must expose changed signal"

        data_changed_calls = 0
        changed_calls = 0

        def on_data_changed() -> None:
            nonlocal data_changed_calls
            data_changed_calls += 1

        def on_changed() -> None:
            nonlocal changed_calls
            changed_calls += 1

        table.data_changed.connect(on_data_changed)
        table.changed.connect(on_changed)

        # 1. set_data emission
        table.set_data(["token", "apiKey"])
        assert data_changed_calls >= 1, "data_changed must emit on set_data"
        assert changed_calls >= 1, "changed must emit on set_data"

        data_changed_before = data_changed_calls
        changed_before = changed_calls

        # 2. model.setData cell modification
        model = table.model()
        assert model is not None
        model.setData(model.index(0, 0), "token_updated", Qt.ItemDataRole.EditRole)
        assert data_changed_calls > data_changed_before, (
            "data_changed must emit on cell edit"
        )
        assert changed_calls > changed_before, "changed must emit on cell edit"

        data_changed_before = data_changed_calls
        changed_before = changed_calls

        # 3. add_row emission
        table.add_row("new_secret")
        assert data_changed_calls > data_changed_before, (
            "data_changed must emit on add_row"
        )
        assert changed_calls > changed_before, "changed must emit on add_row"

        data_changed_before = data_changed_calls
        changed_before = changed_calls

        # 4. remove_selected_rows emission
        sel_model = table.selectionModel()
        if sel_model is not None:
            sel_model.select(model.index(0, 0), _SELECT_ROWS)
            table.remove_selected_rows()
            assert data_changed_calls > data_changed_before, (
                "data_changed must emit on remove_selected_rows"
            )
            assert changed_calls > changed_before, (
                "changed must emit on remove_selected_rows"
            )
    finally:
        table.close()
        table.deleteLater()


def test_compatibility_facades(qapp: Any) -> None:
    """Assert compatibility facades rowCount, columnCount, item(r, c).text(), get_data, set_data."""
    table = HiddenFieldsTable()
    try:
        # Check callable facades
        assert callable(getattr(table, "rowCount", None))
        assert callable(getattr(table, "columnCount", None))
        assert callable(getattr(table, "item", None))
        assert callable(getattr(table, "get_data", None))
        assert callable(getattr(table, "set_data", None))
        assert callable(getattr(table, "add_row", None))
        assert callable(getattr(table, "remove_selected_rows", None))

        table.set_data(["selector_a", "selector_b"])
        assert table.columnCount() == 1
        assert table.rowCount() == 3
        assert table.get_data() == ["selector_a", "selector_b"]

        item0 = table.item(0, 0)
        assert item0 is not None
        assert item0.text() == "selector_a"

        item1 = table.item(1, 0)
        assert item1 is not None
        assert item1.text() == "selector_b"

        item2 = table.item(2, 0)
        assert item2 is not None
        assert item2.text() == ""

        # Out-of-bounds item query returns None or empty facade
        out_of_bounds = table.item(99, 0)
        assert out_of_bounds is None or out_of_bounds.text() == ""
    finally:
        table.close()
        table.deleteLater()
