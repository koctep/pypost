"""PYPOST-509: MainWindow defers tab/tree restore until async env load completes."""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from pypost.models.settings import AppSettings


class _DeferredEnvPresenter(QObject):
    environments_loaded = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.widget = MagicMock()
        self.wait_storage_idle = MagicMock(return_value=True)

    def load_environments(self) -> None:
        return


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _make_encrypted_startup_window(qapp, mock_env):  # noqa: ARG001
    metrics = MagicMock()
    template_service = MagicMock()
    mock_tabs = MagicMock()
    mock_collections = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.main_window.MCPServerManager"),
        patch("pypost.ui.main_window.HistoryManager"),
        patch("pypost.ui.main_window.CollectionsPresenter", return_value=mock_collections),
        patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
        patch("pypost.ui.main_window.EnvPresenter", return_value=mock_env),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.MainWindow._wire_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
        patch("pypost.ui.main_window.resolve_encryption_enabled", return_value=True),
    ):
        mock_sm.return_value.settings = AppSettings(env_encryption_enabled=True)
        from pypost.ui.main_window import MainWindow

        window = MainWindow(metrics=metrics, template_service=template_service)
    window.settings_btn = MagicMock()
    return window, mock_tabs, mock_collections


def test_encrypted_startup_defers_restore_until_environments_loaded(qapp):
    mock_env = _DeferredEnvPresenter()
    window, mock_tabs, mock_collections = _make_encrypted_startup_window(qapp, mock_env)

    mock_tabs.restore_tabs.assert_not_called()
    mock_collections.restore_tree_state.assert_not_called()

    mock_env.environments_loaded.emit()

    mock_tabs.restore_tabs.assert_called_once()
    mock_collections.restore_tree_state.assert_called_once()
