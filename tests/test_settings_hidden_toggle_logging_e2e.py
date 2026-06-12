"""PYPOST-490: settings → apply_settings → env manager → toggle log (PYPOST-448 debt)."""


import pytest

pytestmark = pytest.mark.timeout(120)

import logging
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from pypost.ui.presenters.env_presenter import EnvPresenter

from tests.test_env_presenter import FakeConfigManager, FakeMCPManager, FakeStorage

ENV_NAME = "Dev"
VARIABLE_KEY = "API_KEY"
VARIABLE_VALUE = "secret"


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _settings_after_accept(current: AppSettings, *, log_hidden_key_names: bool) -> AppSettings:
    dlg = SettingsDialog(current)
    dlg.log_hidden_key_names_check.setChecked(log_hidden_key_names)
    dlg.accept()
    return dlg.get_settings()


def _make_env_presenter() -> EnvPresenter:
    env = Environment(
        id="e1",
        name=ENV_NAME,
        variables={VARIABLE_KEY: VARIABLE_VALUE},
    )
    storage = FakeStorage([env])
    config = FakeConfigManager()
    mcp = FakeMCPManager()
    mcp.status_changed = MagicMock()
    mcp.status_changed.connect = MagicMock()
    presenter = EnvPresenter(
        storage,
        config,
        mcp,
        AppSettings(),
        lambda: [],
        MagicMock(),
    )
    presenter.load_environments()
    presenter.env_selector.setCurrentIndex(1)
    return presenter


def _make_integration_window(qapp, env_presenter):  # noqa: ARG001
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
        patch("pypost.ui.main_window.EnvPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow

        window = MainWindow(metrics=metrics, template_service=template_service)
    window.env = env_presenter
    window.collections = mock_collections
    window.tabs = mock_tabs
    window.settings_btn = MagicMock()
    mock_tabs.widget.tabBar.return_value = MagicMock()
    return window


def _toggle_hidden_during_exec(dialog: EnvironmentDialog, caplog) -> None:
    dialog.on_env_selected(0)
    hidden_cb = dialog._get_hidden_checkbox(0)
    assert hidden_cb is not None
    with caplog.at_level(logging.INFO):
        hidden_cb.setChecked(True)


def _patch_env_dialog_exec(caplog):
    def exec_and_toggle(self):
        _toggle_hidden_during_exec(self, caplog)
        return 0

    return patch.object(EnvironmentDialog, "exec", exec_and_toggle)


def _assert_no_value_leak(caplog) -> None:
    assert not any(VARIABLE_VALUE in r.message for r in caplog.records)


def _run_settings_to_toggle_chain(
    qapp,
    caplog,
    *,
    log_hidden_key_names: bool,
) -> None:
    presenter = _make_env_presenter()
    new_settings = _settings_after_accept(
        AppSettings(),
        log_hidden_key_names=log_hidden_key_names,
    )
    window = _make_integration_window(qapp, presenter)
    with patch.object(window.style_manager, "apply_styles"):
        window.apply_settings(new_settings)
    with _patch_env_dialog_exec(caplog):
        presenter._open_env_manager()


def test_default_masked_toggle_log_after_settings_apply(qapp, caplog):
    # Journey: Settings (default) → apply_settings → open env manager → toggle hidden.
    _run_settings_to_toggle_chain(qapp, caplog, log_hidden_key_names=False)
    assert any(
        f"env_hidden_flag_changed env_name={ENV_NAME} key=******** hidden=True" in r.message
        for r in caplog.records
    )
    assert not any(VARIABLE_KEY in r.message for r in caplog.records)
    _assert_no_value_leak(caplog)


def test_readable_toggle_log_when_settings_opt_in(qapp, caplog):
    # Journey: Settings (opt-in) → apply_settings → open env manager → toggle hidden.
    _run_settings_to_toggle_chain(qapp, caplog, log_hidden_key_names=True)
    assert any(
        f"env_hidden_flag_changed env_name={ENV_NAME} key={VARIABLE_KEY} hidden=True" in r.message
        for r in caplog.records
    )
    _assert_no_value_leak(caplog)
