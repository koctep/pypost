"""Open-edit warning and advisory accept for hidden-field selectors (PYPOST-1537)."""

from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit

from pypost.ui.styles.ui_tokens import (
    VALIDATION_LABEL_BACKGROUND,
    VALIDATION_LABEL_FOREGROUND,
)
from pypost.ui.widgets.hidden_fields_table import HiddenFieldsTable

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def table(qapp: Any) -> Iterator[HiddenFieldsTable]:
    widget = HiddenFieldsTable()
    widget.show()
    try:
        yield widget
    finally:
        widget.close()
        widget.deleteLater()


def test_open_edit_warns_stays_neutral_and_keeps_invalid_draft(
    table: HiddenFieldsTable,
) -> None:
    model = table.model()
    assert model is not None
    index = model.index(0, 0)
    table.setCurrentIndex(index)
    table.edit(index)
    assert table.state() == HiddenFieldsTable.State.EditingState
    editor = table.findChild(QLineEdit)
    assert isinstance(editor, QLineEdit)

    editor.setText("$.secret")
    assert table.state() == HiddenFieldsTable.State.EditingState
    stylesheet = editor.styleSheet()
    assert VALIDATION_LABEL_BACKGROUND in stylesheet
    assert VALIDATION_LABEL_FOREGROUND in stylesheet
    assert editor.toolTip()

    editor.setText("token")
    assert table.state() == HiddenFieldsTable.State.EditingState
    assert editor.styleSheet() == ""
    assert editor.toolTip() == ""

    editor.setText("$.secret")
    QTest.keyClick(editor, Qt.Key.Key_Return)
    # Commit is queued, so one event-loop turn stores the draft.
    QCoreApplication.processEvents()

    stored = table.item(0, 0)
    assert stored is not None
    assert stored.text() == "$.secret"
    assert table.get_data() == ["$.secret"]
