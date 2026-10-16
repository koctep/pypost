"""Automated failing repro tests for per-variable conflict strategy and diff inspector.

Verifies the missing functionality specified in PYPOST-1414:
1. Core domain per-variable conflict strategy resolution in
   import_collection_variables_to_environment (variable_conflict_strategies).
2. Side-by-side diff inspector columns (Current Value vs Candidate Value) in
   ImportCollectionVariablesDialog.
3. Dual-source secret masking in diff inspector columns.
4. Per-row strategy selection (Keep Current vs Overwrite) defaulting safely to Keep Current.
5. Bulk collision strategy actions and dynamic import summary calculation.
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtWidgets import QComboBox
import pytest

from pypost.core.constants import HIDDEN_MASK
from pypost.models.collection_variable import CollectionVariable
from pypost.models.models import Collection, Environment

pytestmark = [pytest.mark.timeout(30)]


@pytest.mark.timeout(30)
def test_core_per_variable_conflict_strategy() -> None:
    """Verify core domain supports per-variable conflict strategies with fallback."""
    from pypost.core.collection_variable_import import (
        ConflictStrategy,
        import_collection_variables_to_environment,
    )

    env = Environment(
        name="Dev",
        variables={
            "var_keep": "old_keep",
            "var_overwrite": "old_overwrite",
            "var_fallback": "old_fallback",
        },
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="var_keep", type="string", default="new_keep"),
            CollectionVariable(name="var_overwrite", type="string", default="new_overwrite"),
            CollectionVariable(name="var_fallback", type="string", default="new_fallback"),
            CollectionVariable(name="var_new", type="string", default="new_val"),
        ],
    )

    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        conflict_strategy=ConflictStrategy.SKIP,
        variable_conflict_strategies={
            "var_keep": ConflictStrategy.SKIP,
            "var_overwrite": ConflictStrategy.OVERWRITE,
        },
    )

    assert env.variables["var_keep"] == "old_keep", "var_keep should be preserved"
    assert env.variables["var_overwrite"] == "new_overwrite", "var_overwrite should be updated"
    assert env.variables["var_fallback"] == "old_fallback", "var_fallback should use default SKIP"
    assert env.variables["var_new"] == "new_val", "var_new should be added"

    assert summary.updated_keys == ["var_overwrite"]
    assert set(summary.skipped_keys) == {"var_keep", "var_fallback"}
    assert summary.added_keys == ["var_new"]
    assert summary.total_imported == 2


@pytest.mark.timeout(30)
def test_dialog_side_by_side_diff_columns(qapp: Any) -> None:
    """Verify ImportCollectionVariablesDialog renders 9 columns with side-by-side diff."""
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )

    env = Environment(
        name="Dev",
        variables={"host": "localhost:8000"},
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(
                name="host",
                type="string",
                default="api.example.com",
                description="Host endpoint",
            ),
            CollectionVariable(
                name="timeout",
                type="integer",
                default=30,
                description="Request timeout",
            ),
        ],
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        assert dialog.vars_table.columnCount() == 9
        headers = [
            dialog.vars_table.horizontalHeaderItem(c).text()
            for c in range(dialog.vars_table.columnCount())
        ]
        assert headers == [
            "",
            "Name",
            "Current Value",
            "Candidate Value",
            "Conflict Strategy",
            "Type",
            "Secret",
            "Status",
            "Description",
        ]

        # Row 0: Colliding variable 'host'
        assert dialog.vars_table.item(0, 1).text() == "host"
        assert dialog.vars_table.item(0, 2).text() == "localhost:8000"
        assert dialog.vars_table.item(0, 3).text() == "api.example.com"
        assert dialog.vars_table.item(0, 7).text() == "Exists (Collision)"

        # Row 1: New non-colliding variable 'timeout'
        assert dialog.vars_table.item(1, 1).text() == "timeout"
        assert dialog.vars_table.item(1, 2).text() == "—"
        assert dialog.vars_table.item(1, 3).text() == "30"
        assert dialog.vars_table.item(1, 4).text() == "—"
        assert dialog.vars_table.item(1, 7).text() == "New"
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_dialog_diff_secret_masking(qapp: Any) -> None:
    """Verify dual-source secret masking across both Current and Candidate diff columns."""
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )

    env = Environment(
        name="Dev",
        variables={
            "env_secret": "sensitive_env_token_xyz",
            "col_secret": "plain_env_val",
            "normal_var": "public_env_val",
        },
        hidden_keys={"env_secret"},
    )
    col = Collection(
        name="SecurityAPI",
        variables=[
            CollectionVariable(
                name="env_secret",
                type="string",
                default="candidate_env_token",
                secret=False,
            ),
            CollectionVariable(
                name="col_secret",
                type="string",
                default="sensitive_candidate_token_abc",
                secret=True,
            ),
            CollectionVariable(
                name="normal_var",
                type="string",
                default="public_candidate_val",
                secret=False,
            ),
        ],
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        # env_secret: secret in env -> both columns must be masked
        assert dialog.vars_table.item(0, 2).text() == HIDDEN_MASK
        assert dialog.vars_table.item(0, 3).text() == HIDDEN_MASK
        assert "sensitive_env_token_xyz" not in dialog.vars_table.item(0, 2).text()
        assert "candidate_env_token" not in dialog.vars_table.item(0, 3).text()

        # col_secret: secret in collection -> both columns must be masked
        assert dialog.vars_table.item(1, 2).text() == HIDDEN_MASK
        assert dialog.vars_table.item(1, 3).text() == HIDDEN_MASK
        assert "plain_env_val" not in dialog.vars_table.item(1, 2).text()
        assert "sensitive_candidate_token_abc" not in dialog.vars_table.item(1, 3).text()

        # normal_var: not secret -> plaintext visible
        assert dialog.vars_table.item(2, 2).text() == "public_env_val"
        assert dialog.vars_table.item(2, 3).text() == "public_candidate_val"
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_dialog_per_row_strategy_selection(qapp: Any) -> None:
    """Verify colliding rows have QComboBox defaulting to Keep Current, controlling import."""
    from pypost.core.collection_variable_import import ConflictStrategy
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )

    env = Environment(
        name="Dev",
        variables={
            "var_keep": "initial_keep_val",
            "var_overwrite": "initial_overwrite_val",
        },
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="var_keep", type="string", default="candidate_keep_val"),
            CollectionVariable(
                name="var_overwrite",
                type="string",
                default="candidate_overwrite_val",
            ),
            CollectionVariable(name="var_new", type="string", default="candidate_new_val"),
        ],
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        # Check strategy widgets for colliding rows
        combo_keep = dialog.vars_table.cellWidget(0, 4)
        assert isinstance(combo_keep, QComboBox)
        assert combo_keep.currentText() == "Keep Current"
        assert dialog.get_row_strategy(0) == ConflictStrategy.SKIP

        combo_overwrite = dialog.vars_table.cellWidget(1, 4)
        assert isinstance(combo_overwrite, QComboBox)
        assert combo_overwrite.currentText() == "Keep Current"
        assert dialog.get_row_strategy(1) == ConflictStrategy.SKIP

        # Non-colliding row does not have a strategy combo
        assert dialog.vars_table.cellWidget(2, 4) is None
        assert dialog.vars_table.item(2, 4).text() == "—"
        assert dialog.get_row_strategy(2) is None

        # Change row 1 to Overwrite
        dialog.set_row_strategy(1, ConflictStrategy.OVERWRITE)
        assert dialog.get_row_strategy(1) == ConflictStrategy.OVERWRITE
        strategies = dialog.get_variable_conflict_strategies()
        assert strategies == {
            "var_keep": ConflictStrategy.SKIP,
            "var_overwrite": ConflictStrategy.OVERWRITE,
        }

        # Accept dialog and verify target environment mutations
        dialog.accept()
        assert env.variables["var_keep"] == "initial_keep_val"
        assert env.variables["var_overwrite"] == "candidate_overwrite_val"
        assert env.variables["var_new"] == "candidate_new_val"
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_dialog_bulk_strategy_and_dynamic_summary(qapp: Any) -> None:
    """Verify bulk buttons batch-set colliding strategies and update summary in real-time."""
    from pypost.core.collection_variable_import import ConflictStrategy
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )
    from pypost.ui.widget_ids import (
        IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON,
        IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON,
    )

    env = Environment(
        name="Dev",
        variables={"var1": "old1", "var2": "old2"},
        hidden_keys=set(),
    )
    col = Collection(
        name="API",
        variables=[
            CollectionVariable(name="var1", type="string", default="new1"),
            CollectionVariable(name="var2", type="string", default="new2"),
            CollectionVariable(name="var_new", type="string", default="new_val"),
        ],
    )

    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[col],
    )
    try:
        assert hasattr(dialog, "bulk_keep_current_btn"), (
            "Dialog must have bulk_keep_current_btn"
        )
        assert hasattr(dialog, "bulk_overwrite_btn"), (
            "Dialog must have bulk_overwrite_btn"
        )
        assert dialog.bulk_keep_current_btn.objectName() == (
            IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON
        )
        assert dialog.bulk_overwrite_btn.objectName() == (
            IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON
        )

        # Baseline: 1 new to add, 0 to overwrite, 2 to keep
        summary_text = dialog.summary_label.text().lower()
        assert "1 new" in summary_text
        assert "2 existing to keep" in summary_text
        assert (
            "0 existing to overwrite" in summary_text
            or "0 selected to overwrite" in summary_text
        )

        # Click bulk overwrite
        dialog.bulk_overwrite_btn.click()
        assert dialog.get_row_strategy(0) == ConflictStrategy.OVERWRITE
        assert dialog.get_row_strategy(1) == ConflictStrategy.OVERWRITE

        summary_text_over = dialog.summary_label.text().lower()
        assert "1 new" in summary_text_over
        assert "2 existing to overwrite" in summary_text_over
        assert "0 existing to keep" in summary_text_over

        # Click bulk keep current
        dialog.bulk_keep_current_btn.click()
        assert dialog.get_row_strategy(0) == ConflictStrategy.SKIP
        assert dialog.get_row_strategy(1) == ConflictStrategy.SKIP

        summary_text_keep = dialog.summary_label.text().lower()
        assert "1 new" in summary_text_keep
        assert "2 existing to keep" in summary_text_keep
        assert "0 existing to overwrite" in summary_text_keep

        # Individual tweak: row 0 to Overwrite
        dialog.set_row_strategy(0, ConflictStrategy.OVERWRITE)
        summary_text_mixed = dialog.summary_label.text().lower()
        assert "1 new" in summary_text_mixed
        assert "1 existing to overwrite" in summary_text_mixed
        assert "1 existing to keep" in summary_text_mixed
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_import_observability_conflict_decisions_and_secrets(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify structured logging of conflict decisions, collisions, and secret masking."""
    from pypost.core.collection_variable_import import (
        ConflictStrategy,
        import_collection_variables_to_environment,
    )

    secret_raw_val = "SUPER_SECRET_TOKEN_DO_NOT_LEAK"
    env = Environment(
        name="Production",
        variables={"token": "old_token", "api_url": "https://api.old.com"},
        hidden_keys={"token"},
    )
    col = Collection(
        name="APIColl",
        variables=[
            CollectionVariable(name="token", type="string", default=secret_raw_val, secret=True),
            CollectionVariable(
                name="api_url", type="string", default="https://api.new.com", secret=False
            ),
            CollectionVariable(name="new_var", type="string", default="hello", secret=False),
        ],
    )

    with caplog.at_level(logging.DEBUG):
        summary = import_collection_variables_to_environment(
            environment=env,
            collection=col,
            conflict_strategy=ConflictStrategy.SKIP,
            variable_conflict_strategies={
                "token": ConflictStrategy.OVERWRITE,
                "api_url": ConflictStrategy.SKIP,
            },
        )

    assert summary.total_imported == 2
    logs = caplog.text

    # Structured logging assertions
    assert "collection_variable_import_started" in logs
    assert "collection_variable_import_conflict_decision" in logs
    assert "key=token collision=True strategy=overwrite decision=updated is_secret=True" in logs
    assert "key=api_url collision=True strategy=skip decision=skipped is_secret=False" in logs
    assert "collection_variable_import_secret_masking_preserved" in logs
    assert "collection_variable_import_completed" in logs
    assert "total=2 added=1 updated=1 skipped=1 invalid=0 newly_hidden=0" in logs

    # Plaintext secret MUST NOT be present in logs
    assert secret_raw_val not in logs
    assert "old_token" not in logs


@pytest.mark.timeout(30)
def test_dialog_observability_bulk_and_accept(
    qapp: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify dialog logs bulk actions, row changes, and accept metrics without secret leakage."""
    from pypost.core.collection_variable_import import ConflictStrategy
    from pypost.ui.dialogs.import_collection_variables_dialog import (
        ImportCollectionVariablesDialog,
    )

    sensitive_pass = "TOP_SECRET_PASSWORD_12345"
    env = Environment(
        name="StagingEnv",
        variables={"db_pass": "existing_secret", "port": "5432"},
        hidden_keys={"db_pass"},
    )
    col = Collection(
        name="DatabaseColl",
        variables=[
            CollectionVariable(name="db_pass", type="string", default=sensitive_pass, secret=True),
            CollectionVariable(name="port", type="string", default="5433", secret=False),
        ],
    )

    with caplog.at_level(logging.DEBUG):
        dialog = ImportCollectionVariablesDialog(
            target_environment=env,
            workspace_collections=[col],
        )
        try:
            dialog.bulk_overwrite_btn.click()
            dialog.set_row_strategy(1, ConflictStrategy.SKIP)
            dialog.accept()
        finally:
            dialog.close()

    logs = caplog.text

    # Verify dialog log events
    assert "collection_variable_import_dialog_opened" in logs
    assert "collection_variable_import_table_populated" in logs
    assert "collection_variable_import_bulk_strategy_applied" in logs
    assert "collection_variable_import_row_strategy_changed" in logs
    assert "collection_variable_import_dialog_accepted" in logs
    assert "collisions=2 overwrite_collisions=1 keep_collisions=1" in logs
    assert "env_collection_variables_imported" in logs

    # Plaintext secret MUST NOT be leaked in logs
    assert sensitive_pass not in logs
    assert "existing_secret" not in logs
