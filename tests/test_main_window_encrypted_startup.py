"""PYPOST-509 / PYPOST-754: MainWindow defers tab/tree restore until async loads complete."""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QObject, Signal

from pypost.models.settings import AppSettings


pytestmark = pytest.mark.timeout(120)


class _DeferredEnvPresenter(QObject):
    environments_loaded = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.widget = MagicMock()
        self.mcp_controls = MagicMock()
        self.wait_storage_idle = MagicMock(return_value=True)

    def load_environments(self) -> None:
        return


class _DeferredCollectionsPresenter(QObject):
    collections_loaded = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.restore_tree_state = MagicMock()

    def load_collections_async(self) -> None:
        return


def _make_encrypted_startup_window(qapp, mock_env, mock_collections):  # noqa: ARG001
    metrics = MagicMock()
    template_service = MagicMock()
    mock_tabs = MagicMock()
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.mcp_server_controller.MCPServerManager"),
        patch("pypost.ui.main_window.CollectionsPresenter", return_value=mock_collections),
        patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
        patch("pypost.ui.main_window.EnvPresenter", return_value=mock_env),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
    ):
        mock_sm.return_value.settings = AppSettings(env_encryption_enabled=True)
        from pypost.ui.main_window import MainWindow

        window = MainWindow(
            metrics=metrics,
            template_service=template_service,
            config_manager=MagicMock(recovery_notice=None),
            settings=mock_sm.return_value.settings,
            state_manager=mock_sm.return_value,
            history_manager=MagicMock(),
            storage=MagicMock(),
            request_manager=MagicMock(),
            mcp_controller=MagicMock(),
            alert_manager_factory=MagicMock(),
        )
    window.settings_btn = MagicMock()
    return window, mock_tabs, mock_collections


def test_encrypted_startup_defers_restore_until_both_loads_complete(qapp):
    mock_env = _DeferredEnvPresenter()
    mock_collections = _DeferredCollectionsPresenter()
    window, mock_tabs, mock_collections_mock = _make_encrypted_startup_window(
        qapp, mock_env, mock_collections
    )

    mock_tabs.restore_tabs.assert_not_called()
    mock_collections_mock.restore_tree_state.assert_not_called()

    mock_env.environments_loaded.emit()
    mock_tabs.restore_tabs.assert_not_called()
    mock_collections_mock.restore_tree_state.assert_not_called()

    mock_collections.collections_loaded.emit()

    mock_tabs.restore_tabs.assert_called_once()
    mock_collections_mock.restore_tree_state.assert_called_once()
