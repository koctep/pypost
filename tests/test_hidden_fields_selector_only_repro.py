"""Selector-only model contract for PYPOST-1530."""

from typing import Any

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QSignalSpy

from pypost.ui.models.hidden_fields_table_model import HiddenFieldsTableModel

pytestmark = pytest.mark.timeout(30)


@pytest.mark.parametrize("row", [0, 1, 2])
def test_check_state_read_is_unsupported(qapp: Any, row: int) -> None:
    """Configured selectors and the trailing entry expose no activation state."""
    model = HiddenFieldsTableModel()
    model.set_data(["password", "user.token"])
    index = model.index(row, 0)

    assert not model.flags(index) & Qt.ItemFlag.ItemIsUserCheckable
    assert model.data(index, Qt.ItemDataRole.CheckStateRole) is None


@pytest.mark.parametrize("row", [0, 1, 2])
@pytest.mark.parametrize("state", [Qt.CheckState.Checked, Qt.CheckState.Unchecked])
def test_check_state_write_is_ignored(
    qapp: Any, row: int, state: Qt.CheckState,
) -> None:
    """Unsupported activation writes preserve selectors and emit no changes."""
    model = HiddenFieldsTableModel()
    selectors = ["password", "user.token"]
    model.set_data(selectors)
    data_changed = QSignalSpy(model.dataChanged)
    configuration_changed = QSignalSpy(model.data_changed)
    changed = QSignalSpy(model.changed)

    assert model.setData(model.index(row, 0), state, Qt.ItemDataRole.CheckStateRole) is False
    assert model.get_data() == selectors
    assert model.rowCount() == 3
    assert model.data(model.index(2, 0), Qt.ItemDataRole.EditRole) == ""
    assert data_changed.count() == 0
    assert configuration_changed.count() == 0
    assert changed.count() == 0
