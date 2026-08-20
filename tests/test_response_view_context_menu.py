"""Qt-level tests for ResponseView context menu (PYPOST-164, PYPOST-22)."""

import pytest

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QPoint
from PySide6.QtGui import QTextCursor

from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(60)


_QMENU_PATCH = "pypost.ui.widgets.response_view.QMenu"


def _select_text(view: ResponseView, text: str) -> None:
    body = view.body_view.toPlainText()
    start = body.index(text)
    cursor = view.body_view.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + len(text), QTextCursor.MoveMode.KeepAnchor)
    view.body_view.setTextCursor(cursor)


def _trigger_connected(action: MagicMock) -> None:
    connect_mock = action.triggered.connect
    callback = connect_mock.call_args[0][0]
    callback()


class TestResponseViewContextMenu:
    def test_without_env_keys_omits_set_variable_submenu(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("token-value")
            _select_text(view, "token-value")

            mock_menu = MagicMock()
            mock_menu.isEmpty.return_value = True
            copy_action = MagicMock()
            select_all_action = MagicMock()
            mock_menu.addAction.side_effect = lambda label: {
                "Copy": copy_action,
                "Select All": select_all_action,
            }[label]

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            mock_menu.addMenu.assert_not_called()
            mock_menu.addAction.assert_any_call("Copy")
            mock_menu.addAction.assert_any_call("Select All")
            mock_menu.exec.assert_called_once()
        finally:
            view.close()

    def test_with_env_keys_builds_set_variable_submenu(self, qapp):
        view = ResponseView()
        try:
            view.set_env_keys(["API_KEY", "TOKEN"])
            view.body_view.setPlainText("secret")
            _select_text(view, "secret")

            mock_menu = MagicMock()
            mock_submenu = MagicMock()
            mock_menu.addMenu.return_value = mock_submenu
            mock_menu.isEmpty.return_value = False
            copy_action = MagicMock()
            select_all_action = MagicMock()
            mock_menu.addAction.side_effect = lambda label: {
                "Copy": copy_action,
                "Select All": select_all_action,
            }[label]
            key_actions = [MagicMock(), MagicMock()]
            new_var_action = MagicMock()
            mock_submenu.addAction.side_effect = [
                key_actions[0],
                key_actions[1],
                new_var_action,
            ]

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            mock_menu.addMenu.assert_called_once_with("Set Variable")
            assert mock_submenu.addAction.call_count == 3
            mock_submenu.addSeparator.assert_called_once()
            mock_menu.addAction.assert_any_call("Copy")
        finally:
            view.close()

    def test_env_key_selection_emits_variable_set_requested(self, qapp):
        view = ResponseView()
        try:
            view.set_env_keys(["API_KEY"])
            view.body_view.setPlainText("my-value")
            _select_text(view, "my-value")

            received = []
            view.variable_set_requested.connect(
                lambda key, value: received.append((key, value))
            )

            mock_menu = MagicMock()
            mock_submenu = MagicMock()
            mock_menu.addMenu.return_value = mock_submenu
            mock_menu.isEmpty.return_value = False
            key_action = MagicMock()
            new_var_action = MagicMock()
            mock_submenu.addAction.side_effect = [key_action, new_var_action]
            mock_menu.addAction.side_effect = lambda _label: MagicMock()

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            _trigger_connected(key_action)
            assert received == [("API_KEY", "my-value")]
        finally:
            view.close()

    def test_new_variable_selection_emits_none_key(self, qapp):
        view = ResponseView()
        try:
            view.set_env_keys([])
            view.body_view.setPlainText("fresh")
            _select_text(view, "fresh")

            received = []
            view.variable_set_requested.connect(
                lambda key, value: received.append((key, value))
            )

            mock_menu = MagicMock()
            mock_submenu = MagicMock()
            mock_menu.addMenu.return_value = mock_submenu
            mock_menu.isEmpty.return_value = False
            new_var_action = MagicMock()
            mock_submenu.addAction.return_value = new_var_action
            mock_menu.addAction.side_effect = lambda _label: MagicMock()

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            _trigger_connected(new_var_action)
            assert received == [(None, "fresh")]
        finally:
            view.close()

    def test_copy_action_wires_body_view_copy(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("copy-me")
            _select_text(view, "copy-me")

            mock_menu = MagicMock()
            mock_menu.isEmpty.return_value = True
            copy_action = MagicMock()
            select_all_action = MagicMock()
            mock_menu.addAction.side_effect = lambda label: {
                "Copy": copy_action,
                "Select All": select_all_action,
            }[label]

            with patch(_QMENU_PATCH, return_value=mock_menu):
                with patch.object(view.body_view, "copy") as mock_copy:
                    view.show_context_menu(QPoint(0, 0))
                    _trigger_connected(copy_action)
                    mock_copy.assert_called_once()
        finally:
            view.close()

    def test_select_all_action_wires_body_view_select_all(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("all text")

            mock_menu = MagicMock()
            mock_menu.isEmpty.return_value = True
            select_all_action = MagicMock()
            mock_menu.addAction.return_value = select_all_action

            with patch(_QMENU_PATCH, return_value=mock_menu):
                with patch.object(view.body_view, "selectAll") as mock_select_all:
                    view.show_context_menu(QPoint(0, 0))
                    _trigger_connected(select_all_action)
                    mock_select_all.assert_called_once()
        finally:
            view.close()

    def test_whitespace_only_selection_skips_set_variable(self, qapp):
        view = ResponseView()
        try:
            view.set_env_keys(["API_KEY"])
            view.body_view.setPlainText("   ")
            cursor = view.body_view.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            view.body_view.setTextCursor(cursor)

            mock_menu = MagicMock()
            mock_menu.isEmpty.return_value = True
            select_all_action = MagicMock()
            mock_menu.addAction.return_value = select_all_action

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            mock_menu.addMenu.assert_not_called()
        finally:
            view.close()
