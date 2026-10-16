"""Automated failing repro tests for workspace environment variable import action (PYPOST-1411).

Asserts desired behavior for collection variable import into workspace environments:
1. Pure domain variable import engine (import_collection_variables_to_environment).
2. Conflict resolution policies (ConflictStrategy.SKIP vs. ConflictStrategy.OVERWRITE).
3. Preset profile value mapping.
4. Automatic secret masking (hidden_keys mapping and mutual exclusion).
5. Storage persistence contract (imported variables and newly hidden keys saved).
6. UI integration: EnvironmentVariablesWidget import button and ImportCollectionVariablesDialog.
7. Re-export contract in pypost.core.environment_ops.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment

pytestmark = [pytest.mark.timeout(30)]


@pytest.mark.timeout(30)
def test_import_collection_variables_skip_strategy() -> None:
    """Verify SKIP strategy preserves existing values while adding new keys."""
    from pypost.core.collection_variable_import import (
        ConflictStrategy,
        import_collection_variables_to_environment,
    )

    env = Environment(
        name="Dev",
        variables={"base_url": "https://existing.com"},
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="base_url", type="string", default="https://api.example.com"),
            CollectionVariable(name="api_key", type="string", default="secret123"),
            CollectionVariable(name="timeout", type="integer", default=30),
        ],
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        conflict_strategy=ConflictStrategy.SKIP,
    )
    assert env.variables["base_url"] == "https://existing.com"
    assert env.variables["api_key"] == "secret123"
    assert env.variables["timeout"] == "30"
    assert set(summary.added_keys) == {"api_key", "timeout"}
    assert summary.skipped_keys == ["base_url"]
    assert summary.updated_keys == []
    assert summary.total_imported == 2


@pytest.mark.timeout(30)
def test_import_collection_variables_overwrite_strategy() -> None:
    """Verify OVERWRITE strategy replaces existing environment variables with defaults."""
    from pypost.core.collection_variable_import import (
        ConflictStrategy,
        import_collection_variables_to_environment,
    )

    env = Environment(
        name="Dev",
        variables={"base_url": "https://existing.com"},
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="base_url", type="string", default="https://api.example.com"),
            CollectionVariable(name="api_key", type="string", default="secret123"),
        ],
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        conflict_strategy=ConflictStrategy.OVERWRITE,
    )
    assert env.variables["base_url"] == "https://api.example.com"
    assert env.variables["api_key"] == "secret123"
    assert summary.updated_keys == ["base_url"]
    assert summary.added_keys == ["api_key"]
    assert summary.skipped_keys == []
    assert summary.total_imported == 2


@pytest.mark.timeout(30)
def test_import_collection_variables_automatic_secret_masking() -> None:
    """Verify secret=True variables are masked into hidden_keys and dropped from overrides."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )

    env = Environment(
        name="Dev",
        variables={},
        hidden_keys=set(),
        mcp_overridable_keys={"auth_token"},
    )
    col = Collection(
        name="Auth",
        variables=[
            CollectionVariable(name="auth_token", type="string", default="token-xyz", secret=True),
            CollectionVariable(name="public_name", type="string", default="myapp", secret=False),
        ],
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
    )
    assert "auth_token" in env.hidden_keys
    assert "auth_token" not in env.mcp_overridable_keys
    assert "public_name" not in env.hidden_keys
    assert "auth_token" in summary.newly_hidden_keys


@pytest.mark.timeout(30)
def test_import_collection_variables_preset_values() -> None:
    """Verify selecting a preset profile imports preset-specific values instead of base defaults."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )

    env = Environment(name="StagingEnv", variables={})
    col = Collection(
        name="Service",
        variables=[
            CollectionVariable(name="host", type="string", default="localhost"),
            CollectionVariable(name="port", type="integer", default=8000),
            CollectionVariable(name="debug", type="boolean", default=True),
        ],
        presets={
            "Staging": {
                "host": "staging.service.internal",
                "port": 443,
                "debug": False,
            }
        },
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        preset_name="Staging",
    )
    assert env.variables["host"] == "staging.service.internal"
    assert env.variables["port"] == "443"
    assert env.variables["debug"] == "false"
    assert summary.total_imported == 3


@pytest.mark.timeout(30)
def test_import_collection_variables_invalid_name_rejected() -> None:
    """Verify invalid names are rejected and tracked in invalid_keys without state corruption."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )

    env = Environment(name="Dev", variables={"valid_var": "1"})
    col = Collection(
        name="BadVars",
        variables=[
            CollectionVariable(name="123_starts_with_digit", type="string", default="val1"),
            CollectionVariable(name="has-hyphen", type="string", default="val2"),
            CollectionVariable(name="good_var", type="string", default="val3"),
        ],
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
    )
    assert "good_var" in env.variables
    assert "123_starts_with_digit" not in env.variables
    assert "has-hyphen" not in env.variables
    invalid_var_names = [name for name, _ in summary.invalid_keys]
    assert "123_starts_with_digit" in invalid_var_names
    assert "has-hyphen" in invalid_var_names
    assert summary.added_keys == ["good_var"]


@pytest.mark.timeout(30)
def test_import_collection_variables_selected_keys_filter() -> None:
    """Verify selected_keys filter imports only the specified subset of collection variables."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )

    env = Environment(name="Dev", variables={})
    col = Collection(
        name="Vars",
        variables=[
            CollectionVariable(name="var_a", type="string", default="a"),
            CollectionVariable(name="var_b", type="string", default="b"),
            CollectionVariable(name="var_c", type="string", default="c"),
        ],
    )
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        selected_keys={"var_a", "var_c"},
    )
    assert "var_a" in env.variables
    assert "var_c" in env.variables
    assert "var_b" not in env.variables
    assert set(summary.added_keys) == {"var_a", "var_c"}


@pytest.mark.timeout(30)
def test_environment_ops_reexports_import_engine() -> None:
    """Verify pypost.core.environment_ops re-exports import engine, strategy, and summary."""
    import pypost.core.environment_ops as ops

    assert hasattr(ops, "import_collection_variables_to_environment"), (
        "pypost.core.environment_ops must re-export import_collection_variables_to_environment"
    )
    assert hasattr(ops, "ConflictStrategy"), (
        "pypost.core.environment_ops must re-export ConflictStrategy"
    )
    assert hasattr(ops, "ImportSummary"), (
        "pypost.core.environment_ops must re-export ImportSummary"
    )


@pytest.mark.timeout(30)
def test_environment_variables_widget_import_button_state(qapp: Any) -> None:
    """Assert EnvironmentVariablesWidget provides an import button with proper lifecycle state."""
    from PySide6.QtWidgets import QPushButton

    from pypost.ui.widgets.environments.environment_variables_widget import (
        EnvironmentVariablesWidget,
    )

    try:
        from pypost.ui.widget_ids import COLLECTION_VARIABLE_IMPORT_BUTTON
    except ImportError:
        COLLECTION_VARIABLE_IMPORT_BUTTON = "pypost_collection_variable_import_button"

    widget = EnvironmentVariablesWidget()
    try:
        import_btn = widget.findChild(QPushButton, COLLECTION_VARIABLE_IMPORT_BUTTON)
        assert import_btn is not None, (
            f"Expected import button '{COLLECTION_VARIABLE_IMPORT_BUTTON}' on widget"
        )
        assert not import_btn.isEnabled(), (
            "Import button must be disabled when no environment is loaded"
        )

        env = Environment(name="Dev", variables={"k": "v"})
        widget.load_environment(env)
        assert import_btn.isEnabled(), (
            "Import button must be enabled when an environment is loaded"
        )

        widget.load_environment(None)
        assert not import_btn.isEnabled(), (
            "Import button must be disabled when environment is unloaded"
        )
    finally:
        widget.close()


@pytest.mark.timeout(30)
def test_import_collection_variables_dialog_workflow(qapp: Any) -> None:
    """Assert ImportCollectionVariablesDialog renders candidates and imports selection."""
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )

    env = Environment(name="Dev", variables={"existing_key": "val1"}, hidden_keys=set())
    col = Collection(
        name="TargetCol",
        variables=[
            CollectionVariable(name="existing_key", type="string", default="col_val1"),
            CollectionVariable(name="secret_key", type="string", default="topsecret", secret=True),
        ],
        presets={"Prod": {"existing_key": "prod_val1", "secret_key": "prodsecret"}},
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        assert dialog.objectName() == "pypost_import_collection_variables_dialog"
        assert dialog.vars_table.rowCount() == 2
        dialog.preset_combo.setCurrentText("Prod")
        dialog.accept()
        assert dialog.summary is not None
        assert "secret_key" in env.variables
        assert "secret_key" in env.hidden_keys
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_import_collection_variables_persistence(
    qapp: Any, tmp_path: Any, monkeypatch: Any
) -> None:
    """Verify that imported collection variables and newly hidden keys are persisted to storage."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )
    from pypost.core.config_manager import ConfigManager
    from pypost.core.storage import StorageManager
    from pypost.models.settings import AppSettings
    from pypost.ui.dialogs.env_dialog import EnvironmentDialog
    from pypost.ui.presenters.env_presenter import EnvPresenter
    from tests.test_env_persistence_e2e import _FakeMCPManager

    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    monkeypatch.setattr(
        "pypost.core.config_manager.user_config_dir",
        lambda *args, **kwargs: str(tmp_path / "pypost-config"),
    )

    storage = StorageManager()
    initial_env = Environment(
        name="Dev",
        variables={"base_url": "https://init.example.com"},
        hidden_keys=set(),
    )
    storage.save_environments([initial_env])

    imported_col = Collection(
        name="PaymentAPI",
        variables=[
            CollectionVariable(
                name="api_secret", type="string", default="sk_live_123", secret=True
            ),
            CollectionVariable(name="endpoint", type="string", default="https://api.stripe.com"),
        ],
    )

    presenter = EnvPresenter(
        storage=storage,
        config_manager=ConfigManager(),
        mcp_manager=_FakeMCPManager(),
        settings=AppSettings(),
        get_collections=lambda: [imported_col],
        metrics=MagicMock(),
    )
    presenter.load_environments()

    dialog = EnvironmentDialog(
        presenter.environments,
        current_env_name="Dev",
        get_collections=lambda: [imported_col],
    )
    try:
        target_env = dialog.environments[0]
        summary = import_collection_variables_to_environment(target_env, imported_col)
        assert summary.total_imported == 2

        # Simulate presenter environment update when dialog is closed/applied
        presenter._environments = dialog.environments
        presenter._save_environments()

        # Reload from storage to verify at-rest persistence and secret preservation
        reloaded = storage.load_environments()
        assert len(reloaded) == 1
        assert reloaded[0].variables["api_secret"] == "sk_live_123"
        assert reloaded[0].variables["endpoint"] == "https://api.stripe.com"
        assert "api_secret" in reloaded[0].hidden_keys
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_import_collection_variables_observability_success_and_secret_safety(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify structured logging and secret-safe contract for collection variable import."""
    from pypost.core.collection_variable_import import (
        ConflictStrategy,
        import_collection_variables_to_environment,
    )

    env = Environment(
        name="Staging",
        variables={"existing_var": "val"},
        hidden_keys=set(),
    )
    secret_value = "super_secret_token_never_log_me_9988"
    col = Collection(
        name="AuthAPI",
        variables=[
            CollectionVariable(name="auth_token", type="string", default=secret_value, secret=True),
            CollectionVariable(name="existing_var", type="string", default="new_val"),
        ],
    )

    with caplog.at_level(logging.DEBUG):
        summary = import_collection_variables_to_environment(
            environment=env,
            collection=col,
            conflict_strategy=ConflictStrategy.OVERWRITE,
            preset_name=None,
        )

    assert summary.total_imported == 2
    logs = caplog.text

    # Verify structured logging events exist
    assert "collection_variable_import_started" in logs
    assert "env_name=Staging" in logs
    assert "collection_name=AuthAPI" in logs
    assert "conflict_strategy=overwrite" in logs
    assert "collection_variable_import_completed" in logs
    assert "total=2 added=1 updated=1 skipped=0 invalid=0 newly_hidden=1" in logs

    # MANDATORY: Secret value must never be logged
    assert secret_value not in logs


@pytest.mark.timeout(30)
def test_import_collection_variables_observability_error_and_invalid_keys(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify warning logging for invalid keys and error logging with context on failures."""
    from pypost.core.collection_variable_import import (
        import_collection_variables_to_environment,
    )

    env = Environment(name="Prod", variables={}, hidden_keys=set())
    col = Collection(
        name="FaultyAPI",
        variables=[
            CollectionVariable(name="invalid key with spaces", type="string", default="val"),
        ],
    )

    with caplog.at_level(logging.WARNING):
        summary = import_collection_variables_to_environment(env, col)

    assert len(summary.invalid_keys) == 1
    assert "collection_variable_import_invalid_key" in caplog.text
    assert "invalid key with spaces" in caplog.text

    # Test failure logging on unhandled exception
    broken_env = Environment(name="Broken", variables={}, hidden_keys=set())
    broken_env.variables = None  # type: ignore[assignment]
    col_ok = Collection(
        name="TestAPI",
        variables=[CollectionVariable(name="key1", type="string", default="v1")],
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(Exception):
            import_collection_variables_to_environment(broken_env, col_ok)

    assert "collection_variable_import_failed" in caplog.text
    assert "env_name=Broken" in caplog.text
