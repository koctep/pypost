import logging
from unittest.mock import MagicMock, patch

import pytest

from pypost.core.mcp_server_registry import McpServerStatus
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import McpServerConfiguration
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog, _McpServerEditor

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
def test_server_dialog_displays_identity_state_and_bindings():
    configuration = McpServerConfiguration(
        id="server-1",
        name="Jira tools",
        port=1081,
        collection_id="collection-1",
        environment_id="environment-1",
        enabled=True,
    )
    dialog = McpServersDialog(
        configurations=lambda: [configuration],
        status_for=lambda _id: McpServerStatus("server-1", "running"),
        save=lambda _configuration: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [Collection(id="collection-1", name="Jira")],
        environments=lambda: [Environment(id="environment-1", name="Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
    )

    assert dialog._table.rowCount() == 1
    assert dialog._table.item(0, 1).text() == "server-1"
    assert dialog._table.item(0, 2).text() == "running"
    assert dialog._table.item(0, 3).text() == "127.0.0.1:1081"
    assert dialog._table.item(0, 4).text() == "Jira"
    assert dialog._table.item(0, 5).text() == "Cloud"


@pytest.mark.usefixtures("qapp")
def test_server_dialog_renders_busy_port_failure_message_in_error_column_and_tooltip():
    configuration = McpServerConfiguration(
        id="server-1", port=1081, collection_id="collection-1", environment_id="environment-1"
    )
    bind_error = "server-1 on port 1081: [Errno 98] Address already in use"
    dialog = McpServersDialog(
        configurations=lambda: [configuration],
        status_for=lambda _id: McpServerStatus("server-1", "failed", bind_error),
        save=lambda _configuration: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [Collection(id="collection-1", name="Jira")],
        environments=lambda: [Environment(id="environment-1", name="Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
    )

    assert dialog._table.item(0, 6).text() == bind_error
    assert dialog._table.item(0, 2).toolTip() == bind_error


@pytest.mark.usefixtures("qapp")
def test_editor_requires_collection_and_environment():
    editor = _McpServerEditor(
        collections=[],
        environments=[],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
    )

    editor._accept_if_complete()

    assert "required" in editor._error.text()
    assert editor.result() == 0


@pytest.mark.usefixtures("qapp")
def test_legacy_conversion_preselects_legacy_environment():
    legacy = Environment(id="legacy-env", name="Legacy", enable_mcp=True)
    editor = _McpServerEditor(
        collections=[Collection(id="collection-1", name="Jira")],
        environments=[legacy],
        configuration=None,
        default_environment=legacy,
        default_host="0.0.0.0",
        default_port=1082,
    )

    configuration = editor.configuration()

    assert configuration.environment_id == "legacy-env"
    assert configuration.host == "0.0.0.0"
    assert configuration.port == 1082


@pytest.mark.usefixtures("qapp")
def test_server_dialog_routes_start_and_stop_by_selected_server_id():
    configuration = McpServerConfiguration(
        id="server-1", port=1081, collection_id="collection-1", environment_id="environment-1"
    )
    started, stopped = [], []
    dialog = McpServersDialog(
        configurations=lambda: [configuration],
        status_for=lambda _id: McpServerStatus(_id, "stopped"),
        save=lambda _configuration: None,
        remove=lambda _id: None,
        start=started.append,
        stop=stopped.append,
        activity=lambda _id: [],
        collections=lambda: [Collection(id="collection-1", name="Jira")],
        environments=lambda: [Environment(id="environment-1", name="Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
    )
    dialog._table.selectRow(0)

    dialog._operate(dialog._start)
    dialog._operate(dialog._stop)

    assert started == ["server-1"]
    assert stopped == ["server-1"]


@pytest.mark.usefixtures("qapp")
def test_server_dialog_surfaces_duplicate_port_validation_error():
    dialog = McpServersDialog(
        configurations=lambda: [],
        status_for=lambda _id: McpServerStatus(_id, "stopped"),
        save=lambda _configuration: (_ for _ in ()).throw(
            ValueError("MCP server port 1080 is already used by server-1")
        ),
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [Collection(id="collection-1", name="Jira")],
        environments=lambda: [Environment(id="environment-1", name="Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
    )
    editor = MagicMock()
    editor.exec.return_value = True
    editor.configuration.return_value = McpServerConfiguration(
        id="server-2", port=1080, collection_id="collection-1", environment_id="environment-1"
    )

    with (
        patch("pypost.ui.dialogs.mcp_servers_dialog._McpServerEditor", return_value=editor),
        patch.object(dialog, "_show_error") as show_error,
    ):
        dialog._add()

    show_error.assert_called_once_with("MCP server port 1080 is already used by server-1")


@pytest.mark.usefixtures("qapp")
def test_server_dialog_shows_tools_from_the_selected_collection_only():
    selected_collection = Collection(
        id="collection-1",
        name="Jira",
        requests=[RequestData(id="jira-tool", name="Jira Tool", expose_as_mcp=True)],
    )
    other_collection = Collection(
        id="collection-2",
        name="Other",
        requests=[RequestData(id="other-tool", name="Other Tool", expose_as_mcp=True)],
    )
    configuration = McpServerConfiguration(
        id="server-1", port=1081, collection_id="collection-1", environment_id="environment-1"
    )
    dialog = McpServersDialog(
        configurations=lambda: [configuration],
        status_for=lambda _id: McpServerStatus(_id, "stopped"),
        save=lambda _configuration: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [selected_collection, other_collection],
        environments=lambda: [Environment(id="environment-1", name="Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
    )
    dialog._table.selectRow(0)

    with patch("pypost.ui.dialogs.mcp_servers_dialog.McpToolsOverviewDialog") as overview:
        dialog._show_tools()

    entries = overview.call_args.args[0]
    assert [entry.request_name for entry in entries] == ["Jira Tool"]
    overview.return_value.setWindowTitle.assert_called_once_with("MCP Tools — server-1")


@pytest.mark.usefixtures("qapp")
def test_server_dialog_observability_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Ensure McpServersDialog logs configuration additions without leaking secrets."""
    with caplog.at_level(logging.INFO, logger="pypost.ui.dialogs.mcp_servers_dialog"):
        saved = []
        dialog = McpServersDialog(
            configurations=lambda: [],
            status_for=lambda _id: McpServerStatus(_id, "stopped"),
            save=saved.append,
            remove=lambda _id: None,
            start=lambda _id: None,
            stop=lambda _id: None,
            activity=lambda _id: [],
            collections=lambda: [Collection(id="col-1", name="Jira")],
            environments=lambda: [Environment(id="env-1", name="Cloud")],
            legacy_environment=lambda: None,
            legacy_host="127.0.0.1",
            legacy_port=1080,
        )
        editor = MagicMock()
        editor.exec.return_value = True
        editor.configuration.return_value = McpServerConfiguration(
            id="server-obs",
            name="Observability Test Server",
            port=1090,
            server_type="proxy",
            upstream_url="http://127.0.0.1:8080/mcp",
            headers={"Authorization": "Bearer supersecret123"},
            environment_id="env-1",
        )
        with patch(
            "pypost.ui.dialogs.mcp_servers_dialog._McpServerEditor",
            return_value=editor,
        ):
            dialog._add()

        assert any(
            "Adding new MCP server: id=server-obs" in r.message for r in caplog.records
        )
        # Verify secret token value is not logged
        assert not any("supersecret123" in r.message for r in caplog.records)

