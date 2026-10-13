"""Automated red repro tests for variable setup wizard integration (PYPOST-1374).

Asserts:
- _McpServerEditor provides a "Configure Variables..." button with automation ID
  MCP_SERVER_CONFIGURE_VARIABLES_BUTTON.
- Button is visible/enabled when a library collection has variables, and hidden/disabled
  when collection defines no variables or non-library source is selected.
- Clicking button or invoking _on_configure_variables_clicked() opens VariableSetupWizardDialog,
  pre-populating with existing draft overlay values and profile defaults.
- Accepting the wizard updates _library_overlay ('overrides' and 'secrets') and
  synchronizes inline form inputs.
- Cancelling the wizard preserves previous draft overlay values and inline form inputs.
- Saving McpServersDialog persists the configured overlay to LocalLibraryOverlay storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QDialog

from pypost.core.collection_serializer import write_collection_file
from pypost.core.config_manager import ConfigManager
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog, _McpServerEditor
from pypost.ui.mcp_server_controller import McpServerSettingsController

pytestmark = pytest.mark.timeout(30)


def _sample_library_selection(
    variables: list[dict[str, Any]] | None = None,
    profiles: dict[str, Any] | None = None,
    overlay: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if variables is None:
        variables = [
            {
                "name": "api_host",
                "type": "string",
                "default": "api.example.com",
                "description": "API host endpoint",
                "help_text": "Enter your host URL without protocol.",
                "required": True,
            },
            {
                "name": "api_token",
                "type": "string",
                "secret": True,
                "description": "Authentication bearer token",
                "help_text": "Generate a token in settings -> tokens.",
                "required": True,
            },
        ]
    if profiles is None:
        profiles = {
            "dev": {"api_host": "dev.api.example.com"},
            "prod": {"api_host": "prod.api.example.com"},
        }
    return {
        "library_id": "lib-1",
        "manifest_id": "manifest-1",
        "path": "collections/sample.json",
        "name": "Sample API Collection",
        "manifest_variables": variables,
        "manifest_profiles": profiles,
        "overlay": overlay or {},
    }


def _create_editor(
    qapp,
    selection: dict[str, Any] | None = None,
    server_type: str = "local",
    collection_source: str = "library",
) -> _McpServerEditor:
    editor = _McpServerEditor(
        collections=[Collection(id="ws-col", name="Workspace Col")],
        environments=[Environment(id="dev-env", name="Dev Env")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        library_selections=[selection] if selection else [],
    )
    # Configure server type
    idx = editor._server_type.findData(server_type)
    if idx >= 0:
        editor._server_type.setCurrentIndex(idx)
    # Configure collection source
    idx = editor._collection_source.findData(collection_source)
    if idx >= 0:
        editor._collection_source.setCurrentIndex(idx)
    if selection and collection_source == "library":
        editor._replace_library_selections([selection])
    return editor


@pytest.mark.usefixtures("qapp")
def test_configure_variables_button_exists_and_has_stable_id(qapp):
    """Editor provides a configure variables button with stable automation ID."""
    from pypost.ui import widget_ids

    assert hasattr(widget_ids, "MCP_SERVER_CONFIGURE_VARIABLES_BUTTON"), (
        "widget_ids missing MCP_SERVER_CONFIGURE_VARIABLES_BUTTON constant"
    )
    expected_id = widget_ids.MCP_SERVER_CONFIGURE_VARIABLES_BUTTON

    selection = _sample_library_selection()
    editor = _create_editor(qapp, selection=selection)
    try:
        assert hasattr(editor, "_configure_variables_btn"), (
            "_McpServerEditor missing _configure_variables_btn attribute"
        )
        btn = editor._configure_variables_btn
        assert btn.objectName() == expected_id
        assert "Configure Variables" in btn.text()
    finally:
        editor.close()


@pytest.mark.usefixtures("qapp")
def test_configure_variables_button_visibility_and_enablement(qapp):
    """Button is visible/enabled only for library collection with declared variables."""
    # 1. Library collection with variables -> visible and enabled
    selection_with_vars = _sample_library_selection()
    editor = _create_editor(qapp, selection=selection_with_vars)
    try:
        btn = getattr(editor, "_configure_variables_btn", None)
        assert btn is not None, "_McpServerEditor missing _configure_variables_btn"
        assert btn.isVisible() is True
        assert btn.isEnabled() is True

        # 2. Switch to workspace collection source -> button hidden
        ws_idx = editor._collection_source.findData("workspace")
        editor._collection_source.setCurrentIndex(ws_idx)
        assert btn.isVisible() is False

        # 3. Switch back to library source with collection having NO variables -> hidden/disabled
        selection_no_vars = _sample_library_selection(variables=[])
        lib_idx = editor._collection_source.findData("library")
        editor._collection_source.setCurrentIndex(lib_idx)
        editor._replace_library_selections([selection_no_vars])
        assert (btn.isVisible() is False) or (btn.isEnabled() is False)

        # 4. Proxy server type -> button hidden
        proxy_idx = editor._server_type.findData("proxy")
        editor._server_type.setCurrentIndex(proxy_idx)
        assert btn.isVisible() is False
    finally:
        editor.close()


@pytest.mark.usefixtures("qapp")
def test_wizard_launch_prepopulates_draft_values(qapp):
    """Wizard launch converts manifest variables and pre-populates draft values."""
    selection = _sample_library_selection(
        overlay={
            "overrides": {"api_host": "custom.api.example.com"},
            "secrets": {"api_token": "secret-token-xyz"},
        }
    )
    editor = _create_editor(qapp, selection=selection)
    try:
        assert hasattr(editor, "_on_configure_variables_clicked"), (
            "_McpServerEditor missing _on_configure_variables_clicked method"
        )
        assert hasattr(editor, "_create_variable_wizard"), (
            "_McpServerEditor missing _create_variable_wizard"
        )
        assert hasattr(editor, "_launch_variable_wizard"), (
            "_McpServerEditor missing _launch_variable_wizard"
        )

        with patch.object(editor, "_create_variable_wizard") as mock_create, (
            patch.object(
                editor,
                "_launch_variable_wizard",
                return_value=QDialog.DialogCode.Rejected,
            )
        ):
            mock_create.return_value = MagicMock()
            editor._on_configure_variables_clicked()

            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            vars_arg = call_kwargs.get("variables")
            initial_vals = call_kwargs.get("initial_values")

            assert vars_arg is not None
            assert len(vars_arg) == 2
            assert all(isinstance(v, CollectionVariable) for v in vars_arg)

            assert initial_vals is not None
            assert initial_vals.get("api_host") == "custom.api.example.com"
            assert initial_vals.get("api_token") == "secret-token-xyz"
    finally:
        editor.close()


@pytest.mark.usefixtures("qapp")
def test_wizard_acceptance_updates_overlay_and_inline_fields(qapp):
    """Accepting wizard updates _library_overlay and synchronizes inline form fields."""
    selection = _sample_library_selection(
        overlay={
            "overrides": {"api_host": "initial.host.com"},
            "secrets": {"api_token": "initial-secret"},
        }
    )
    editor = _create_editor(qapp, selection=selection)
    try:
        wizard_result = {
            "values": {
                "api_host": "updated.host.com",
                "api_token": "new-secret-123",
            },
            "overrides": {
                "api_host": "updated.host.com",
            },
            "secrets": {
                "api_token": "new-secret-123",
            },
        }

        mock_wizard = MagicMock()
        mock_wizard.get_configured_variables.return_value = wizard_result

        assert hasattr(editor, "_on_configure_variables_clicked"), (
            "_McpServerEditor missing _on_configure_variables_clicked method"
        )
        assert hasattr(editor, "_create_variable_wizard"), (
            "_McpServerEditor missing _create_variable_wizard"
        )
        assert hasattr(editor, "_launch_variable_wizard"), (
            "_McpServerEditor missing _launch_variable_wizard"
        )
        with patch.object(editor, "_create_variable_wizard", return_value=mock_wizard), (
            patch.object(
                editor,
                "_launch_variable_wizard",
                return_value=QDialog.DialogCode.Accepted,
            )
        ):
            editor._on_configure_variables_clicked()

            # Verify editor overlay draft updated
            overlay_overrides = editor._library_overlay.get("overrides", {})
            overlay_secrets = editor._library_overlay.get("secrets", {})
            assert overlay_overrides.get("api_host") == "updated.host.com"
            assert overlay_secrets.get("api_token") == "new-secret-123"

            # Verify inline QLineEdit fields synchronized
            assert editor._library_variable_fields["api_host"].text() == "updated.host.com"
            assert editor._library_variable_fields["api_token"].text() == "new-secret-123"
    finally:
        editor.close()


@pytest.mark.usefixtures("qapp")
def test_wizard_cancellation_preserves_draft_state(qapp):
    """Cancelling wizard preserves previous overlay and inline values."""
    selection = _sample_library_selection(
        overlay={
            "overrides": {"api_host": "keep.this.host.com"},
            "secrets": {"api_token": "keep-secret-token"},
        }
    )
    editor = _create_editor(qapp, selection=selection)
    try:
        mock_wizard = MagicMock()
        # Mock get_configured_variables returning different values
        mock_wizard.get_configured_variables.return_value = {
            "values": {"api_host": "discarded.host.com", "api_token": "discarded"},
            "overrides": {"api_host": "discarded.host.com"},
            "secrets": {"api_token": "discarded"},
        }

        assert hasattr(editor, "_create_variable_wizard"), (
            "_McpServerEditor missing _create_variable_wizard"
        )
        assert hasattr(editor, "_launch_variable_wizard"), (
            "_McpServerEditor missing _launch_variable_wizard"
        )
        with patch.object(editor, "_create_variable_wizard", return_value=mock_wizard), (
            patch.object(
                editor,
                "_launch_variable_wizard",
                return_value=QDialog.DialogCode.Rejected,
            )
        ):
            editor._on_configure_variables_clicked()

            # Values must NOT be altered
            overlay_overrides = editor._library_overlay.get("overrides", {})
            overlay_secrets = editor._library_overlay.get("secrets", {})
            assert overlay_overrides.get("api_host") == "keep.this.host.com"
            assert overlay_secrets.get("api_token") == "keep-secret-token"
            assert editor._library_variable_fields["api_host"].text() == "keep.this.host.com"
            assert editor._library_variable_fields["api_token"].text() == "keep-secret-token"
    finally:
        editor.close()


@pytest.mark.usefixtures("qapp")
def test_save_persists_overlay_to_local_library_overlay(tmp_path: Path, qapp):
    """Accepted wizard values persist through save into LocalLibraryOverlay storage."""
    # Set up real library service and config manager
    lib_dir = tmp_path / "library"
    (lib_dir / "collections").mkdir(parents=True)
    write_collection_file(
        Collection(id="sample", name="Persist Sample"),
        lib_dir / "collections/sample.json",
    )
    manifest_file = lib_dir / "pypost-library.json"
    manifest_file.write_text(
        json.dumps(
            {
                "id": "lib-persist",
                "name": "Persist Library",
                "collections": ["collections/sample.json"],
                "variables": [
                    {
                        "name": "api_host",
                        "type": "string",
                        "default": "default.example.com",
                    },
                    {
                        "name": "api_token",
                        "type": "string",
                        "secret": True,
                        "required": True,
                    },
                ],
                "presets": {"dev": {}},
            }
        ),
        encoding="utf-8",
    )

    selection = {
        "library_id": "lib-persist",
        "manifest_id": "lib-persist",
        "path": "collections/sample.json",
        "name": "Persist Sample",
        "manifest_variables": [
            {"name": "api_host", "type": "string", "default": "default.example.com"},
            {"name": "api_token", "type": "string", "secret": True, "required": True},
        ],
        "manifest_profiles": {"dev": {}},
        "overlay": {},
    }

    overlay_mgr = LocalOverlayManager(tmp_path / "overlays")
    conn_store = LibraryConnectionStore(tmp_path / "connections.json")
    service = LibraryManagerService(
        connection_store=conn_store,
        overlay_manager=overlay_mgr,
    )
    service.connect_local_directory(lib_dir)

    config_mgr = ConfigManager(config_dir=tmp_path)
    registry = MCPServerRegistry(library_service=service)
    controller = McpServerSettingsController(
        config_manager=config_mgr,
        registry=registry,
        library_service=service,
    )

    saved_payloads = []
    dialog = McpServersDialog(
        configurations=lambda: [],
        status_for=lambda _id: McpServerStatus(_id, "stopped"),
        save=lambda _cfg: None,
        save_library=lambda cfg, sel, handoff: (
            saved_payloads.append((cfg, sel, handoff)),
            controller.save_library_server(cfg, sel, handoff),
        ),
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [],
        environments=lambda: [Environment(id="dev-env", name="Dev Env")],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
        library_service=service,
    )

    editor = _create_editor(qapp, selection=selection)
    try:
        # Simulate wizard configuration update
        wizard_result = {
            "values": {
                "api_host": "persisted.api.com",
                "api_token": "persisted-secret-token",
            },
            "overrides": {
                "api_host": "persisted.api.com",
            },
            "secrets": {
                "api_token": "persisted-secret-token",
            },
        }

        mock_wizard = MagicMock()
        mock_wizard.get_configured_variables.return_value = wizard_result

        assert hasattr(editor, "_on_configure_variables_clicked"), (
            "_McpServerEditor missing _on_configure_variables_clicked"
        )
        with patch.object(editor, "_create_variable_wizard", return_value=mock_wizard), (
            patch.object(
                editor,
                "_launch_variable_wizard",
                return_value=QDialog.DialogCode.Accepted,
            )
        ):
            editor._on_configure_variables_clicked()

        editor._accept_if_complete()
        assert editor.result() == QDialog.DialogCode.Accepted

        dialog._save_configuration(editor, editor.configuration())
        assert len(saved_payloads) == 1

        # Check persisted overlay in LocalOverlayManager
        overlay = overlay_mgr.load_overlay("lib-persist")
        assert overlay is not None
        assert overlay.overrides.get("api_host") == "persisted.api.com"
        assert overlay.secrets.get("api_token") == "persisted-secret-token"
    finally:
        editor.close()
        dialog.close()
