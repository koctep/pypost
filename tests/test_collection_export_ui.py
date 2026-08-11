"""Qt-level tests for CollectionExportActions (PYPOST-989)."""

import json
import logging
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.widget_ids import COLLECTION_EXPORT_ALL_BUTTON, COLLECTION_EXPORT_BUTTON
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)

pytestmark = pytest.mark.timeout(60)

_MODULE = "pypost.ui.presenters.collection_export_actions"
_SAVE = f"{_MODULE}.prompt_export_collection_file"
_RESULT = f"{_MODULE}.show_collection_export_result"
_NO_SELECTION = f"{_MODULE}.show_collection_export_no_selection_error"
_ALL_SAVE = f"{_MODULE}.prompt_export_all_collections_file"
_ALL_RESULT = f"{_MODULE}.show_all_collections_export_result"
_ALL_ERROR = f"{_MODULE}.show_all_collections_export_error"


def _make_presenter(collections=None, serialize_collection=None):
    manager = FakeRequestManager(list(collections or []))
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        serialize_collection=serialize_collection,
    )
    presenter.refresh_tree()
    return presenter, manager


def _select_collection(presenter, collection_id: str) -> None:
    model = presenter.widget.model()
    for row in range(model.rowCount()):
        item = model.item(row)
        if item.data(Qt.UserRole) == collection_id:
            presenter.widget.setCurrentIndex(item.index())
            return
    raise AssertionError(f"collection {collection_id} not found in tree")


class TestExportCollectionEntryPoint:
    @patch.object(CollectionsPresenter, "export_collection")
    def test_panel_exposes_an_identified_export_button_wired_to_the_flow(
        self, mock_export, qapp
    ):
        presenter, _manager = _make_presenter([make_collection("c1", "Billing")])
        try:
            button = presenter.panel.findChild(QPushButton, COLLECTION_EXPORT_BUTTON)
            assert button is not None
            button.click()
            mock_export.assert_called_once()
        finally:
            presenter.panel.close()

    @patch.object(CollectionsPresenter, "export_all_collections")
    def test_panel_exposes_export_all_button_wired_to_the_flow(
        self, mock_export_all, qapp
    ):
        presenter, _manager = _make_presenter([make_collection("c1", "Billing")])
        try:
            button = presenter.panel.findChild(QPushButton, COLLECTION_EXPORT_ALL_BUTTON)
            assert button is not None
            button.click()
            mock_export_all.assert_called_once()
        finally:
            presenter.panel.close()


class TestExportCollection:
    @patch(_RESULT)
    @patch(_SAVE)
    def test_happy_path_exports_selected_collection_and_shows_success(
        self, mock_save, mock_result, qapp, tmp_path
    ):
        export_path = tmp_path / "Billing API.json"
        mock_save.return_value = export_path
        collection = make_collection(
            "c1",
            "Billing API",
            [make_request("r1", "Ping", method="GET")],
        )
        presenter, _manager = _make_presenter(
            [collection],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            _select_collection(presenter, "c1")
            presenter.export_collection()

            assert export_path.exists()
            data = json.loads(export_path.read_text(encoding="utf-8"))
            assert data["name"] == "Billing API"
            assert len(data["requests"]) == 1
            mock_result.assert_called_once()
            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is True
            assert "Billing API" in _args[1]
        finally:
            presenter.panel.close()


class TestExportAllCollections:
    @patch(_ALL_RESULT)
    @patch(_ALL_SAVE)
    def test_exports_every_collection_without_a_tree_selection(
        self, mock_save, mock_result, qapp, tmp_path
    ):
        export_path = tmp_path / "collections.json"
        mock_save.return_value = export_path
        collections = [
            make_collection("c1", "Billing", [make_request("r1", "Create")]),
            make_collection("c2", "Reporting", [make_request("r2", "Report")]),
        ]
        presenter, _manager = _make_presenter(
            collections,
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            presenter.widget.setCurrentIndex(presenter.widget.model().index(-1, -1))
            presenter.export_all_collections()

            data = json.loads(export_path.read_text(encoding="utf-8"))
            assert [record["name"] for record in data] == ["Billing", "Reporting"]
            mock_result.assert_called_once()
            assert "2 collection(s)" in mock_result.call_args.args[1]
            assert "2 request(s)" in mock_result.call_args.args[1]
        finally:
            presenter.panel.close()

    @patch(_ALL_RESULT)
    @patch(_ALL_SAVE)
    def test_logs_completion_with_safe_all_export_counts(
        self, mock_save, _mock_result, qapp, tmp_path, caplog
    ):
        mock_save.return_value = tmp_path / "collections.json"
        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing", [make_request("r1", "Create")])],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            with caplog.at_level(logging.INFO, logger=_MODULE):
                presenter.export_all_collections()
            assert any(
                "collections_export_completed collection_count=1 request_count=1"
                in record.message
                for record in caplog.records
            )
        finally:
            presenter.panel.close()

    @patch(_ALL_RESULT)
    @patch(_ALL_SAVE)
    def test_empty_library_exports_valid_empty_backup(
        self, mock_save, mock_result, qapp, tmp_path
    ):
        export_path = tmp_path / "collections.json"
        mock_save.return_value = export_path
        presenter, _manager = _make_presenter(
            [], serialize_collection=lambda col: col.model_dump(mode="json")
        )
        try:
            presenter.export_all_collections()

            assert json.loads(export_path.read_text(encoding="utf-8")) == []
            assert "0 collection(s) (0 request(s))" in mock_result.call_args.args[1]
        finally:
            presenter.panel.close()

    @patch(_ALL_SAVE, return_value=None)
    def test_cancelled_all_export_does_not_serialize_or_write(self, mock_save, qapp):
        def unexpected_serialize(_collection):
            raise AssertionError("serialization must not run after cancellation")

        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing")], serialize_collection=unexpected_serialize
        )
        try:
            presenter.export_all_collections()
            mock_save.assert_called_once()
        finally:
            presenter.panel.close()

    @patch(_ALL_ERROR)
    @patch(_ALL_SAVE)
    def test_all_export_write_failure_shows_error_dialog(
        self, mock_save, mock_show_error, qapp, tmp_path
    ):
        mock_save.return_value = tmp_path / "collections.json"

        def boom(_collection):
            from pypost.core.collection_export import CollectionExportError

            raise CollectionExportError("Could not write file: disk full")

        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing")], serialize_collection=boom
        )
        try:
            presenter.export_all_collections()
            mock_show_error.assert_called_once()
            assert "disk full" in mock_show_error.call_args.args[1]
        finally:
            presenter.panel.close()

    @patch(_SAVE, return_value=None)
    def test_cancelled_save_dialog_leaves_files_unchanged(self, mock_save, qapp, tmp_path):
        export_path = tmp_path / "Billing API.json"
        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing API")],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            _select_collection(presenter, "c1")
            presenter.export_collection()
            assert not export_path.exists()
        finally:
            presenter.panel.close()

    @patch(_NO_SELECTION)
    def test_no_tree_selection_shows_error(self, mock_no_selection, qapp):
        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing API")],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            presenter.widget.setCurrentIndex(presenter.widget.model().index(-1, -1))
            presenter.export_collection()
            mock_no_selection.assert_called_once()
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_SAVE)
    def test_request_selection_exports_parent_collection(
        self, mock_save, mock_result, qapp, tmp_path
    ):
        export_path = tmp_path / "Billing API.json"
        mock_save.return_value = export_path
        collection = make_collection(
            "c1",
            "Billing API",
            [make_request("r1", "Ping")],
        )
        presenter, _manager = _make_presenter(
            [collection],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            model = presenter.widget.model()
            request_item = model.item(0).child(0)
            presenter.widget.setCurrentIndex(request_item.index())
            presenter.export_collection()

            data = json.loads(export_path.read_text(encoding="utf-8"))
            assert data["name"] == "Billing API"
            mock_result.assert_called_once()
        finally:
            presenter.panel.close()

    @patch(f"{_MODULE}.show_collection_export_error")
    @patch(_SAVE)
    def test_write_failure_shows_error_dialog(
        self, mock_save, mock_show_error, qapp, tmp_path
    ):
        export_path = tmp_path / "Billing API.json"
        mock_save.return_value = export_path

        def boom(_col):
            from pypost.core.collection_export import CollectionExportError

            raise CollectionExportError("Could not write file: disk full")

        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing API")],
            serialize_collection=boom,
        )
        try:
            _select_collection(presenter, "c1")
            presenter.export_collection()
            mock_show_error.assert_called_once()
            assert "disk full" in mock_show_error.call_args[0][1]
        finally:
            presenter.panel.close()

    def test_no_serialize_callable_is_noop(self, qapp):
        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing API")],
            serialize_collection=None,
        )
        try:
            _select_collection(presenter, "c1")
            presenter.export_collection()
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_SAVE)
    def test_logs_completed_event(
        self, mock_save, _mock_result, qapp, tmp_path, caplog
    ):
        export_path = tmp_path / "Billing API.json"
        mock_save.return_value = export_path
        presenter, _manager = _make_presenter(
            [make_collection("c1", "Billing API", [make_request("r1", "Ping")])],
            serialize_collection=lambda col: col.model_dump(mode="json"),
        )
        try:
            _select_collection(presenter, "c1")
            with caplog.at_level(logging.INFO):
                presenter.export_collection()
            assert any(
                "collection_export_completed collection_name=Billing API request_count=1"
                in r.message
                for r in caplog.records
            )
        finally:
            presenter.panel.close()
