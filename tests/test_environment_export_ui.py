"""Qt-level tests for EnvironmentListWidget.export_environments (PYPOST-988)."""

import json
import logging
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.timeout(60)

from pypost.core.environment_export import ExportScope
from pypost.models.models import Environment
from pypost.ui.widgets.environments.environment_list_widget import EnvironmentListWidget

_MODULE = "pypost.ui.widgets.environments.environment_list_widget"


def _make_widget(environments, serialize_export_records=None):
    return EnvironmentListWidget(
        environments,
        serialize_export_records=serialize_export_records,
    )


class TestExportEnvironments:
    @patch(f"{_MODULE}.show_export_result")
    @patch(f"{_MODULE}.prompt_export_environments_file")
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.ALL)
    def test_single_environment_export_writes_object_root(
        self, _mock_scope, mock_save_dialog, _mock_show_result, qapp, tmp_path
    ):
        export_path = tmp_path / "environment.json"
        mock_save_dialog.return_value = export_path
        env = Environment(name="Dev", variables={"HOST": "dev.example.com"})
        widget = _make_widget(
            [env],
            serialize_export_records=lambda envs: [
                environment.model_dump(mode="json") for environment in envs
            ],
        )
        try:
            widget.export_environments()

            data = json.loads(export_path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            assert data["name"] == "Dev"
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_export_result")
    @patch(f"{_MODULE}.prompt_export_environments_file")
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.ALL)
    def test_happy_path_exports_all_and_shows_success(
        self, _mock_scope, mock_save_dialog, mock_show_result, qapp, tmp_path
    ):
        export_path = tmp_path / "environments.json"
        mock_save_dialog.return_value = export_path

        def serialize(envs):
            return [env.model_dump(mode="json") for env in envs]

        envs = [
            Environment(name="Dev", variables={"HOST": "dev.example.com"}),
            Environment(name="Prod", variables={"HOST": "prod.example.com"}),
        ]
        widget = _make_widget(envs, serialize_export_records=serialize)
        try:
            widget.export_environments()
            assert export_path.exists()
            data = json.loads(export_path.read_text(encoding="utf-8"))
            assert isinstance(data, list)
            assert len(data) == 2
            mock_show_result.assert_called_once()
            _args, kwargs = mock_show_result.call_args
            assert kwargs["success"] is True
        finally:
            widget.close()

    @patch(f"{_MODULE}.prompt_export_scope", return_value=None)
    def test_cancelled_scope_leaves_files_unchanged(self, _mock_scope, qapp, tmp_path):
        export_path = tmp_path / "environments.json"

        def serialize(envs):
            return [env.model_dump(mode="json") for env in envs]

        widget = _make_widget([Environment(name="Dev")], serialize_export_records=serialize)
        try:
            widget.export_environments()
            assert not export_path.exists()
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_export_no_selection_error")
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.SELECTED)
    def test_selected_scope_without_selection_shows_error(
        self, _mock_scope, mock_show_error, qapp
    ):
        widget = _make_widget(
            [Environment(name="Dev")],
            serialize_export_records=lambda envs: [],
        )
        try:
            widget.env_list.setCurrentRow(-1)
            widget.export_environments()
            mock_show_error.assert_called_once()
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_export_result")
    @patch(f"{_MODULE}.prompt_export_environments_file")
    @patch(f"{_MODULE}.confirm_export_includes_secrets", return_value=True)
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.SELECTED)
    def test_hidden_values_require_confirmation(
        self,
        _mock_scope,
        mock_confirm_secrets,
        mock_save_dialog,
        mock_show_result,
        qapp,
        tmp_path,
    ):
        export_path = tmp_path / "Prod.json"
        mock_save_dialog.return_value = export_path
        env = Environment(name="Prod", variables={"token": "abc"}, hidden_keys={"token"})
        widget = _make_widget(
            [env],
            serialize_export_records=lambda envs: [e.model_dump(mode="json") for e in envs],
        )
        try:
            widget.env_list.setCurrentRow(0)
            widget.export_environments()
            mock_confirm_secrets.assert_called_once()
            assert export_path.exists()
        finally:
            widget.close()

    @patch(f"{_MODULE}.prompt_export_environments_file")
    @patch(f"{_MODULE}.confirm_export_includes_secrets", return_value=False)
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.ALL)
    def test_cancelled_secrets_confirmation_skips_write(
        self,
        _mock_scope,
        _mock_confirm,
        mock_save_dialog,
        qapp,
        tmp_path,
    ):
        export_path = tmp_path / "environments.json"
        mock_save_dialog.return_value = export_path
        env = Environment(name="Prod", variables={"token": "abc"}, hidden_keys={"token"})
        widget = _make_widget(
            [env],
            serialize_export_records=lambda envs: [e.model_dump(mode="json") for e in envs],
        )
        try:
            widget.export_environments()
            mock_save_dialog.assert_not_called()
            assert not export_path.exists()
        finally:
            widget.close()

    def test_no_serialize_callable_is_noop(self, qapp):
        widget = _make_widget([Environment(name="Dev")], serialize_export_records=None)
        try:
            widget.export_environments()
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_export_result")
    @patch(f"{_MODULE}.prompt_export_environments_file")
    @patch(f"{_MODULE}.prompt_export_scope", return_value=ExportScope.ALL)
    def test_logs_completed_event(
        self, _mock_scope, mock_save_dialog, _mock_show_result, qapp, tmp_path, caplog
    ):
        export_path = tmp_path / "environments.json"
        mock_save_dialog.return_value = export_path
        widget = _make_widget(
            [Environment(name="Dev")],
            serialize_export_records=lambda envs: [e.model_dump(mode="json") for e in envs],
        )
        try:
            with caplog.at_level(logging.INFO):
                widget.export_environments()
            assert any(
                "environment_export_completed count=1" in r.message for r in caplog.records
            )
        finally:
            widget.close()
