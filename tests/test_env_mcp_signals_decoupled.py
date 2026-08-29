"""Contract and repro tests for decoupling Environment-to-MCP state propagation
with domain Qt signals (PYPOST-1108).

Asserts that:
1. EnvPresenter defines domain Qt signals:
   - environment_selected (payload: Environment | None)
   - environment_updated (payload: str)
   - environment_manager_closed (payload: None)
2. EnvPresenter emits environment_selected on selection and deselection.
3. EnvPresenter emits environment_updated on script/manual variable updates.
4. EnvPresenter emits environment_manager_closed when the Environment dialog closes.
5. EnvPresenter does NOT directly invoke operational methods on McpControlsPresenter.
6. main_window_signals.wire_presenter_signals connects window.env domain signals
   to window.mcp_controls target slots.
7. McpControlsPresenter defines on_environment_manager_closed slot.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QWidget

from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.main_window_signals import wire_presenter_signals
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.presenters.mcp_controls_presenter import McpControlsPresenter

pytestmark = pytest.mark.timeout(60)


@pytest.fixture(autouse=True)
def _prevent_blocking_dialogs():
    """Ensure message boxes never block test execution."""
    with patch("pypost.ui.presenters.env_presenter.show_no_environment_selected"), \
         patch("pypost.ui.presenters.env_presenter.show_invalid_variable_name_error"):
        yield


def _make_env(
    env_id: str,
    name: str,
    variables: dict[str, str] | None = None,
    enable_mcp: bool = False,
) -> Environment:
    return Environment(
        id=env_id,
        name=name,
        variables=variables or {},
        enable_mcp=enable_mcp,
    )


class _FakeStorage:
    def __init__(self, environments: list[Environment] | None = None) -> None:
        self._environments = environments or []
        self.saved: list[list[Environment]] = []

    def load_environments(self) -> list[Environment]:
        return list(self._environments)

    def save_environments(self, envs: list[Environment]) -> None:
        self.saved.append(list(envs))

    def serialize_environment_records(
        self,
        environments: list[Environment],
        *,
        target_envelope_version: int | None = None,
    ) -> list[dict]:
        return [env.model_dump(mode="json") for env in environments]


class _FakeConfigManager:
    def __init__(self) -> None:
        self.saved: list[AppSettings] = []

    def save_config(self, settings: AppSettings) -> None:
        self.saved.append(settings)


def _make_presenter(environments: list[Environment] | None = None) -> EnvPresenter:
    storage = _FakeStorage(environments)
    config = _FakeConfigManager()
    mcp = MagicMock()
    settings = AppSettings()
    metrics = MagicMock()
    return EnvPresenter(
        storage=storage,
        config_manager=config,
        mcp_manager=mcp,
        settings=settings,
        get_collections=lambda: [],
        metrics=metrics,
    )


def test_env_presenter_defines_domain_signals() -> None:
    """EnvPresenter must define environment_selected, environment_updated,
    and environment_manager_closed.
    """
    assert hasattr(EnvPresenter, "environment_selected"), (
        "EnvPresenter must define environment_selected Qt signal"
    )
    assert hasattr(EnvPresenter, "environment_updated"), (
        "EnvPresenter must define environment_updated Qt signal"
    )
    assert hasattr(EnvPresenter, "environment_manager_closed"), (
        "EnvPresenter must define environment_manager_closed Qt signal"
    )


def test_env_presenter_emits_environment_selected_signal(qapp) -> None:
    """EnvPresenter must emit environment_selected with Environment on select, None on deselect."""
    env1 = _make_env("e1", "Env1", {"K": "V"})
    p = _make_presenter([env1])
    try:
        p.load_environments()

        assert hasattr(p, "environment_selected"), (
            "EnvPresenter instance missing environment_selected signal"
        )
        spy = MagicMock()
        p.environment_selected.connect(spy)

        p._env_selector.setCurrentIndex(1)
        spy.assert_called_with(env1)

        spy.reset_mock()
        p._env_selector.setCurrentIndex(0)
        spy.assert_called_with(None)
    finally:
        p.widget.deleteLater()


def test_env_presenter_emits_environment_updated_signal(qapp) -> None:
    """EnvPresenter must emit environment_updated(env_id) on script updates and variable sets."""
    env1 = _make_env("e1", "Env1", {"K": "V"})
    p = _make_presenter([env1])
    try:
        p.load_environments()
        p._env_selector.setCurrentIndex(1)

        assert hasattr(p, "environment_updated"), (
            "EnvPresenter instance missing environment_updated signal"
        )
        spy = MagicMock()
        p.environment_updated.connect(spy)

        p.on_env_update({"API_KEY": "new_secret"})
        spy.assert_called_with("e1")

        spy.reset_mock()
        p.handle_variable_set_request("MANUAL_KEY", "value")
        spy.assert_called_with("e1")
    finally:
        p.widget.deleteLater()


def test_env_presenter_emits_environment_manager_closed_signal(qapp) -> None:
    """EnvPresenter must emit environment_manager_closed when EnvironmentDialog closes."""
    env1 = _make_env("e1", "Env1")
    p = _make_presenter([env1])
    try:
        p.load_environments()

        assert hasattr(p, "environment_manager_closed"), (
            "EnvPresenter instance missing environment_manager_closed signal"
        )
        spy = MagicMock()
        p.environment_manager_closed.connect(spy)

        with patch("pypost.ui.presenters.env_presenter.EnvironmentDialog") as mock_dlg_cls:
            mock_dlg = mock_dlg_cls.return_value
            mock_dlg.environments = p._environments
            mock_dlg.exec.return_value = 0
            p._open_env_manager()

        spy.assert_called_once_with()
    finally:
        p.widget.deleteLater()


def test_env_presenter_does_not_directly_invoke_mcp_controls(qapp) -> None:
    """EnvPresenter must NOT call operational methods directly on _mcp_controls."""
    env1 = _make_env("e1", "Env1", {"K": "V"})
    p = _make_presenter([env1])
    try:
        p.load_environments()
        mock_mcp_controls = MagicMock()
        mock_mcp_controls.legacy_server_running.return_value = False
        p._mcp_controls = mock_mcp_controls

        # 1. Select environment
        p._env_selector.setCurrentIndex(1)
        # 2. Update variables via script
        p.on_env_update({"A": "B"})
        # 3. Update variable manually while environment is active
        p.handle_variable_set_request("KEY", "VAL")
        # 4. Deselect environment
        p._env_selector.setCurrentIndex(0)
        # 5. Open environment manager
        with patch("pypost.ui.presenters.env_presenter.EnvironmentDialog") as mock_dlg_cls:
            mock_dlg = mock_dlg_cls.return_value
            mock_dlg.environments = p._environments
            mock_dlg.exec.return_value = 0
            p._open_env_manager()

        mock_mcp_controls.handle_environment_selected.assert_not_called()
        mock_mcp_controls.refresh_environment.assert_not_called()
        mock_mcp_controls.reconcile_references.assert_not_called()
        mock_mcp_controls.track_active_env_changed.assert_not_called()
        mock_mcp_controls.refresh_tools_button.assert_not_called()
        mock_mcp_controls.legacy_server_running.assert_not_called()
    finally:
        p.widget.deleteLater()


def test_wire_presenter_signals_connects_env_domain_signals_to_mcp_controls() -> None:
    """wire_presenter_signals must connect env domain signals to mcp_controls slots."""
    window = MagicMock()
    wire_presenter_signals(window)

    window.env.environment_selected.connect.assert_any_call(
        window.mcp_controls.handle_environment_selected
    )
    window.env.environment_updated.connect.assert_any_call(
        window.mcp_controls.refresh_environment
    )
    window.env.environment_manager_closed.connect.assert_any_call(
        window.mcp_controls.on_environment_manager_closed
    )


def test_mcp_controls_presenter_defines_on_environment_manager_closed_slot() -> None:
    """McpControlsPresenter must expose on_environment_manager_closed slot."""
    assert hasattr(McpControlsPresenter, "on_environment_manager_closed"), (
        "McpControlsPresenter must expose on_environment_manager_closed slot"
    )


def test_env_presenter_signal_emission_logging(qapp, caplog) -> None:
    """EnvPresenter emits debug logs on domain signals without leaking secrets."""
    secret_value = "super_secret_token_xyz"
    env1 = _make_env("e1", "Env1", {"API_KEY": secret_value})
    p = _make_presenter([env1])
    try:
        with caplog.at_level(logging.DEBUG):
            p.load_environments()
            p._env_selector.setCurrentIndex(1)
            assert "environment_selected_emitted env_id=e1" in caplog.text

            p.on_env_update({"TOKEN": secret_value})
            assert "environment_updated_emitted env_id=e1 source=script" in caplog.text

            p.handle_variable_set_request("OTHER_KEY", secret_value)
            assert "environment_updated_emitted env_id=e1 source=manual_set" in caplog.text

            with patch("pypost.ui.presenters.env_presenter.EnvironmentDialog") as mock_dlg_cls:
                mock_dlg = mock_dlg_cls.return_value
                mock_dlg.environments = p._environments
                mock_dlg.exec.return_value = 0
                p._open_env_manager()
            assert "environment_manager_closed_emitted" in caplog.text

            # Ensure secret values are never logged
            assert secret_value not in caplog.text
    finally:
        p.widget.deleteLater()


def test_mcp_controls_slot_handling_logging(qapp, caplog) -> None:
    """McpControlsPresenter logs debug events on slot invocations."""
    manager = MagicMock()
    manager.is_running.return_value = False
    settings = AppSettings()
    metrics = MagicMock()
    env = _make_env("e1", "Env1", enable_mcp=False)

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [env],
        current_environment=lambda: env,
        metrics=metrics,
        dialog_parent=QWidget(),
    )
    try:
        with caplog.at_level(logging.DEBUG):
            presenter.handle_environment_selected(env)
            assert "mcp_handle_environment_selected env_id=e1 mcp_enabled=False" in caplog.text

            presenter.refresh_environment("e1")
            assert "mcp_refresh_environment env_id=e1" in caplog.text

            presenter.reconcile_references()
            assert "mcp_reconcile_references" in caplog.text

            presenter.on_environment_manager_closed()
            assert "mcp_on_environment_manager_closed" in caplog.text
    finally:
        presenter._dialog_parent.deleteLater()


def test_wire_presenter_signals_logs_completion(caplog) -> None:
    """wire_presenter_signals logs start and completion events at DEBUG level."""
    window = MagicMock()
    with caplog.at_level(logging.DEBUG):
        wire_presenter_signals(window)
    assert "wire_presenter_signals_started" in caplog.text
    assert "wire_presenter_signals_completed" in caplog.text

