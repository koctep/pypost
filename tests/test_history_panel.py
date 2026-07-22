import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication, QSizePolicy

from pypost.ui.widgets.history_panel import HistoryPanel
from pypost.models.models import HistoryEntry

@pytest.mark.usefixtures("qapp")

class TestHistoryPanel(unittest.TestCase):
    def test_history_panel_copy_as_curl_shortcut(self):
        history_manager = MagicMock()
        entry = HistoryEntry(
            id="1",
            method="GET",
            url="https://api.example.com",
            headers={"Host": "example.com"},
            body="",
            status_code=200,
            response_time_ms=10,
            timestamp="2023-01-01T12:00:00Z",
        )
        history_manager.get_entries.return_value = [entry]

        panel = HistoryPanel(history_manager=history_manager)

        # Ensure list widget is populated
        self.assertEqual(panel._list_widget.count(), 1)
        panel._list_widget.setCurrentRow(0)

        with patch("pypost.ui.widgets.history_panel.CurlGenerator.generate_from_history") as mock_generate:
            mock_generate.return_value = "curl -X GET https://api.example.com"
            
            received = []
            panel.curl_copied.connect(lambda: received.append(True))
            
            panel._copy_shortcut.activated.emit()
            
            mock_generate.assert_called_once_with(entry)
            self.assertEqual(QApplication.clipboard().text(), "curl -X GET https://api.example.com")
            self.assertEqual(len(received), 1)

    def test_history_panel_copy_as_curl_context_menu(self):
        history_manager = MagicMock()
        entry = HistoryEntry(
            id="2",
            method="POST",
            url="https://api.example.com",
            headers={"Content-Type": "application/json"},
            body="test",
            status_code=201,
            response_time_ms=20,
            timestamp="2023-01-01T12:00:00Z",
        )
        history_manager.get_entries.return_value = [entry]

        panel = HistoryPanel(history_manager=history_manager)

        self.assertEqual(panel._list_widget.count(), 1)
        panel._list_widget.setCurrentRow(0)

        with patch("pypost.ui.widgets.history_panel.QMenu") as mock_menu_class:
            mock_action_copy = MagicMock()
            mock_action_delete = MagicMock()
            mock_menu_instance = mock_menu_class.return_value
            
            # Make the menu return our mock action when exec is called
            mock_menu_instance.exec.return_value = mock_action_copy
            mock_menu_instance.addAction.side_effect = [mock_action_copy, mock_action_delete]
            
            with patch.object(panel, "_copy_as_curl") as mock_copy_method:
                panel._on_context_menu(QPoint(0, 0))
                mock_copy_method.assert_called_once()

    def test_selected_entry_lookup_by_id_index(self):
        history_manager = MagicMock()
        entries = [
            HistoryEntry(
                id="a",
                method="GET",
                url="https://example.com/a",
                headers={},
                body="",
                status_code=200,
                response_time_ms=10,
                timestamp="2023-01-01T12:00:00Z",
            ),
            HistoryEntry(
                id="b",
                method="POST",
                url="https://example.com/b",
                headers={},
                body="payload",
                status_code=201,
                response_time_ms=20,
                timestamp="2023-01-01T13:00:00Z",
            ),
        ]
        history_manager.get_entries.return_value = entries

        panel = HistoryPanel(history_manager=history_manager)
        self.assertEqual(panel._list_widget.count(), 2)

        panel._list_widget.setCurrentRow(1)
        self.assertIs(panel._selected_entry(), entries[1])

        history_manager.get_entries.return_value = [entries[0]]
        panel.refresh()
        panel._list_widget.setCurrentRow(0)
        self.assertIs(panel._selected_entry(), entries[0])

    def test_detail_fields_use_expanding_layout(self):
        history_manager = MagicMock()
        history_manager.get_entries.return_value = []

        panel = HistoryPanel(history_manager=history_manager)

        for field in (panel._detail_headers, panel._detail_body):
            policy = field.sizePolicy()
            self.assertEqual(
                policy.verticalPolicy(), QSizePolicy.Policy.Expanding
            )
            self.assertGreater(field.minimumHeight(), 0)
            self.assertEqual(field.maximumHeight(), 16777215)

if __name__ == "__main__":
    unittest.main()
