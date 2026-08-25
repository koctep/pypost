"""Failing repro / acceptance tests for PYPOST-1143.

Verifies WebSocketPresenter exposes public read-only env_vars and hidden_keys
properties and that WebSocketComposer / WebSocketStreamView no longer use
private-attribute getattr fallbacks.
"""

from __future__ import annotations

import inspect

import pytest

from pypost.models.websocket import WebSocketConnection
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.widgets.websocket import composer as composer_module
from pypost.ui.widgets.websocket import stream_view as stream_view_module

pytestmark = pytest.mark.timeout(10)


def _make_presenter(
    env_vars: dict[str, str] | None = None,
    hidden_keys: set[str] | None = None,
) -> WebSocketPresenter:
    conn = WebSocketConnection(name="test", url="ws://localhost/test")
    return WebSocketPresenter(
        connection=conn,
        env_vars=env_vars or {"HOST": "localhost"},
        hidden_keys=hidden_keys or {"SECRET"},
    )


class TestWebSocketPresenterEnvProperties:
    """Public env_vars and hidden_keys properties on WebSocketPresenter."""

    def test_env_vars_property_returns_initial_snapshot(self) -> None:
        presenter = _make_presenter(
            env_vars={"API_KEY": "abc", "HOST": "example.com"},
            hidden_keys=set(),
        )
        assert presenter.env_vars == {"API_KEY": "abc", "HOST": "example.com"}

    def test_hidden_keys_property_returns_initial_snapshot(self) -> None:
        presenter = _make_presenter(
            env_vars={},
            hidden_keys={"API_KEY", "TOKEN"},
        )
        assert presenter.hidden_keys == {"API_KEY", "TOKEN"}

    def test_setters_update_public_properties(self) -> None:
        presenter = _make_presenter()
        presenter.set_variables({"NEW": "value"})
        presenter.set_hidden_keys({"NEW"})
        assert presenter.env_vars == {"NEW": "value"}
        assert presenter.hidden_keys == {"NEW"}

    def test_properties_return_defensive_copies(self) -> None:
        presenter = _make_presenter(
            env_vars={"X": "1"},
            hidden_keys={"X"},
        )
        env_copy = presenter.env_vars
        keys_copy = presenter.hidden_keys
        env_copy["Y"] = "2"
        keys_copy.add("Y")
        assert presenter.env_vars == {"X": "1"}
        assert presenter.hidden_keys == {"X"}


class TestConsumerModulesUsePublicProperties:
    """Child widgets must not getattr private presenter attributes."""

    def test_composer_does_not_getattr_private_env_vars(self) -> None:
        source = inspect.getsource(composer_module.WebSocketComposer.send_current_payload)
        assert 'getattr(self.presenter, "_env_vars"' not in source
        assert "presenter.env_vars" in source

    def test_stream_view_export_does_not_getattr_private_env(self) -> None:
        json_source = inspect.getsource(stream_view_module.WebSocketStreamView.export_json)
        text_source = inspect.getsource(stream_view_module.WebSocketStreamView.export_text)
        for source in (json_source, text_source):
            assert 'getattr(self.presenter, "_env_vars"' not in source
            assert 'getattr(self.presenter, "_hidden_keys"' not in source
            assert "presenter.env_vars" in source
            assert "presenter.hidden_keys" in source
