"""Failing repro tests for McpServerHeadersTable and _McpServerEditor (PYPOST-1104).

Asserts:
1. Table Instantiation & Column Setup (Key, Value, stretch resize, empty trailing row).
2. Data Roundtripping (set_data / get_data with key stripping).
3. Row Addition and Deletion.
4. Value Autocompletion with {{ trigger and environment variables.
5. Header Key RFC 7230 Syntax Validation (spaces/colons rejected, empty key with value rejected).
6. Template Placeholder & Variable Existence Validation (unclosed brace, missing var warning).
7. Environment Switching Reactivity (updating environment refreshes validation and autocompletion).
8. _McpServerEditor Dialog Integration (_headers_table widget, env binding,
   blocking on structural errors, config roundtrip).
"""

from __future__ import annotations

import logging

import pytest
from PySide6.QtWidgets import QHeaderView

from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration
from pypost.ui.dialogs.mcp_servers_dialog import _McpServerEditor
from pypost.ui.widgets.empty_row_key_value_table import EmptyRowKeyValueTable
from pypost.ui.widgets.mcp_server_headers_table import (
    McpServerHeadersTable,
    VariableAutocompleteDelegate,
    VariableAutocompleteLineEdit,
    validate_header_key,
    validate_header_value,
)

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_instantiation_and_structure() -> None:
    """McpServerHeadersTable must inherit EmptyRowKeyValueTable and setup 2 columns."""
    assert issubclass(McpServerHeadersTable, EmptyRowKeyValueTable)

    table = McpServerHeadersTable()
    try:
        assert table.columnCount() == 2
        assert table.horizontalHeaderItem(0).text() == "Key"
        assert table.horizontalHeaderItem(1).text() == "Value"
        assert table.rowCount() >= 1  # At least the trailing empty row
        assert (
            table.horizontalHeader().sectionResizeMode(0)
            == QHeaderView.ResizeMode.Stretch
        )
        assert (
            table.horizontalHeader().sectionResizeMode(1)
            == QHeaderView.ResizeMode.Stretch
        )
        # Column 1 should have VariableAutocompleteDelegate installed
        delegate = table.itemDelegateForColumn(1)
        assert isinstance(delegate, VariableAutocompleteDelegate)
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_set_and_get_data() -> None:
    """set_data populates rows with trailing empty row; get_data strips keys and roundtrips."""
    table = McpServerHeadersTable()
    try:
        headers = {
            "Authorization": "Bearer {{ API_KEY }}",
            "X-Custom-Header": "value123",
        }
        table.set_data(headers)

        # 2 data rows + 1 trailing empty row = 3 rows
        assert table.rowCount() == 3
        assert table.item(0, 0).text() == "Authorization"
        assert table.item(0, 1).text() == "Bearer {{ API_KEY }}"
        assert table.item(1, 0).text() == "X-Custom-Header"
        assert table.item(1, 1).text() == "value123"
        assert table.item(2, 0).text() == ""
        assert table.item(2, 1).text() == ""

        roundtripped = table.get_data()
        assert roundtripped == headers
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_row_addition_and_deletion() -> None:
    """Modifying the trailing empty row appends another, and remove_selected_rows removes rows."""
    table = McpServerHeadersTable()
    try:
        table.set_data({})
        assert table.rowCount() == 1  # Trailing empty row

        # Enter key into trailing row
        last_row = table.rowCount() - 1
        table.item(last_row, 0).setText("X-New-Key")
        # Should have auto-added another trailing row
        assert table.rowCount() == 2

        # Add a second row
        last_row = table.rowCount() - 1
        table.item(last_row, 0).setText("X-Second-Key")
        assert table.rowCount() == 3

        # Select row 0 and delete
        table.selectRow(0)
        table.remove_selected_rows()
        assert table.rowCount() == 2
        assert table.get_data() == {"X-Second-Key": ""}

        # Cannot delete trailing empty row
        table.selectRow(1)
        table.remove_selected_rows()
        assert table.rowCount() == 2
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_value_autocompletion() -> None:
    """VariableAutocompleteLineEdit triggers autocomplete on '{{' and completes candidate."""
    env_vars = ["API_KEY", "AUTH_TOKEN", "BASE_URL"]
    editor = VariableAutocompleteLineEdit(variables=env_vars)
    try:
        # Initial text without trigger
        editor.setText("Bearer ")
        assert not editor.is_popup_visible()

        # Type {{ trigger
        editor.setText("Bearer {{ ")
        editor.trigger_autocomplete()
        assert editor.is_popup_visible()

        # Candidates should contain the environment variables
        candidates = editor.current_candidates()
        assert "API_KEY" in candidates
        assert "AUTH_TOKEN" in candidates
        assert "BASE_URL" in candidates

        # Filter by typing prefix
        editor.setText("Bearer {{ AU")
        editor.trigger_autocomplete()
        filtered = editor.current_candidates()
        assert filtered == ["AUTH_TOKEN"]

        # Select candidate
        editor.apply_completion("AUTH_TOKEN")
        assert editor.text() == "Bearer {{ AUTH_TOKEN }}"
        assert not editor.is_popup_visible()
    finally:
        editor.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_key_syntax_validation() -> None:
    """Header key syntax validates RFC 7230 tokens and flags structural errors."""
    table = McpServerHeadersTable()
    try:
        # Valid key
        res = validate_header_key("X-Custom_Header.1", has_value=True)
        assert res is not None
        assert res.is_valid is True
        assert res.is_structural_error is False

        # Invalid key with spaces
        res_space = validate_header_key("Invalid Key", has_value=True)
        assert res_space is not None
        assert res_space.is_valid is False
        assert res_space.is_structural_error is True
        assert "space" in res_space.message.lower()

        # Invalid key with colon
        res_colon = validate_header_key("Header:Name", has_value=True)
        assert res_colon is not None
        assert res_colon.is_valid is False
        assert res_colon.is_structural_error is True
        assert "colon" in res_colon.message.lower()

        # Empty key with value
        res_empty = validate_header_key("", has_value=True)
        assert res_empty is not None
        assert res_empty.is_valid is False
        assert res_empty.is_structural_error is True

        # Test within table
        table.set_data({"Invalid Key": "some_value"})
        assert table.has_structural_errors() is True
        errors = table.get_validation_errors()
        assert len(errors) > 0

        # Replace with valid key
        table.set_data({"Valid-Key": "some_value"})
        assert table.has_structural_errors() is False
        assert len(table.get_validation_errors()) == 0
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_template_and_variable_validation() -> None:
    """Value validation checks for unclosed placeholders and undefined environment variables."""
    known_vars = {"DEFINED_VAR"}

    # Unclosed placeholder
    res_unclosed = validate_header_value("Bearer {{ UNCLOSED", known_vars)
    assert any("unclosed" in r.message.lower() for r in res_unclosed)

    # Undefined variable
    res_undefined = validate_header_value("Bearer {{ UNDEFINED_VAR }}", known_vars)
    assert any("UNDEFINED_VAR" in r.message for r in res_undefined)
    # Undefined variable is an advisory warning, not structural error
    assert not any(r.is_structural_error for r in res_undefined)

    # Defined variable produces no error/warnings
    res_valid = validate_header_value("Bearer {{ DEFINED_VAR }}", known_vars)
    assert len(res_valid) == 0

    table = McpServerHeadersTable()
    try:
        table.set_environment_variables({"DEFINED_VAR": "secret"})
        table.set_data({"Authorization": "Bearer {{ UNDEFINED_VAR }}"})
        # Structural error should be False (can still save with advisory warning)
        assert table.has_structural_errors() is False
        warnings = table.get_validation_warnings()
        assert any("UNDEFINED_VAR" in w for w in warnings)
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_environment_switching_reactivity() -> None:
    """Switching environment updates variable candidates and validation states."""
    env1 = Environment(id="env-1", name="Dev", variables={"DEV_KEY": "abc"})
    env2 = Environment(id="env-2", name="Prod", variables={"PROD_KEY": "xyz"})

    table = McpServerHeadersTable()
    try:
        table.set_environment(env1)
        table.set_data({"Authorization": "Bearer {{ DEV_KEY }}"})
        assert len(table.get_validation_warnings()) == 0

        # Switch to env2
        table.set_environment(env2)
        # Now DEV_KEY is missing in env2
        warnings = table.get_validation_warnings()
        assert any("DEV_KEY" in w for w in warnings)

        # Autocomplete candidates should now reflect env2
        assert "PROD_KEY" in table.environment_variable_names
        assert "DEV_KEY" not in table.environment_variable_names
    finally:
        table.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_editor_dialog_integration() -> None:
    """_McpServerEditor must integrate McpServerHeadersTable and enforce validation."""
    env = Environment(id="env-1", name="Cloud", variables={"TOKEN": "my-secret"})
    config = McpServerConfiguration(
        id="server-proxy",
        name="Proxy Server",
        port=1085,
        server_type="proxy",
        upstream_url="http://localhost:8000/mcp",
        headers={"Authorization": "Bearer {{ TOKEN }}"},
        environment_id="env-1",
    )

    editor = _McpServerEditor(
        collections=[Collection(id="col-1", name="Col")],
        environments=[env],
        configuration=config,
        default_environment=env,
        default_host="127.0.0.1",
        default_port=1085,
    )
    try:
        # Editor must use McpServerHeadersTable instance for _headers_table
        assert hasattr(editor, "_headers_table"), "_McpServerEditor must have _headers_table"
        assert isinstance(editor._headers_table, McpServerHeadersTable)

        # Headers should be populated
        assert editor._headers_table.get_data() == {"Authorization": "Bearer {{ TOKEN }}"}

        # Saving with valid configuration succeeds
        editor._accept_if_complete()
        assert editor.result() == 1  # Accepted

        updated_config = editor.configuration()
        assert updated_config.headers == {"Authorization": "Bearer {{ TOKEN }}"}

        # Now inject a structural error into the headers table
        editor._headers_table.set_data({"Invalid Key": "some_value"})
        assert editor._headers_table.has_structural_errors() is True

        # Re-attempting save should be blocked by structural errors
        editor._accept_if_complete()
        assert "header" in editor._error.text().lower()
    finally:
        editor.deleteLater()


@pytest.mark.usefixtures("qapp")
def test_mcp_server_headers_table_observability_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Ensure debug/info logging occurs for autocomplete triggers/selections and validation."""
    table = McpServerHeadersTable()
    try:
        with caplog.at_level(logging.DEBUG, logger="pypost.ui.widgets.mcp_server_headers_table"):
            # 1. Environment binding logs debug info without logging secrets
            env = Environment(
                id="env-obs",
                name="ObservabilityEnv",
                variables={"SECRET_API_KEY": "supersecret123"},
            )
            table.set_environment(env)
            assert any(
                "Bound environment 'ObservabilityEnv'" in r.message for r in caplog.records
            )
            assert not any("supersecret123" in r.message for r in caplog.records)

            # 2. Autocomplete trigger and selection logging
            editor = VariableAutocompleteLineEdit(variables=["SECRET_API_KEY", "OTHER_VAR"])
            try:
                editor.setText("Bearer {{ SEC")
                editor.trigger_autocomplete()
                assert any(
                    "Autocomplete triggered" in r.message and "SEC" in r.message
                    for r in caplog.records
                )

                editor.apply_completion("SECRET_API_KEY")
                assert any(
                    "Autocomplete selected variable: SECRET_API_KEY" in r.message
                    for r in caplog.records
                )
            finally:
                editor.deleteLater()

            # 3. Validation warnings logging
            caplog.clear()
            table.set_data({"Bad Header Key": "Bearer {{ MISSING_VAR }}"})
            table.validate_rows()
            assert any("structural errors" in r.message for r in caplog.records)
            assert any("validation warnings" in r.message for r in caplog.records)
            assert not any("supersecret123" in r.message for r in caplog.records)
    finally:
        table.deleteLater()

