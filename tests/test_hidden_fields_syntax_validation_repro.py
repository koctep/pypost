"""Repro / UI suite for PYPOST-1387 inline syntax validation in HiddenFieldsTable.

Asserts model BackgroundRole / ToolTipRole feedback and advisory get_data
behavior from ``ai-tasks/PYPOST-1387/20-architecture.md``.
"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import Qt

from pypost.ui.models.hidden_fields_table_model import HiddenFieldsTableModel
from pypost.ui.widgets.hidden_fields_table import HiddenFieldsTable

pytestmark = pytest.mark.timeout(30)

# Neutral static help today: "Response field selector or dot-notation path".
# Guidance must not pass merely because a weak token like "dot" appears there.
_STATIC_HELP_TOOLTIP = "Response field selector or dot-notation path"
_ERRORISH_TOOLTIP_TOKENS = (
    "invalid",
    "unsupported",
    "error",
    "not accepted",
    "not supported",
)
_SUPPORTED_FORM_EXAMPLES = (
    "token",
    "auth.token",
    "users[*].email",
    "[*].id",
    "users.email",
    "header:Authorization",
)


def _tooltip_has_guidance(tooltip: Any) -> bool:
    """True only when tooltip is errorish *and* cites a concrete supported form.

    Weak substrings of the current static help string (e.g. ``dot``) must not
    satisfy this check — the static tooltip must remain red until production
    returns real validation guidance.
    """
    text = str(tooltip or "").lower()
    if not text.strip():
        return False
    static_lower = _STATIC_HELP_TOOLTIP.lower()
    has_errorish = any(token in text for token in _ERRORISH_TOOLTIP_TOKENS)
    has_supported_example = any(
        example.lower() in text
        for example in _SUPPORTED_FORM_EXAMPLES
        if example.lower() not in static_lower
    )
    return has_errorish and has_supported_example


def _assert_invalid_cell_feedback(model: HiddenFieldsTableModel, row: int) -> None:
    index = model.index(row, 0)
    background = model.data(index, Qt.ItemDataRole.BackgroundRole)
    tooltip = model.data(index, Qt.ItemDataRole.ToolTipRole)
    problems: list[str] = []
    if background is None:
        problems.append("missing BackgroundRole highlight")
    if not _tooltip_has_guidance(tooltip):
        problems.append(
            "ToolTipRole lacks errorish wording plus a supported-form example "
            f"(got {tooltip!r})"
        )
    assert not problems, f"row {row}: invalid selector feedback incomplete: {'; '.join(problems)}"


def _assert_no_error_feedback(model: HiddenFieldsTableModel, row: int) -> None:
    index = model.index(row, 0)
    background = model.data(index, Qt.ItemDataRole.BackgroundRole)
    tooltip = model.data(index, Qt.ItemDataRole.ToolTipRole)
    assert background is None, (
        f"row {row}: valid/empty selector must not have error BackgroundRole; "
        f"got {background!r}"
    )
    tooltip_text = str(tooltip or "").lower()
    assert not any(token in tooltip_text for token in _ERRORISH_TOOLTIP_TOKENS), (
        f"row {row}: valid/empty selector must not show an error tooltip; got {tooltip!r}"
    )


def test_model_set_data_highlights_invalid_selector(qapp: Any) -> None:
    """After set_data with an invalid selector, BackgroundRole and ToolTipRole guide the user."""
    model = HiddenFieldsTableModel()
    model.set_data(["$.users[0].name"])
    _assert_invalid_cell_feedback(model, 0)
    _assert_no_error_feedback(model, 1)  # trailing blank row


def test_model_set_data_clears_highlight_for_valid_selector(qapp: Any) -> None:
    """Valid selectors must not keep an error background or error tooltip."""
    model = HiddenFieldsTableModel()
    model.set_data(["auth.token", "header:Authorization", "users[*].email"])
    for row in range(3):
        _assert_no_error_feedback(model, row)
    _assert_no_error_feedback(model, 3)  # trailing blank


def test_model_setData_invalid_then_valid_updates_roles(qapp: Any) -> None:
    """Editing from invalid to valid via setData must clear error chrome."""
    model = HiddenFieldsTableModel()
    model.set_data(["token"])
    index = model.index(0, 0)

    assert model.setData(index, "users[0].name", Qt.ItemDataRole.EditRole) is True
    _assert_invalid_cell_feedback(model, 0)

    assert model.setData(index, "users[*].email", Qt.ItemDataRole.EditRole) is True
    _assert_no_error_feedback(model, 0)


def test_trailing_blank_row_has_no_error_background(qapp: Any) -> None:
    """Empty trailing row used for new entry must never appear as a syntax error."""
    model = HiddenFieldsTableModel()
    model.set_data(["token"])
    trailing = model.rowCount() - 1
    assert model.data(model.index(trailing, 0), Qt.ItemDataRole.DisplayRole) == ""
    _assert_no_error_feedback(model, trailing)


def test_get_data_preserves_invalid_selectors_advisory(qapp: Any) -> None:
    """Advisory validation must not rewrite or drop invalid draft selectors from get_data()."""
    model = HiddenFieldsTableModel()
    invalid = "$.users[0].name"
    model.set_data([invalid, "token"])
    assert model.get_data() == [invalid, "token"]


def test_table_set_data_exposes_invalid_background_and_tooltip(qapp: Any) -> None:
    """HiddenFieldsTable.set_data must surface the same model role feedback for invalid rows."""
    table = HiddenFieldsTable()
    try:
        table.set_data(["users[0].name", "token"])
        model = table.model()
        assert isinstance(model, HiddenFieldsTableModel)
        _assert_invalid_cell_feedback(model, 0)
        _assert_no_error_feedback(model, 1)
        assert table.get_data() == ["users[0].name", "token"]
    finally:
        table.close()
        table.deleteLater()
