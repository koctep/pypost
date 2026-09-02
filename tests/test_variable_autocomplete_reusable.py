"""Failing repro for PYPOST-1243 reusable variable autocomplete behavior."""

from __future__ import annotations

import importlib
import logging
from typing import Any

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLineEdit

from pypost.ui.widgets.request_editor import RequestWidget

pytestmark = pytest.mark.timeout(60)


def _shared_autocomplete_types():
    """Load the required shared module with a deliberate, readable red assertion."""
    module_spec = importlib.util.find_spec(
        "pypost.ui.widgets.variable_autocomplete_line_edit"
    )
    assert module_spec is not None, (
        "PYPOST-1243 requires the shared variable_autocomplete_line_edit module"
    )
    module = importlib.import_module("pypost.ui.widgets.variable_autocomplete_line_edit")
    return module.VariableAutocompleteDelegate, module.VariableAutocompleteLineEdit


def _popup_item_center(editor: Any, row: int = 0) -> QPoint:
    """Return a visible point for the requested completion popup item."""
    item = editor._popup.item(row)
    assert item is not None
    return editor._popup.visualItemRect(item).center()


def _host_feedback(host: Any, text: str) -> list[dict[str, Any]]:
    """Capture the host's visible status sink while refreshing one document."""
    statuses: list[dict[str, Any]] = []
    host.show_reference_feedback = statuses.extend
    host.refresh_reference_status(text)
    return statuses


@pytest.mark.usefixtures("qapp")
def test_shared_editor_covers_trigger_filter_keyboard_and_mouse_selection(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The shared editor supports trigger, filtering, and both selection paths."""
    _, variable_autocomplete_line_edit = _shared_autocomplete_types()
    editor = variable_autocomplete_line_edit(
        variables=["API_KEY", "AUTH_TOKEN", "PUBLIC_HOST"]
    )
    try:
        editor.setText("prefix ")
        editor.setCursorPosition(len(editor.text()))
        with caplog.at_level(
            logging.DEBUG,
            logger="pypost.ui.widgets.variable_autocomplete_line_edit",
        ):
            editor.trigger_autocomplete()
        assert not editor.is_popup_visible()

        with caplog.at_level(
            logging.DEBUG,
            logger="pypost.ui.widgets.variable_autocomplete_line_edit",
        ):
            editor.insert("{{ au")
            editor.trigger_autocomplete()
        assert editor.is_popup_visible()
        assert editor.current_candidates() == ["AUTH_TOKEN"]
        assert "variable_autocomplete_triggered context=query" in caplog.text
        assert "super-secret" not in " ".join(editor.current_candidates())

        QTest.keyClick(editor, Qt.Key.Key_Down)
        with caplog.at_level(
            logging.INFO,
            logger="pypost.ui.widgets.variable_autocomplete_line_edit",
        ):
            QTest.keyClick(editor, Qt.Key.Key_Return)
        assert "variable_autocomplete_selected context=query" in caplog.text
        assert "super-secret" not in caplog.text
        assert editor.text() == "prefix {{ AUTH_TOKEN }}"
        assert not editor.is_popup_visible()

        editor.setText("prefix {{ ap }} suffix")
        editor.setCursorPosition(len("prefix {{ ap"))
        editor.trigger_autocomplete()
        assert editor.current_candidates() == ["API_KEY"]
        QTest.mouseClick(
            editor._popup.viewport(),
            Qt.MouseButton.LeftButton,
            pos=_popup_item_center(editor),
        )
        assert editor.text() == "prefix {{ API_KEY }} suffix"
        assert not editor.is_popup_visible()
    finally:
        editor.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_shared_editor_preserves_multiple_references_and_dismissal() -> None:
    """Completion changes only the active reference and Escape dismisses safely."""
    _, variable_autocomplete_line_edit = _shared_autocomplete_types()
    editor = variable_autocomplete_line_edit(variables=["API_KEY", "PUBLIC_HOST"])
    try:
        editor.setText("{{ API_KEY }} / middle {{ pub }} / tail")
        editor.setCursorPosition(len("{{ API_KEY }} / middle {{ pub"))
        editor.trigger_autocomplete()
        assert editor.current_candidates() == ["PUBLIC_HOST"]
        QTest.keyClick(editor, Qt.Key.Key_Escape)
        assert not editor.is_popup_visible()
        assert editor.text() == "{{ API_KEY }} / middle {{ pub }} / tail"

        editor.trigger_autocomplete()
        editor.apply_completion("PUBLIC_HOST")
        assert editor.text() == "{{ API_KEY }} / middle {{ PUBLIC_HOST }} / tail"
        assert "API_KEY" in editor.text()
        assert "super-secret" not in editor.text()
    finally:
        editor.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_request_hosts_share_completion_feedback_environment_switching_and_masking() -> None:
    """Params, headers, and body share safe completion and visible feedback behavior."""
    delegate_type, variable_autocomplete_line_edit = _shared_autocomplete_types()
    widget = RequestWidget()
    try:
        first_environment = {
            "API_KEY": "super-secret",
            "PUBLIC_HOST": "api.example.test",
        }
        second_environment = {
            "NEW_TOKEN": "another-secret",
            "PUBLIC_HOST": "switched.example.test",
        }
        widget.set_variables(first_environment)

        hosts = (widget.params_table, widget.headers_table, widget.body_edit)
        for host in hosts:
            assert hasattr(host, "complete_at_cursor")
            assert hasattr(host, "refresh_reference_status")

        for table in (widget.params_table, widget.headers_table):
            delegate = table.itemDelegateForColumn(1)
            assert isinstance(delegate, delegate_type)
            editor = delegate.createEditor(
                table, None, table.model().index(0, 1)
            )
            assert isinstance(editor, QLineEdit)
            assert isinstance(editor, variable_autocomplete_line_edit)
            editor.setText("before {{ API")
            editor.setCursorPosition(len(editor.text()))
            editor.trigger_autocomplete()
            assert editor.current_candidates() == ["API_KEY"]
            editor.apply_completion("API_KEY")
            assert editor.text() == "before {{ API_KEY }}"
            assert "super-secret" not in editor.text()
            editor.deleteLater()

        body_text = "first {{ API_KEY }}\nsecond {{ PUB }}\nthird {{ MISSING }}"
        result = widget.body_edit.complete_at_cursor(
            body_text, len("first {{ API_KEY }}\nsecond {{ PUB")
        )
        assert result is not None
        start, end, replacement = result
        assert body_text[start:end] == "{{ PUB"
        assert replacement == "{{ PUBLIC_HOST }}"
        assert body_text.startswith("first {{ API_KEY }}")
        assert body_text.endswith("{{ MISSING }}")

        for host in hosts:
            feedback = _host_feedback(
                host,
                "{{ }} | {{ API_KEY | {{ MISSING }}",
            )
            kinds = {status["kind"] for status in feedback}
            messages = " ".join(status["message"] for status in feedback)
            assert {"empty", "incomplete", "unavailable"} <= kinds
            assert "MISSING" in messages
            assert "super-secret" not in messages
            assert "another-secret" not in messages

        widget.set_variables(second_environment)
        for table in (widget.params_table, widget.headers_table):
            delegate = table.itemDelegateForColumn(1)
            editor = delegate.createEditor(
                table, None, table.model().index(0, 1)
            )
            editor.setText("{{ new")
            editor.setCursorPosition(len(editor.text()))
            editor.trigger_autocomplete()
            assert editor.current_candidates() == ["NEW_TOKEN"]
            assert "API_KEY" not in editor.current_candidates()
            assert "another-secret" not in editor.current_candidates()
            editor.deleteLater()

        switched_result = widget.body_edit.complete_at_cursor(
            "{{ new", len("{{ new")
        )
        assert switched_result is not None
        assert switched_result[2] == "{{ NEW_TOKEN }}"
    finally:
        widget.deleteLater()
