"""Automated red repro tests for Built-in source in MCP server dialog.

Task: PYPOST-1353 / Epic: PYPOST-1335
Tests acceptance criteria 1 through 6:
1. Built-in source creation and save blocked without environment (AC 1).
2. Built-in source picker and table read-only marker and tooltip (AC 2).
3. Existing workspace and library flows unaffected (AC 3).
4. Legacy pypost-examples row renders as library without bundled marker (AC 4).
5. McpControlsPresenter supplies builtin_view to dialog without
   reconstructing registry (AC 1, AC 6).
6. Edit workflow preselects Built-in source and entry for existing bundled configuration (AC 5).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QWidget

from pypost.core.builtin_collections import BuiltinCollectionEntry, BuiltinCollectionView
from pypost.core.mcp_server_registry import McpServerStatus
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog, _McpServerEditor
from pypost.ui.presenters.mcp_controls_presenter import (
    McpControlsPresenter,
    McpServerController,
)

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def mock_builtin_view() -> BuiltinCollectionView:
    """Provide a mock BuiltinCollectionView with standard curated entries."""
    view = MagicMock(spec=BuiltinCollectionView)
    entries = [
        BuiltinCollectionEntry(
            collection_path="collections/jira_mcp.json",
            environment_path="environments/jira_cloud.json",
            name="Jira Cloud MCP",
            collection_id="jira-cloud-mcp",
            version="2.0.0",
        ),
        BuiltinCollectionEntry(
            collection_path="collections/gitlab_mcp.json",
            environment_path="environments/gitlab.json",
            name="GitLab MCP",
            collection_id="gitlab-mcp",
            version="1.0.0",
        ),
        BuiltinCollectionEntry(
            collection_path="collections/github_mcp.json",
            environment_path="environments/github.json",
            name="GitHub MCP",
            collection_id="github-mcp",
            version="1.0.0",
        ),
    ]
    view.list_entries.return_value = entries
    return view


# ==============================================================================
# AC 1: Built-in source creation and save blocks without environment
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_builtin_source_creation_and_save_blocks_without_environment(
    mock_builtin_view: BuiltinCollectionView,
) -> None:
    """Selecting Built-in requires an environment before save; save produces bundled config."""
    env = Environment(id="env-1", name="Dev Cloud")
    editor = _McpServerEditor(
        collections=[Collection(id="ws-col", name="Workspace Col")],
        environments=[env],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        builtin_view=mock_builtin_view,
    )

    # 1. Assert "Built-in" option exists in _collection_source
    builtin_idx = editor._collection_source.findData("builtin")
    assert builtin_idx >= 0, "Built-in source choice missing from _collection_source combo"

    # Select "Built-in"
    editor._collection_source.setCurrentIndex(builtin_idx)
    editor.show()

    # 2. Assert built-in combo is visible, while workspace and library widgets are hidden
    assert hasattr(editor, "_builtin_collection"), "Editor must have _builtin_collection combo"
    assert editor._builtin_collection.isVisible()
    assert not editor._collection.isVisible()
    assert not editor._library.isVisible()
    assert not editor._library_collection.isVisible()
    assert not editor._library_profile.isVisible()

    # 3. Blocking validation: with no environment selected, save must be blocked
    editor._environment.setCurrentIndex(-1)
    editor._accept_if_complete()
    assert editor.result() == 0, "Save must be blocked when environment is missing"
    assert "required" in editor._error.text().lower()

    # 4. Selecting an environment enables save
    env_idx = editor._environment.findData("env-1")
    assert env_idx >= 0
    editor._environment.setCurrentIndex(env_idx)

    # Pick the Jira Cloud MCP entry
    jira_idx = editor._builtin_collection.findData("collections/jira_mcp.json")
    if jira_idx < 0:
        # Fallback check if full entry object or path was stored as userData
        for i in range(editor._builtin_collection.count()):
            data = editor._builtin_collection.itemData(i)
            match_path = getattr(data, "collection_path", data)
            if match_path == "collections/jira_mcp.json":
                jira_idx = i
                break
    assert jira_idx >= 0, "Jira Cloud MCP must be present in _builtin_collection combo"
    editor._builtin_collection.setCurrentIndex(jira_idx)

    editor._accept_if_complete()
    assert editor.result() == 1, "Save must succeed once environment is selected"

    # 5. Emitting configuration produces bundled MCP server configuration
    config = editor.configuration()
    assert config.server_type == "local"
    assert config.bundled_library is True
    assert config.library_id == "pypost-examples"
    assert config.manifest_id == "pypost-examples"
    assert config.library_collection_path == "collections/jira_mcp.json"
    assert config.collection_id is None
    assert config.environment_id == "env-1"
    assert editor.library_selection() is None, "library_selection() must be None for built-in"


# ==============================================================================
# AC 2: Picker and overview table read-only marker and tooltip
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_builtin_source_picker_and_table_read_only_marker(
    mock_builtin_view: BuiltinCollectionView,
) -> None:
    """Built-in collection picker items and overview table rows display '(read-only)'."""
    editor = _McpServerEditor(
        collections=[Collection(id="ws-col", name="Workspace Col")],
        environments=[Environment(id="env-1", name="Dev Cloud")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        builtin_view=mock_builtin_view,
    )

    # Verify picker items have '(read-only)' marker and informative tooltip
    assert hasattr(editor, "_builtin_collection"), "Editor must have _builtin_collection combo"
    count = editor._builtin_collection.count()
    assert count == 3, f"Expected 3 curated entries, found {count}"

    for i in range(count):
        text = editor._builtin_collection.itemText(i)
        tooltip = editor._builtin_collection.itemData(i, 3)  # Qt.ItemDataRole.ToolTipRole is 3
        assert "(read-only)" in text, f"Item '{text}' missing '(read-only)' marker"
        tooltip_lower = tooltip.lower()
        has_expected_desc = (
            "shipped" in tooltip_lower
            or "upgrade" in tooltip_lower
            or "read-only" in tooltip_lower
        )
        assert has_expected_desc, f"Item '{text}' missing expected description in tooltip"

    # Verify McpServersDialog overview table renders "(read-only)" for bundled rows
    builtin_config = McpServerConfiguration(
        id="srv-builtin",
        name="Jira Server",
        port=1081,
        server_type="local",
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        bundled_library=True,
        collection_id=None,
        environment_id="env-1",
    )
    dialog = McpServersDialog(
        configurations=lambda: [builtin_config],
        status_for=lambda _id: McpServerStatus("srv-builtin", "stopped"),
        save=lambda _cfg: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [],
        environments=lambda: [Environment(id="env-1", name="Dev Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
        builtin_view=mock_builtin_view,
    )

    col_idx = dialog._COLUMNS.index("Collection")
    cell_text = dialog._table.item(0, col_idx).text()
    assert "Built-in" in cell_text, f"Expected 'Built-in' in table cell, got '{cell_text}'"
    assert "(read-only)" in cell_text, f"Expected '(read-only)' in table cell, got '{cell_text}'"
    assert "Jira Cloud MCP" in cell_text or "jira_mcp.json" in cell_text


# ==============================================================================
# AC 3: Existing workspace and library flows unaffected
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_existing_workspace_and_library_flows_unaffected(
    mock_builtin_view: BuiltinCollectionView,
) -> None:
    """Selecting Workspace collection or Library preserves original behavior and widgets."""
    ws_col = Collection(id="ws-1", name="My Workspace Collection")
    env = Environment(id="env-1", name="Dev Cloud")

    editor = _McpServerEditor(
        collections=[ws_col],
        environments=[env],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        builtin_view=mock_builtin_view,
    )

    # 1. Default source is workspace collection
    ws_idx = editor._collection_source.findData("workspace")
    assert ws_idx >= 0
    editor._collection_source.setCurrentIndex(ws_idx)
    editor.show()
    assert editor._collection.isVisible()
    if hasattr(editor, "_builtin_collection"):
        assert not editor._builtin_collection.isVisible()
    assert not editor._library.isVisible()

    editor._select_data(editor._collection, "ws-1")
    editor._select_data(editor._environment, "env-1")
    editor._accept_if_complete()
    assert editor.result() == 1
    cfg_ws = editor.configuration()
    assert cfg_ws.collection_id == "ws-1"
    assert cfg_ws.library_id is None
    assert cfg_ws.bundled_library is False

    # 2. Overview table with workspace and ordinary library rows
    ws_cfg = McpServerConfiguration(
        id="srv-ws",
        port=1082,
        server_type="local",
        collection_id="ws-1",
        environment_id="env-1",
    )
    lib_cfg = McpServerConfiguration(
        id="srv-lib",
        port=1083,
        server_type="local",
        library_id="ext-library",
        manifest_id="ext-library",
        library_collection_path="collections/ext.json",
        bundled_library=False,
        environment_id="env-1",
    )
    dialog = McpServersDialog(
        configurations=lambda: [ws_cfg, lib_cfg],
        status_for=lambda _id: McpServerStatus(_id, "stopped"),
        save=lambda _cfg: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [ws_col],
        environments=lambda: [env],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
        builtin_view=mock_builtin_view,
    )

    col_idx = dialog._COLUMNS.index("Collection")
    ws_cell = dialog._table.item(0, col_idx).text()
    lib_cell = dialog._table.item(1, col_idx).text()

    assert ws_cell == "My Workspace Collection"
    assert "ext-library" in lib_cell
    assert "Built-in" not in ws_cell
    assert "Built-in" not in lib_cell


# ==============================================================================
# AC 4: Legacy pypost-examples row renders as library
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_legacy_pypost_examples_row_renders_as_library(
    mock_builtin_view: BuiltinCollectionView,
) -> None:
    """Configuration with library_id='pypost-examples' and bundled_library=False is 'library'."""
    legacy_cfg = McpServerConfiguration(
        id="srv-legacy",
        name="Legacy Examples",
        port=1084,
        server_type="local",
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        bundled_library=False,
        environment_id="env-1",
    )

    editor = _McpServerEditor(
        collections=[],
        environments=[Environment(id="env-1", name="Dev Cloud")],
        configuration=legacy_cfg,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        builtin_view=mock_builtin_view,
    )

    # In editor, collection source must be 'library', not 'builtin'
    assert editor._collection_source.currentData() == "library"
    assert editor._collection_source.currentData() != "builtin"

    # In McpServersDialog overview table, it renders as library, not Built-in
    dialog = McpServersDialog(
        configurations=lambda: [legacy_cfg],
        status_for=lambda _id: McpServerStatus("srv-legacy", "stopped"),
        save=lambda _cfg: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [],
        environments=lambda: [Environment(id="env-1", name="Dev Cloud")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
        builtin_view=mock_builtin_view,
    )

    col_idx = dialog._COLUMNS.index("Collection")
    cell_text = dialog._table.item(0, col_idx).text()
    assert "Built-in" not in cell_text
    assert "pypost-examples" in cell_text


# ==============================================================================
# AC 1, AC 6: McpControlsPresenter supplies builtin_view to dialog
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_mcp_controls_presenter_supplies_builtin_view_to_dialog() -> None:
    """McpControlsPresenter passes builtin_view to McpServersDialog."""
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings(mcp_host="127.0.0.1", mcp_port=9080)
    metrics = MagicMock()
    library_service = MagicMock()

    controller = MagicMock(spec=McpServerController)
    mock_builtin_view_instance = MagicMock(spec=BuiltinCollectionView)
    # Simulate controller.registry._builtin_view
    controller.registry = MagicMock()
    controller.registry._builtin_view = mock_builtin_view_instance

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
        library_service=library_service,
    )
    presenter.set_server_controller(controller)

    with patch(
        "pypost.ui.presenters.mcp_controls_presenter.McpServersDialog"
    ) as mock_dialog_cls:
        mock_dialog_instance = MagicMock()
        mock_dialog_cls.return_value = mock_dialog_instance

        presenter._open_mcp_servers()

        mock_dialog_cls.assert_called_once()
        _, kwargs = mock_dialog_cls.call_args
        assert "builtin_view" in kwargs, "McpServersDialog must receive builtin_view parameter"
        assert kwargs["builtin_view"] is mock_builtin_view_instance


# ==============================================================================
# AC 5: Edit workflow preselects Built-in source and entry
# ==============================================================================


@pytest.mark.usefixtures("qapp")
def test_editor_opens_existing_builtin_server_for_editing(
    mock_builtin_view: BuiltinCollectionView,
) -> None:
    """Opening an existing bundled server preselects 'builtin' and the matching entry."""
    bundled_cfg = McpServerConfiguration(
        id="srv-bundled",
        name="My Bundled Jira",
        port=1085,
        server_type="local",
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        bundled_library=True,
        collection_id=None,
        environment_id="env-cloud",
    )

    editor = _McpServerEditor(
        collections=[],
        environments=[Environment(id="env-cloud", name="Cloud Env")],
        configuration=bundled_cfg,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        builtin_view=mock_builtin_view,
    )

    # 1. Collection source must be "builtin"
    assert editor._collection_source.currentData() == "builtin"

    # 2. Builtin collection combo must be visible and select the Jira collection path
    assert hasattr(editor, "_builtin_collection")
    editor.show()
    assert editor._builtin_collection.isVisible()
    current_entry_data = editor._builtin_collection.currentData()
    if hasattr(current_entry_data, "collection_path"):
        current_path = current_entry_data.collection_path
    else:
        current_path = str(current_entry_data)
    assert current_path == "collections/jira_mcp.json"

    # 3. Environment preselected
    assert editor._environment.currentData() == "env-cloud"
