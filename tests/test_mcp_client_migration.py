"""PYPOST-1171: Legacy HTTP method MCP migration to MCP Client tab."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from pypost.core.mcp_client_migration import (
    is_legacy_mcp_request,
    request_data_to_mcp_client,
)
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from pypost.ui.widgets.mcp_client import McpClientTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from pypost.ui.widgets.request_editor import RequestWidget

pytestmark = pytest.mark.timeout(60)


class _FakeRequestManager:
    def find_request(self, req_id):
        return None

    def get_collections(self):
        return []


class _FakeStateManager:
    def __init__(self) -> None:
        self.settings = AppSettings()

    def get_open_tabs(self):
        return []

    def set_open_tabs(self, ids):
        pass


@pytest.fixture
def tabs_presenter(qapp) -> TabsPresenter:
    presenter = TabsPresenter(
        _FakeRequestManager(),
        _FakeStateManager(),
        AppSettings(),
        metrics=MagicMock(),
        protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
    )
    yield presenter
    presenter.widget.close()
    presenter.widget.deleteLater()


def test_is_legacy_mcp_request() -> None:
    assert is_legacy_mcp_request(RequestData(method="MCP", url="http://x"))
    assert is_legacy_mcp_request(RequestData(method="mcp", url="http://x"))
    assert not is_legacy_mcp_request(RequestData(method="GET", url="http://x"))


def test_request_data_to_mcp_client_maps_url_headers_name() -> None:
    request = RequestData(
        id="req-1",
        name="List Tools",
        method="MCP",
        url="http://127.0.0.1:1080/mcp",
        headers={"Authorization": "Bearer x"},
    )
    connection = request_data_to_mcp_client(request)
    assert connection.id == "req-1"
    assert connection.name == "List Tools"
    assert connection.url == "http://127.0.0.1:1080/mcp"
    assert connection.headers == {"Authorization": "Bearer x"}
    assert connection.last_tool_name is None
    assert connection.last_tool_arguments == {}


def test_request_data_to_mcp_client_maps_call_tool_body() -> None:
    request = RequestData(
        method="MCP",
        url="http://127.0.0.1:1080/mcp",
        body='{"name": "echo", "arguments": {"message": "hi"}}',
    )
    connection = request_data_to_mcp_client(request)
    assert connection.last_tool_name == "echo"
    assert connection.last_tool_arguments == {"message": "hi"}


def test_method_combo_excludes_mcp(qapp) -> None:
    widget = RequestWidget()
    try:
        items = [
            widget.method_combo.itemText(i)
            for i in range(widget.method_combo.count())
        ]
        assert "MCP" not in items
    finally:
        widget.close()
        widget.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_legacy_mcp_request_opens_client_tab(tabs_presenter: TabsPresenter) -> None:
    request = RequestData(
        id="mcp-list-tools",
        name="List Tools",
        method="MCP",
        url="http://127.0.0.1:1080/mcp",
        headers={"X-Test": "1"},
    )
    tab = tabs_presenter.open_legacy_mcp_request_tab(request, save_state=False)
    assert isinstance(tab, McpClientTab)
    assert tab.connection_data.url == "http://127.0.0.1:1080/mcp"
    assert tab.connection_data.headers == {"X-Test": "1"}
    assert tabs_presenter.widget.currentWidget() is tab


@pytest.mark.usefixtures("qapp")
def test_add_new_tab_routes_legacy_mcp_to_client_tab(tabs_presenter: TabsPresenter) -> None:
    request = RequestData(
        name="List Tools",
        method="MCP",
        url="http://127.0.0.1:1080/mcp",
    )
    tabs_presenter.add_new_tab(request, save_state=False)
    current = tabs_presenter.widget.currentWidget()
    assert isinstance(current, McpClientTab)
    assert current.connection_data.url == "http://127.0.0.1:1080/mcp"
