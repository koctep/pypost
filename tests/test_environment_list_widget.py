"""Qt-level tests for EnvironmentListWidget.import_environments (PYPOST-986)."""

import pytest

import logging
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QPushButton

from pypost.core.environment_import import EnvironmentImportFileError, ImportConflictDecision
from pypost.models.models import Environment
from pypost.ui.widget_ids import ENV_IMPORT_BUTTON
from pypost.ui.widgets.environments.environment_list_widget import EnvironmentListWidget

pytestmark = pytest.mark.timeout(60)


_MODULE = "pypost.ui.widgets.environments.environment_list_widget"


def _make_widget(environments, read_import_file=None):
    return EnvironmentListWidget(environments, read_import_file=read_import_file)


class TestImportEnvironments:
    @patch(f"{_MODULE}.show_import_result")
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_happy_path_adds_environments_and_shows_success(
        self, _mock_prompt_file, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [Environment(name="Staging", variables={"HOST": "s.example.com"})], []

        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            assert [e.name for e in envs] == ["Dev", "Staging"]
            assert widget.env_list.count() == 2
            mock_show_result.assert_called_once()
            _args, kwargs = mock_show_result.call_args
            assert kwargs["success"] is True
        finally:
            widget.close()

    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=None)
    def test_cancelled_file_picker_leaves_environments_unchanged(self, _mock_prompt_file, qapp):
        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=lambda path: ([], []))
        try:
            widget.import_environments()
            assert len(envs) == 1
            assert envs[0].name == "Dev"
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_invalid_file_error")
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/bad.json"))
    def test_invalid_file_shows_error_and_leaves_environments_unchanged(
        self, _mock_prompt_file, mock_show_error, qapp
    ):
        def raise_error(path):
            raise EnvironmentImportFileError("File is not valid JSON: boom")

        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=raise_error)
        try:
            widget.import_environments()
            assert len(envs) == 1
            assert envs[0].name == "Dev"
            mock_show_error.assert_called_once()
            assert "not valid JSON" in mock_show_error.call_args[0][1]
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_invalid_file_error")
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/empty.json"))
    def test_zero_candidates_treated_as_invalid_file(
        self, _mock_prompt_file, mock_show_error, qapp
    ):
        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=lambda path: ([], []))
        try:
            widget.import_environments()
            assert len(envs) == 1
            mock_show_error.assert_called_once()
            assert "No valid environments" in mock_show_error.call_args[0][1]
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(
        f"{_MODULE}.prompt_import_conflict",
        return_value=(ImportConflictDecision.OVERWRITE, False),
    )
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_conflict_prompts_once_per_conflicting_name(
        self, _mock_prompt_file, mock_prompt_conflict, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [Environment(name="Dev", variables={"A": "new"})], []

        existing_dev = Environment(id="dev-id", name="Dev", variables={"A": "old"})
        envs = [existing_dev]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            mock_prompt_conflict.assert_called_once()
            assert len(envs) == 1
            assert envs[0].id == "dev-id"
            assert envs[0].variables == {"A": "new"}
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(
        f"{_MODULE}.prompt_import_conflict",
        return_value=(ImportConflictDecision.SKIP, True),
    )
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_apply_to_all_conflicts_prompts_only_once(
        self, _mock_prompt_file, mock_prompt_conflict, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [
                Environment(name="Dev", variables={"A": "new"}),
                Environment(name="Prod", variables={"B": "new"}),
            ], []

        envs = [
            Environment(id="dev-id", name="Dev", variables={"A": "old"}),
            Environment(id="prod-id", name="Prod", variables={"B": "old"}),
        ]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            mock_prompt_conflict.assert_called_once()
            assert len(envs) == 2
            assert envs[0].variables == {"A": "old"}
            assert envs[1].variables == {"B": "old"}
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(
        f"{_MODULE}.prompt_import_conflict",
        return_value=(ImportConflictDecision.SKIP, True),
    )
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_apply_to_all_conflicts_applies_to_third_and_later_conflicts(
        self, _mock_prompt_file, mock_prompt_conflict, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [
                Environment(name="Dev", variables={"A": "new"}),
                Environment(name="Prod", variables={"B": "new"}),
                Environment(name="Staging", variables={"C": "new"}),
            ], []

        envs = [
            Environment(id="dev-id", name="Dev", variables={"A": "old"}),
            Environment(id="prod-id", name="Prod", variables={"B": "old"}),
            Environment(id="staging-id", name="Staging", variables={"C": "old"}),
        ]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            mock_prompt_conflict.assert_called_once()
            assert len(envs) == 3
            assert envs[0].variables == {"A": "old"}
            assert envs[1].variables == {"B": "old"}
            assert envs[2].variables == {"C": "old"}
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(
        f"{_MODULE}.prompt_import_conflict",
        return_value=(ImportConflictDecision.OVERWRITE, True),
    )
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_apply_to_all_conflicts_applies_overwrite_to_third_and_later_conflicts(
        self, _mock_prompt_file, mock_prompt_conflict, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [
                Environment(name="Dev", variables={"A": "new"}),
                Environment(name="Prod", variables={"B": "new"}),
                Environment(name="Staging", variables={"C": "new"}),
            ], []

        envs = [
            Environment(id="dev-id", name="Dev", variables={"A": "old"}),
            Environment(id="prod-id", name="Prod", variables={"B": "old"}),
            Environment(id="staging-id", name="Staging", variables={"C": "old"}),
        ]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            mock_prompt_conflict.assert_called_once()
            assert len(envs) == 3
            assert [e.id for e in envs] == ["dev-id", "prod-id", "staging-id"]
            assert envs[0].variables == {"A": "new"}
            assert envs[1].variables == {"B": "new"}
            assert envs[2].variables == {"C": "new"}
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(
        f"{_MODULE}.prompt_import_conflict",
        return_value=(ImportConflictDecision.KEEP_BOTH, True),
    )
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_apply_to_all_conflicts_applies_keep_both_to_third_and_later_conflicts(
        self, _mock_prompt_file, mock_prompt_conflict, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [
                Environment(name="Dev", variables={"A": "new"}),
                Environment(name="Prod", variables={"B": "new"}),
                Environment(name="Staging", variables={"C": "new"}),
            ], []

        envs = [
            Environment(id="dev-id", name="Dev", variables={"A": "old"}),
            Environment(id="prod-id", name="Prod", variables={"B": "old"}),
            Environment(id="staging-id", name="Staging", variables={"C": "old"}),
        ]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            mock_prompt_conflict.assert_called_once()
            assert len(envs) == 6
            assert [e.name for e in envs] == [
                "Dev",
                "Prod",
                "Staging",
                "Copy of Dev",
                "Copy of Prod",
                "Copy of Staging",
            ]
            assert envs[0].variables == {"A": "old"}
            assert envs[1].variables == {"B": "old"}
            assert envs[2].variables == {"C": "old"}
            assert envs[3].variables == {"A": "new"}
            assert envs[4].variables == {"B": "new"}
            assert envs[5].variables == {"C": "new"}
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_partial_parse_failure_still_imports_valid_entries(
        self, _mock_prompt_file, mock_show_result, qapp
    ):
        def read_import_file(path):
            return [Environment(name="Staging", variables={})], ["Secret: could not be decrypted"]

        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            widget.import_environments()
            assert [e.name for e in envs] == ["Dev", "Staging"]
            _args, kwargs = mock_show_result.call_args
            assert kwargs["success"] is True
            assert "Secret" in _args[1]
        finally:
            widget.close()

    def test_no_read_import_file_callable_is_noop(self, qapp):
        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=None)
        try:
            widget.import_environments()
            assert len(envs) == 1
        finally:
            widget.close()

    @patch(f"{_MODULE}.show_import_result")
    @patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))
    def test_logs_completed_event_with_counts(
        self, _mock_prompt_file, _mock_show_result, qapp, caplog,
    ):
        def read_import_file(path):
            return [Environment(name="Staging", variables={})], []

        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs, read_import_file=read_import_file)
        try:
            with caplog.at_level(logging.INFO):
                widget.import_environments()
            assert any(
                "environment_import_completed added_count=1" in r.message
                for r in caplog.records
            )
        finally:
            widget.close()


class TestImportButtonWiring:
    @patch.object(EnvironmentListWidget, "import_environments")
    def test_mouse_click_on_import_button_starts_import(self, mock_import, qapp):
        envs = [Environment(name="Dev", variables={})]
        widget = _make_widget(envs)
        try:
            button = widget.findChild(QPushButton, ENV_IMPORT_BUTTON)
            assert button is not None
            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            mock_import.assert_called_once()
        finally:
            widget.close()
