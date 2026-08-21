"""Qt-level tests for the Import Collection flow (PYPOST-987)."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QPushButton

from pypost.core.collection_import import CollectionImportFileError
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.request_manager import RequestManager
from pypost.core.storage import StorageManager
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.widget_ids import COLLECTION_IMPORT_BUTTON
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
    make_collection,
    make_request,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_PICKER = f"{_MODULE}.prompt_import_collection_file"
_CONFLICT = f"{_MODULE}.prompt_collection_import_conflict"
_RESULT = f"{_MODULE}.show_collection_import_result"
_INVALID = f"{_MODULE}.show_collection_import_invalid_file_error"

_PATH = Path("/tmp/import.json")
_IMPORT_WAIT_MS = 5_000


def _make_presenter(collections=None, read_import_file=None):
    manager = FakeRequestManager(list(collections or []))
    presenter = CollectionsPresenter(
        manager,
        FakeStateManager(),
        FakeMetrics(),
        {},
        read_import_file=read_import_file,
    )
    presenter.refresh_tree()
    return presenter, manager


def _reader(collections, parse_errors=None):
    def read(path):
        return list(collections), list(parse_errors or [])

    return read


def _wait_import(done: Callable[[], bool]) -> None:
    """Pump the event loop until async import parse/finish completes."""
    process_until(done, timeout_ms=_IMPORT_WAIT_MS)


class TestImportCollectionEntryPoint:
    @patch(_PICKER, return_value=None)
    def test_panel_exposes_an_identified_import_button_wired_to_the_flow(
        self, mock_picker, qapp
    ):
        presenter, _manager = _make_presenter()
        try:
            button = presenter.panel.findChild(QPushButton, COLLECTION_IMPORT_BUTTON)
            assert button is not None
            button.click()
            mock_picker.assert_called_once()
        finally:
            presenter.panel.close()

    def test_widget_property_still_returns_the_tree(self, qapp):
        presenter, _manager = _make_presenter()
        try:
            assert presenter.widget is not presenter.panel
            assert presenter.widget.parent() is presenter.panel
        finally:
            presenter.panel.close()


class TestImportCollections:
    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_happy_path_adds_collection_persists_and_refreshes_tree(
        self, _mock_picker, mock_result, qapp
    ):
        incoming = make_collection("new-id", "Imported", [make_request("r1", "Ping")])
        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")], _reader([incoming])
        )
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            assert [col.name for col in manager.get_collections()] == [
                "Existing",
                "Imported",
            ]
            manager.storage.save_collection.assert_called_once()
            assert presenter.widget.model().rowCount() == 2
            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is True
            assert "Requests imported: 1" in _args[1]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_emits_collections_changed_so_mcp_tools_re_register(
        self, _mock_picker, _mock_result, qapp
    ):
        incoming = make_collection("new-id", "Imported")
        presenter, _manager = _make_presenter([], _reader([incoming]))
        received = []
        presenter.collections_changed.connect(lambda: received.append(True))
        try:
            presenter.import_collections()
            _wait_import(lambda: len(received) >= 1)
            assert received == [True]
        finally:
            presenter.panel.close()

    @patch(_PICKER, return_value=None)
    def test_cancelled_picker_leaves_collections_unchanged(self, _mock_picker, qapp):
        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")], _reader([])
        )
        try:
            presenter.import_collections()
            assert [col.name for col in manager.get_collections()] == ["Existing"]
            manager.storage.save_collection.assert_not_called()
        finally:
            presenter.panel.close()

    @patch(_INVALID)
    @patch(_PICKER, return_value=_PATH)
    def test_invalid_file_shows_error_and_changes_nothing(
        self, _mock_picker, mock_invalid, qapp
    ):
        def raise_error(path):
            raise CollectionImportFileError("File is not valid JSON: boom")

        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")], raise_error
        )
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_invalid.call_count >= 1)
            assert [col.name for col in manager.get_collections()] == ["Existing"]
            manager.storage.save_collection.assert_not_called()
            mock_invalid.assert_called_once()
            assert "not valid JSON" in mock_invalid.call_args[0][1]
        finally:
            presenter.panel.close()

    @patch(_INVALID)
    @patch(_PICKER, return_value=_PATH)
    def test_zero_candidates_treated_as_invalid_file(
        self, _mock_picker, mock_invalid, qapp
    ):
        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")],
            _reader([], ['Entry 1: missing or empty "name" field']),
        )
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_invalid.call_count >= 1)
            assert len(manager.get_collections()) == 1
            manager.storage.save_collection.assert_not_called()
            message = mock_invalid.call_args[0][1]
            assert "No valid collections" in message
            assert "Entry 1" in message
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_CONFLICT, return_value=(ImportConflictDecision.OVERWRITE, False))
    @patch(_PICKER, return_value=_PATH)
    def test_overwrite_conflict_prompts_once_and_keeps_existing_identity(
        self, _mock_picker, mock_conflict, _mock_result, qapp
    ):
        existing = make_collection("keep-id", "My API", [make_request("old", "Old")])
        incoming = make_collection("other-id", "My API", [make_request("new", "New")])
        presenter, manager = _make_presenter([existing], _reader([incoming]))
        try:
            presenter.import_collections()
            _wait_import(lambda: _mock_result.call_count >= 1)

            mock_conflict.assert_called_once()
            collections = manager.get_collections()
            assert len(collections) == 1
            assert collections[0].id == "keep-id"
            assert [req.id for req in collections[0].requests] == ["new"]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_CONFLICT, return_value=(ImportConflictDecision.SKIP, True))
    @patch(_PICKER, return_value=_PATH)
    def test_apply_to_all_prompts_only_once_for_two_conflicts(
        self, _mock_picker, mock_conflict, _mock_result, qapp
    ):
        existing = [make_collection("c1", "My API"), make_collection("c2", "Billing")]
        incoming = [make_collection("i1", "My API"), make_collection("i2", "Billing")]
        presenter, manager = _make_presenter(existing, _reader(incoming))
        try:
            presenter.import_collections()
            _wait_import(lambda: _mock_result.call_count >= 1)

            mock_conflict.assert_called_once()
            assert [col.id for col in manager.get_collections()] == ["c1", "c2"]
            manager.storage.save_collection.assert_not_called()
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_CONFLICT, return_value=(ImportConflictDecision.KEEP_BOTH, True))
    @patch(_PICKER, return_value=_PATH)
    def test_apply_to_all_prompts_only_once_for_three_conflicts(
        self, _mock_picker, mock_conflict, _mock_result, qapp
    ):
        existing = [
            make_collection("c1", "My API"),
            make_collection("c2", "Billing"),
            make_collection("c3", "Auth"),
        ]
        incoming = [
            make_collection("i1", "My API"),
            make_collection("i2", "Billing"),
            make_collection("i3", "Auth"),
        ]
        presenter, manager = _make_presenter(existing, _reader(incoming))
        try:
            presenter.import_collections()
            _wait_import(lambda: _mock_result.call_count >= 1)

            mock_conflict.assert_called_once()
            assert mock_conflict.call_args.kwargs["remaining_count"] == 2
            assert [col.name for col in manager.get_collections()] == [
                "My API",
                "Billing",
                "Auth",
                "Copy of My API",
                "Copy of Billing",
                "Copy of Auth",
            ]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_CONFLICT, return_value=(ImportConflictDecision.KEEP_BOTH, False))
    @patch(_PICKER, return_value=_PATH)
    def test_keep_both_adds_a_renamed_copy_alongside_the_original(
        self, _mock_picker, _mock_conflict, mock_result, qapp
    ):
        existing = make_collection("keep-id", "My API", [make_request("old", "Old")])
        incoming = make_collection("keep-id", "My API", [make_request("old", "Old")])
        presenter, manager = _make_presenter([existing], _reader([incoming]))
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            collections = manager.get_collections()
            assert [col.name for col in collections] == ["My API", "Copy of My API"]
            assert collections[1].id != "keep-id"
            assert collections[1].requests[0].id != "old"
            assert "Copy of My API" in mock_result.call_args[0][1]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_partial_parse_failure_still_imports_valid_entries(
        self, _mock_picker, mock_result, qapp
    ):
        incoming = make_collection("i1", "Good")
        presenter, manager = _make_presenter(
            [], _reader([incoming], ["Broken: missing or empty \"name\" field"])
        )
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            assert [col.name for col in manager.get_collections()] == ["Good"]
            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is True
            assert "Broken" in _args[1]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_save_failure_is_surfaced_as_an_unsuccessful_result(
        self, _mock_picker, mock_result, qapp
    ):
        incoming = make_collection("i1", "Imported")
        presenter, manager = _make_presenter([], _reader([incoming]))
        manager.storage.save_collection.side_effect = OSError("disk full")
        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is False
            assert "disk full" in _args[1]
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_partial_save_failure_recounts_summary_to_durable_membership(
        self, _mock_picker, mock_result, qapp, caplog
    ):
        first = make_collection("c1", "Saved", [make_request("r1", "Req 1")])
        second = make_collection(
            "c2", "Failed", [make_request("r2", "Req 2"), make_request("r3", "Req 3")]
        )
        presenter, manager = _make_presenter([], _reader([first, second]))

        def save_collection(col):
            if col.id == "c2":
                raise OSError("disk full")

        manager.storage.save_collection.side_effect = save_collection

        try:
            with caplog.at_level(logging.ERROR, logger="pypost.core.collection_import_apply"):
                presenter.import_collections()
                _wait_import(lambda: mock_result.call_count >= 1)

            _args, kwargs = mock_result.call_args
            summary = _args[1]
            assert kwargs["success"] is False
            assert "Collections added: 1" in summary
            assert "Requests imported: 1" in summary
            assert "Failed" in summary
            assert "disk full" in summary
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_partial_save_failure_tree_and_manager_match_durable_storage(
        self, _mock_picker, mock_result, qapp
    ):
        existing = make_collection("c0", "Existing", [make_request("r0", "Req 0")])
        first = make_collection("c1", "Saved", [make_request("r1", "Req 1")])
        second = make_collection(
            "c2", "Failed", [make_request("r2", "Req 2"), make_request("r3", "Req 3")]
        )
        durable = [existing]
        presenter, manager = _make_presenter([existing], _reader([first, second]))

        def save_collection(col):
            if col.id == "c2":
                raise OSError("disk full")
            durable.append(col)

        manager.storage.save_collection.side_effect = save_collection
        manager.storage.load_collections.side_effect = lambda: list(durable)

        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is False
            assert "disk full" in _args[1]
            assert [col.name for col in manager.get_collections()] == [
                "Existing",
                "Saved",
            ]
            model = presenter.widget.model()
            assert model.rowCount() == 2
            assert [model.item(r).text() for r in range(2)] == ["Existing", "Saved"]
            assert not any(
                col.name == "Failed" or col.id == "c2"
                for col in manager.get_collections()
            )
            assert not any(
                model.item(r).text() == "Failed" for r in range(model.rowCount())
            )
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_total_save_failure_retains_only_preexisting_durable_collections(
        self, _mock_picker, mock_result, qapp
    ):
        existing = make_collection("c0", "Existing", [make_request("r0", "Req 0")])
        incoming = make_collection("c1", "Failed", [make_request("r1", "Req 1")])
        durable = [existing]
        presenter, manager = _make_presenter([existing], _reader([incoming]))

        manager.storage.save_collection.side_effect = OSError("permission denied")
        manager.storage.load_collections.side_effect = lambda: list(durable)

        try:
            presenter.import_collections()
            _wait_import(lambda: mock_result.call_count >= 1)

            _args, kwargs = mock_result.call_args
            assert kwargs["success"] is False
            assert "permission denied" in _args[1]
            assert [col.name for col in manager.get_collections()] == ["Existing"]
            model = presenter.widget.model()
            assert model.rowCount() == 1
            assert model.item(0).text() == "Existing"
            assert not any(col.name == "Failed" for col in manager.get_collections())
            assert not any(
                model.item(r).text() == "Failed" for r in range(model.rowCount())
            )
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    @patch(_PICKER, return_value=_PATH)
    def test_logs_completed_event_with_counts(
        self, _mock_picker, _mock_result, qapp, caplog
    ):
        incoming = make_collection("i1", "Imported", [make_request("r1", "Ping")])
        presenter, _manager = _make_presenter([], _reader([incoming]))
        try:
            with caplog.at_level(logging.DEBUG):
                presenter.import_collections()
                _wait_import(
                    lambda: any(
                        "collection_import_completed added_count=1" in r.message
                        and "request_count=1" in r.message
                        for r in caplog.records
                    )
                )
            assert any(
                "collection_import_parse_started path=" in r.message
                for r in caplog.records
            )
            assert any(
                "collection_import_busy_cue_shown" in r.message for r in caplog.records
            )
            assert any(
                "collection_import_busy_cue_cleared" in r.message
                for r in caplog.records
            )
            assert any(
                "collection_import_completed added_count=1" in r.message
                and "request_count=1" in r.message
                for r in caplog.records
            )
        finally:
            presenter.panel.close()

    @patch(_INVALID)
    @patch(_PICKER, return_value=_PATH)
    def test_logs_file_invalid_on_parse_failure(
        self, _mock_picker, mock_invalid, qapp, caplog
    ):
        def raise_error(path):
            raise CollectionImportFileError("File is not valid JSON: boom")

        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")], raise_error
        )
        try:
            with caplog.at_level(logging.WARNING, logger=_MODULE):
                presenter.import_collections()
                _wait_import(lambda: mock_invalid.call_count >= 1)

            mock_invalid.assert_called_once()
            assert [col.name for col in manager.get_collections()] == ["Existing"]
            manager.storage.save_collection.assert_not_called()
            invalid_records = [
                r
                for r in caplog.records
                if r.name == _MODULE
                and r.levelno == logging.WARNING
                and "collection_import_file_invalid reason=" in r.message
            ]
            assert any(
                "not valid JSON" in r.message and "boom" in r.message
                for r in invalid_records
            )
            assert not any(
                "reason=no_valid_collections" in r.message for r in caplog.records
            )
        finally:
            presenter.panel.close()

    @patch(_INVALID)
    @patch(_PICKER, return_value=_PATH)
    def test_logs_file_invalid_on_zero_usable_collections(
        self, _mock_picker, mock_invalid, qapp, caplog
    ):
        presenter, manager = _make_presenter(
            [make_collection("c1", "Existing")],
            _reader([], ['Entry 1: missing or empty "name" field']),
        )
        try:
            with caplog.at_level(logging.WARNING, logger=_MODULE):
                presenter.import_collections()
                _wait_import(lambda: mock_invalid.call_count >= 1)

            mock_invalid.assert_called_once()
            assert [col.name for col in manager.get_collections()] == ["Existing"]
            manager.storage.save_collection.assert_not_called()
            assert any(
                r.name == _MODULE
                and r.levelno == logging.WARNING
                and "collection_import_file_invalid reason=no_valid_collections"
                in r.message
                for r in caplog.records
            )
        finally:
            presenter.panel.close()


class TestImportCollectionsEndToEnd:
    @patch(_RESULT)
    def test_real_file_lands_on_disk_and_reloads_with_every_request_field(
        self, mock_result, qapp, tmp_path
    ):
        """Real parser, real RequestManager, real StorageManager — no fakes."""
        source = tmp_path / "shared.json"
        source.write_text(
            json.dumps(
                {
                    "id": "shared-col",
                    "name": "Shared API",
                    "requests": [
                        {
                            "id": "shared-req",
                            "name": "Create user",
                            "method": "POST",
                            "url": "https://api.example.com/users",
                            "headers": {"Authorization": "Bearer {{token}}"},
                            "params": {"dry_run": "true"},
                            "body": '{"name": "ada"}',
                            "body_type": "json",
                            "post_script": "print(response.status_code)",
                            "expose_as_mcp": True,
                            "mcp_description": "Create a user",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        storage = StorageManager(data_dir=tmp_path / "data")
        manager = RequestManager(storage)
        presenter = CollectionsPresenter(manager, FakeStateManager(), FakeMetrics(), {})
        try:
            with patch(_PICKER, return_value=source):
                presenter.import_collections()
                _wait_import(lambda: mock_result.call_count >= 1)

            assert mock_result.call_args[1]["success"] is True
            reloaded = StorageManager(data_dir=tmp_path / "data").load_collections()
            assert [col.name for col in reloaded] == ["Shared API"]
            request = reloaded[0].requests[0]
            assert request.method == "POST"
            assert request.url == "https://api.example.com/users"
            assert request.headers == {"Authorization": "Bearer {{token}}"}
            assert request.params == {"dry_run": "true"}
            assert request.body == '{"name": "ada"}'
            assert request.post_script == "print(response.status_code)"
            assert request.expose_as_mcp is True
            assert request.mcp_description == "Create a user"
        finally:
            presenter.panel.close()

    @patch(_RESULT)
    def test_real_storage_save_failure_reconciles_tree_and_disk(
        self, mock_result, qapp, tmp_path
    ):
        source = tmp_path / "multi.json"
        source.write_text(
            json.dumps(
                [
                    {
                        "id": "new-col-1",
                        "name": "New API 1",
                        "requests": [
                            {
                                "id": "r1",
                                "name": "Get Status",
                                "method": "GET",
                                "url": "https://api.example.com/status",
                            }
                        ],
                    },
                    {
                        "id": "new-col-2",
                        "name": "New API 2",
                        "requests": [
                            {
                                "id": "r2",
                                "name": "Post Data",
                                "method": "POST",
                                "url": "https://api.example.com/data",
                            }
                        ],
                    },
                ]
            ),
            encoding="utf-8",
        )
        storage = StorageManager(data_dir=tmp_path / "data")
        existing = make_collection("c0", "Existing API", [make_request("r0", "Health")])
        storage.save_collection(existing)

        manager = RequestManager(storage)
        presenter = CollectionsPresenter(manager, FakeStateManager(), FakeMetrics(), {})
        presenter.refresh_tree()
        assert presenter.widget.model().rowCount() == 1

        real_save = storage.save_collection

        def failing_save(col):
            if col.name == "New API 2":
                raise OSError("simulated disk full")
            return real_save(col)

        try:
            with patch.object(storage, "save_collection", side_effect=failing_save):
                with patch(_PICKER, return_value=source):
                    presenter.import_collections()
                    _wait_import(lambda: mock_result.call_count >= 1)

            assert mock_result.call_args[1]["success"] is False
            disk_collections = StorageManager(data_dir=tmp_path / "data").load_collections()
            assert {col.name for col in disk_collections} == {"Existing API", "New API 1"}

            assert [col.name for col in manager.get_collections()] == [
                col.name for col in disk_collections
            ]

            model = presenter.widget.model()
            assert model.rowCount() == len(disk_collections)
            assert [model.item(r).text() for r in range(model.rowCount())] == [
                col.name for col in disk_collections
            ]

            for r, col in enumerate(disk_collections):
                item = model.item(r)
                assert item.text() == col.name
                assert item.rowCount() == len(col.requests)
                for req_idx, req in enumerate(col.requests):
                    assert item.child(req_idx).text() == f"{req.method} {req.name}"
        finally:
            presenter.panel.close()
