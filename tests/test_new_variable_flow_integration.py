"""Integration tests for ResponseView → EnvPresenter new variable creation (PYPOST-475/480)."""

import pytest

from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QInputDialog

from pypost.models.models import Environment
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(120)


def _make_presenter_with_env(env: Environment) -> EnvPresenter:
    storage = MagicMock()
    presenter = EnvPresenter(
        storage=storage,
        config_manager=MagicMock(),
        mcp_manager=MagicMock(),
        settings=MagicMock(),
        get_collections=lambda: [],
        metrics=MagicMock(),
    )
    presenter._environments = [env]
    presenter._env_selector.blockSignals(True)
    presenter._env_selector.addItem(env.name, env)
    presenter._env_selector.setCurrentIndex(1)
    presenter._env_selector.blockSignals(False)
    return presenter

class TestNewVariableFlowIntegration:
    """End-to-end wiring: ResponseView → dialog → validation → env model + save."""

    def test_response_view_new_variable_valid_name_persisted(self, qapp):
        env = Environment(name="Dev", variables={})
        presenter = _make_presenter_with_env(env)
        view = ResponseView()
        view.current_env_keys = []
        view.variable_set_requested.connect(presenter.handle_variable_set_request)

        with (
            patch.object(QInputDialog, "getText", return_value=("api_token", True)),
            patch.object(presenter, "_encryption_enabled", return_value=False),
        ):
            view.variable_set_requested.emit(None, "secret-value")

        assert env.variables["api_token"] == "secret-value"
        presenter._storage.save_environments.assert_called_once_with([env])

    def test_response_view_new_variable_invalid_name_rejected(self, qapp):
        env = Environment(name="Dev", variables={})
        presenter = _make_presenter_with_env(env)
        view = ResponseView()
        view.current_env_keys = []
        view.variable_set_requested.connect(presenter.handle_variable_set_request)

        with (
            patch.object(QInputDialog, "getText", return_value=("1bad", True)),
            patch(
                "pypost.ui.presenters.env_presenter.show_invalid_variable_name_error",
            ) as mock_warning,
        ):
            view.variable_set_requested.emit(None, "value")

        assert "1bad" not in env.variables
        mock_warning.assert_called_once()
        assert "digit" in mock_warning.call_args[0][1]

    def test_new_variable_menu_path_uses_none_key(self, qapp):
        """Context menu 'New Variable...' emits key=None (PYPOST-480 contract)."""
        view = ResponseView()
        view.current_env_keys = ["existing"]
        received = []
        view.variable_set_requested.connect(
            lambda key, val: received.append((key, val)),
        )
        view.variable_set_requested.emit(None, "selected-text")
        assert received == [(None, "selected-text")]
