"""PYPOST-1244 red repro for bounded, indexed autocomplete lookup."""

from __future__ import annotations

import pytest

from pypost.ui.widgets.variable_autocomplete_line_edit import VariableAutocompleteLineEdit

pytestmark = pytest.mark.timeout(60)


def test_autocomplete_limits_candidates_and_supports_custom_limit(qapp) -> None:
    names = [f"TOKEN_{index:03d}" for index in range(45)]
    editor = VariableAutocompleteLineEdit(variables=names)
    try:
        editor.setText("{{ token_")
        editor.setCursorPosition(len(editor.text()))
        editor.trigger_autocomplete()
        assert len(editor.current_candidates()) == 30
        assert editor.current_candidates() == names[:30]

        custom = VariableAutocompleteLineEdit(variables=names, candidate_limit=5)
        try:
            custom.setText("{{ token_")
            custom.setCursorPosition(len(custom.text()))
            custom.trigger_autocomplete()
            assert custom.current_candidates() == names[:5]
        finally:
            custom.deleteLater()
    finally:
        editor.deleteLater()


def test_autocomplete_index_refreshes_after_variables_change(qapp) -> None:
    editor = VariableAutocompleteLineEdit(variables=["OLD_VALUE"])
    try:
        editor.set_variables(["NEW_VALUE"])
        editor.setText("{{ new")
        editor.setCursorPosition(len(editor.text()))
        editor.trigger_autocomplete()
        assert editor.current_candidates() == ["NEW_VALUE"]
        assert "OLD_VALUE" not in editor.current_candidates()
    finally:
        editor.deleteLater()
