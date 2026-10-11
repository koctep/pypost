"""PYPOST-1355: persisted independent copies of Built-in MCP collections."""
from __future__ import annotations

from contextlib import ExitStack
import inspect
import logging
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from pypost.core.builtin_collections import BuiltinCollectionView
from pypost.core.mcp_server_registry import McpServerStatus
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.core.request_manager import RequestManager
from pypost.core.storage import StorageManager
from pypost.models.collection_variable import CollectionVariable
from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import Collection, Environment, LibraryCollectionLink, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.models.websocket import WebSocketConnection
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog, _McpServerEditor
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.presenters.mcp_controls_presenter import McpControlsPresenter
from tests.helpers.collections_tree import FakeStateManager

pytestmark = pytest.mark.timeout(30)
COLLECTION_PATH = "collections/test.json"
CREATION_LOGGER = "pypost.ui.presenters.collections_presenter_creation"


@pytest.fixture
def builtin(tmp_path):
    root = tmp_path / "bundle"
    (root / "collections").mkdir(parents=True)
    (root / "environments").mkdir()
    (root / "environments/test.json").write_text(
        "[" + Environment(name="Paired").model_dump_json() + "]", encoding="utf-8"
    )
    source = Collection(
        id="shipped", name="Internal name", description="A shipped API", version="2.0.0",
        variables=[CollectionVariable(name="PATH", default="items", required=True)],
        presets={"defaults": {"headers": {"X-Mode": "original"}}},
        requests=[RequestData(
            id="shipped-request", name="Fetch", url="https://example.invalid/{{PATH}}",
            method="POST", headers={"X-Token": "{{TOKEN}}"}, params={"limit": "2"},
            body='{"ok": true}', post_script="response.status_code", expose_as_mcp=True,
            mcp_description="Fetch data",
        )],
    )
    path = root / COLLECTION_PATH
    path.write_text(source.model_dump_json(), encoding="utf-8")
    (root / "pypost-library.yaml").write_text(
        'schema_version: "1.0.0"\nid: pypost-examples\nname: Test\n'
        'version: "1.0.0"\ncollections: [collections/test.json]\n', encoding="utf-8"
    )
    (root / "builtin-collections.yaml").write_text(
        'entries:\n  - collection: collections/test.json\n'
        '    environment: environments/test.json\n    name: Test MCP\n',
        encoding="utf-8",
    )
    view = BuiltinCollectionView(PredefinedLibraryService(root=root))
    assert len(view.list_entries()) == 1
    assert view.load_collection(COLLECTION_PATH).requests[0].id == "shipped-request"
    return view, path


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr("pypost.core.storage.user_data_dir", lambda *args: str(tmp_path / "data"))
    return StorageManager()


@pytest.fixture
def owner(qapp, storage):
    manager = RequestManager(storage)
    presenter = CollectionsPresenter(manager, FakeStateManager(), storage=storage)
    presenter.refresh_tree()
    yield presenter
    assert presenter.teardown(timeout_ms=5000)
    presenter.widget.close()


@pytest.fixture
def editors(qapp):
    widgets = []
    yield widgets
    for widget in widgets:
        widget.close()


def creation(owner):
    callback = getattr(owner, "create_workspace_collection", None)
    assert callable(callback), "CollectionsPresenter must own durable workspace collection creation"
    return callback


def source_for_copy(view):
    source = view.load_collection(COLLECTION_PATH)
    source.name = view.list_entries()[0].name
    return source


def copy_button(widget):
    buttons = [button for button in widget.findChildren(QPushButton)
               if button.text() == "Copy for editing"]
    assert len(buttons) == 1, "Built-in editor must provide Copy for editing"
    return buttons[0]


def has_update_note(widget):
    return any(label.isVisible() and "updates" in label.text().lower()
               and "no longer" in label.text().lower()
               for label in widget.findChildren(QLabel))


def make_editor(editors, builtin, collections, callback=None, configuration=None):
    view, _ = builtin
    kwargs = dict(
        collections=list(collections()), environments=[Environment(id="env", name="Selected")],
        configuration=configuration, default_environment=None, default_host="127.0.0.1",
        default_port=1080, builtin_view=view,
    )
    if callback is not None:
        parameters = inspect.signature(_McpServerEditor).parameters
        assert "create_collection" in parameters and "get_collections" in parameters, (
            "Editor must accept the canonical creation capability and live collection provider"
        )
        kwargs.update(create_collection=callback, get_collections=collections)
    widget = _McpServerEditor(**kwargs)
    editors.append(widget)
    widget._collection_source.setCurrentIndex(widget._collection_source.findData("builtin"))
    widget._environment.setCurrentIndex(widget._environment.findData("env"))
    widget.show()
    return widget


def bundled_configuration():
    return McpServerConfiguration(
        id="server", name="Bundled", port=1080, environment_id="env", enabled=True,
        bundled_library=True, library_id="pypost-examples", manifest_id="pypost-examples",
        library_collection_path=COLLECTION_PATH,
    )


def make_manager(editors, builtin, owner, configurations, save):
    dialog = McpServersDialog(
        configurations=lambda: configurations,
        status_for=lambda server_id: McpServerStatus(server_id, "stopped"),
        save=save, remove=MagicMock(), start=MagicMock(), stop=MagicMock(), activity=lambda _: [],
        collections=owner._request_manager.get_collections,
        environments=lambda: [Environment(id="env", name="Selected")],
        legacy_environment=lambda: None, legacy_host="127.0.0.1", legacy_port=1080,
        builtin_view=builtin[0], create_collection=creation(owner),
    )
    editors.append(dialog)
    return dialog


def test_canonical_creation_persists_before_publish_and_supports_tree_editing(
    owner, storage, builtin, monkeypatch, caplog
):
    view, path = builtin
    before = path.read_bytes()
    source = source_for_copy(view)
    source.description = "PRIVATE_DESCRIPTION"
    source.requests[0].headers["Authorization"] = "PRIVATE_SECRET"
    source.requests[0].body = "PRIVATE_BODY"
    source.library_link = LibraryCollectionLink(
        library_id="source", collection_path=COLLECTION_PATH
    )
    original = source.model_dump(mode="json")
    saved = []
    save = storage.save_collection

    def observe_save(candidate):
        assert owner._request_manager.get_collections() == []
        assert owner.widget.model().rowCount() == 0
        save(candidate)
        saved.append(candidate.id)

    monkeypatch.setattr(storage, "save_collection", observe_save)
    changed = []
    owner.collections_changed.connect(lambda: changed.append(True))
    with caplog.at_level(logging.INFO, logger=CREATION_LOGGER):
        copy = creation(owner)(source)
    assert copy is not None and UUID(copy.id) and copy.id != source.id
    assert copy.name == "Test MCP (copy)" and copy.library_link is None
    assert saved == [copy.id] and changed == [True]
    messages = [record.getMessage() for record in caplog.records
                if record.name == CREATION_LOGGER]
    assert messages == [
        f"workspace_collection_creation_admitted collection_id={copy.id} "
        "existing_count=0 request_count=1",
        f"workspace_collection_creation_succeeded collection_id={copy.id} "
        "request_count=1 collection_count=1",
    ]
    assert all(private not in " ".join(messages) for private in (
        "PRIVATE_DESCRIPTION", "PRIVATE_SECRET", "PRIVATE_BODY", "Test MCP", "example.invalid"
    ))
    assert owner.collection_by_id(copy.id) is copy
    assert owner._request_manager.find_request(copy.requests[0].id) == (copy.requests[0], copy)
    assert storage.load_collections()[0].model_dump() == copy.model_dump()
    item = owner.widget.model().item(0)
    assert item.text() == copy.name and item.rowCount() == 1
    opened = []
    owner.open_request_in_tab.connect(opened.append)
    owner._on_collection_clicked(item.child(0).index())
    assert len(opened) == 1 and opened[0].id == copy.requests[0].id
    assert opened[0] is not copy.requests[0]
    assert copy.requests[0].model_dump(exclude={"id"}) == (
        source.requests[0].model_dump(exclude={"id"})
    )
    assert copy.description == source.description and copy.version == source.version
    assert copy.variables == source.variables
    assert copy.presets == source.presets
    assert source.model_dump(mode="json") == original and path.read_bytes() == before


def test_repeated_copies_reserve_names_and_all_item_ids_and_edit_independently(
    owner, storage, builtin
):
    view, path = builtin
    before = path.read_bytes()
    source = source_for_copy(view)
    source.websockets = [WebSocketConnection(id="ws", name="Socket", url="wss://example.invalid")]
    source.mcp_clients = [
        McpClientConnection(id="client", name="Client", url="https://example.invalid")
    ]
    existing = source.model_copy(deep=True)
    existing.name = "Test MCP (copy)"
    storage.save_collection(existing)
    owner._request_manager.apply_loaded_collections([existing])
    owner.refresh_tree()
    first = creation(owner)(source)
    second = creation(owner)(source)
    assert first is not None and second is not None
    assert [first.name, second.name] == ["Test MCP (copy) (2)", "Test MCP (copy) (3)"]
    assert len({source.id, first.id, second.id}) == 3
    for attribute in ("requests", "websockets", "mcp_clients"):
        assert len({getattr(col, attribute)[0].id for col in (existing, first, second)}) == 3
        assert getattr(first, attribute)[0].model_dump(exclude={"id"}) == (
            getattr(source, attribute)[0].model_dump(exclude={"id"})
        )
    assert owner._request_manager.rename_request(first.requests[0].id, "Edited first")
    loaded = {col.id: col for col in storage.load_collections()}
    assert loaded[first.id].requests[0].name == "Edited first"
    assert loaded[second.id].requests[0].name == loaded[existing.id].requests[0].name == "Fetch"
    first.presets["defaults"]["headers"]["X-Mode"] = "changed"
    assert second.presets == existing.presets == source.presets
    assert path.read_bytes() == before


@pytest.mark.parametrize("busy", ["load", "import", "teardown"])
def test_creation_rejects_busy_or_disposed_owner_without_publishing(
    owner, storage, builtin, monkeypatch, caplog, busy
):
    callback = creation(owner)
    with monkeypatch.context() as admission_patch:
        if busy == "teardown":
            assert owner.teardown(timeout_ms=5000)
        elif busy == "load":
            admission_patch.setattr(owner._async_loader, "is_busy", lambda: True)
        else:
            admission_patch.setattr(owner._import_actions, "is_busy", lambda: True)
        save = MagicMock(wraps=storage.save_collection)
        admission_patch.setattr(storage, "save_collection", save)
        with caplog.at_level(logging.INFO, logger=CREATION_LOGGER):
            assert callback(source_for_copy(builtin[0])) is None
        reason = {"load": "load_busy", "import": "import_busy", "teardown": "teardown"}[busy]
        messages = [record.getMessage() for record in caplog.records
                    if record.name == CREATION_LOGGER]
        assert messages == [f"workspace_collection_creation_rejected reason={reason}"]
        save.assert_not_called()
        assert owner._request_manager.get_collections() == []
        assert owner.widget.model().rowCount() == 0


def test_partial_save_failure_cleans_only_new_id_and_allows_retry(
    owner, storage, builtin, monkeypatch, caplog
):
    callback = creation(owner)
    storage.collections_path.mkdir(parents=True, exist_ok=True)
    legacy = storage.collections_path / "Test MCP (copy).json"
    legacy.write_bytes(b"unrelated legacy file")
    attempted = []
    save = storage.save_collection

    def fail(candidate):
        attempted.append(candidate.id)
        (storage.collections_path / f"{candidate.id}.json").write_bytes(b'{"partial":')
        raise OSError("PRIVATE_CREDENTIAL")

    monkeypatch.setattr(storage, "save_collection", fail)
    with caplog.at_level(logging.WARNING, logger=CREATION_LOGGER):
        with pytest.raises(OSError):
            callback(source_for_copy(builtin[0]))
    assert len(attempted) == 1
    assert not (storage.collections_path / f"{attempted[0]}.json").exists()
    assert legacy.read_bytes() == b"unrelated legacy file"
    assert owner._request_manager.get_collections() == [] and owner.widget.model().rowCount() == 0
    assert "PRIVATE_CREDENTIAL" not in caplog.text
    assert any(record.name == CREATION_LOGGER and record.getMessage() == (
        f"workspace_collection_creation_failed collection_id={attempted[0]} reason=save"
    ) for record in caplog.records)
    assert not any("cleanup_failed" in record.getMessage() for record in caplog.records)
    monkeypatch.setattr(storage, "save_collection", save)
    copy = callback(source_for_copy(builtin[0]))
    assert copy is not None and owner.collection_by_id(copy.id) is copy


def test_cleanup_failure_preserves_save_error_and_logs_safely_without_switching(
    owner, storage, builtin, editors, monkeypatch, caplog
):
    callback = creation(owner)
    original_error = OSError("PRIVATE_SAVE_CREDENTIAL")
    attempted, deleted, outcomes = [], [], []
    changed = []
    owner.collections_changed.connect(lambda: changed.append(True))
    storage.collections_path.mkdir(parents=True, exist_ok=True)

    def fail_save(candidate):
        attempted.append(candidate.id)
        (storage.collections_path / f"{candidate.id}.json").write_bytes(b'{"partial":')
        raise original_error

    def fail_delete(collection_id, *, collection_name=None):
        deleted.append((collection_id, collection_name))
        raise OSError("PRIVATE_DELETE_CREDENTIAL")

    def observe_outcome(source):
        try:
            return callback(source)
        except OSError as error:
            outcomes.append(error)
            raise

    monkeypatch.setattr(storage, "save_collection", fail_save)
    monkeypatch.setattr(storage, "delete_collection", fail_delete)
    widget = make_editor(
        editors, builtin, owner._request_manager.get_collections, observe_outcome
    )
    button = copy_button(widget)
    with caplog.at_level(logging.WARNING, logger="pypost"):
        button.click()
    assert len(attempted) == 1 and deleted == [(attempted[0], None)]
    assert outcomes == [original_error] and outcomes[0] is original_error
    assert owner._request_manager.get_collections() == []
    assert owner.widget.model().rowCount() == 0 and changed == []
    assert widget._collection_source.currentData() == "builtin"
    assert widget._collection.findData(attempted[0]) == -1
    assert widget._environment.currentData() == "env" and button.isEnabled()
    assert widget._error.text()
    messages = [record.getMessage() for record in caplog.records]
    cleanup = [record for record in caplog.records if record.name == CREATION_LOGGER
               and record.getMessage().startswith("workspace_collection_cleanup_failed")]
    assert len(cleanup) == 1 and cleanup[0].levelno == logging.ERROR
    assert cleanup[0].getMessage() == (
        f"workspace_collection_cleanup_failed collection_id={attempted[0]}"
    )
    assert cleanup[0].exc_info is None
    assert not any("creation_succeeded" in message for message in messages)
    assert "PRIVATE_SAVE_CREDENTIAL" not in caplog.text + widget._error.text()
    assert "PRIVATE_DELETE_CREDENTIAL" not in caplog.text + widget._error.text()


def test_missing_capability_disables_action_and_preserves_manual_selection(editors, builtin):
    workspace = [Collection(id="manual", name="Manual")]
    widget = make_editor(editors, builtin, lambda: workspace)
    button = copy_button(widget)
    assert button.isVisible() and not button.isEnabled()
    assert has_update_note(widget)
    button.click()
    assert widget._collection_source.currentData() == "builtin" and len(workspace) == 1
    widget._collection_source.setCurrentIndex(widget._collection_source.findData("workspace"))
    assert not button.isVisible()
    widget._collection.setCurrentIndex(widget._collection.findData("manual"))
    widget._accept_if_complete()
    assert widget.configuration().collection_id == "manual"
    widget._server_type.setCurrentIndex(widget._server_type.findData("proxy"))
    assert not button.isVisible()


@pytest.mark.parametrize("save", [False, True])
def test_copy_persists_but_only_save_reassociates_existing_server(
    owner, storage, builtin, editors, save
):
    original = bundled_configuration()
    other = McpServerConfiguration(
        id="other", collection_id="unrelated", environment_id="env", port=1081
    )
    configurations = [original, other]
    before = [config.model_dump() for config in configurations]
    widget = make_editor(editors, builtin, owner._request_manager.get_collections,
                         creation(owner), original)
    button = copy_button(widget)
    assert button.isVisible() and button.isEnabled() and has_update_note(widget)
    button.click()
    copies = owner._request_manager.get_collections()
    assert len(copies) == 1 and copies[0].name == "Test MCP (copy)"
    assert widget._collection_source.currentData() == "workspace"
    assert widget._collection.currentData() == copies[0].id
    assert widget._environment.currentData() == "env" and has_update_note(widget)
    assert [config.model_dump() for config in configurations] == before
    if save:
        widget._accept_if_complete()
        assert widget.result() == 1
        result = widget.configuration()
        assert result.id == original.id and result.collection_id == copies[0].id
        assert result.environment_id == "env" and result.enabled is True
        assert result.bundled_library is False
        assert result.library_id is result.manifest_id is result.library_collection_path is None
        assert result.library_collection_index is None
    else:
        widget.reject()
        assert widget.result() == 0 and original.bundled_library is True
    saved = []

    def persist_server(configuration):
        saved.append(configuration)
        configurations[0] = configuration

    dialog = make_manager(editors, builtin, owner, configurations, persist_server)
    dialog._table.selectRow(0)
    with patch("pypost.ui.dialogs.mcp_servers_dialog._McpServerEditor", return_value=widget):
        with patch.object(widget, "exec", return_value=widget.result()):
            dialog._edit()
    if save:
        assert len(saved) == 1 and configurations[0].collection_id == copies[0].id
        assert configurations[0].bundled_library is False
    else:
        assert saved == [] and configurations[0].model_dump() == before[0]
    assert configurations[1].model_dump() == before[1]
    assert storage.load_collections()[0].id == copies[0].id


def test_new_server_cancel_keeps_workspace_copy_without_server(owner, storage, builtin, editors):
    widget = make_editor(editors, builtin, owner._request_manager.get_collections, creation(owner))
    copy_button(widget).click()
    widget.reject()
    save = MagicMock()
    dialog = make_manager(editors, builtin, owner, [], save)
    with patch("pypost.ui.dialogs.mcp_servers_dialog._McpServerEditor", return_value=widget):
        with patch.object(widget, "exec", return_value=0):
            dialog._add()
    save.assert_not_called()
    assert widget.result() == 0 and len(storage.load_collections()) == 1


@pytest.mark.parametrize("failure", ["reject", "save", "load"])
def test_editor_failure_keeps_builtin_and_environment_then_retries(
    editors, builtin, monkeypatch, caplog, failure
):
    workspace = []
    attempts = []

    def callback(source):
        attempts.append(source)
        if len(attempts) == 1 and failure == "reject":
            return None
        if len(attempts) == 1 and failure == "save":
            raise OSError("PRIVATE_CREDENTIAL")
        copy = source.model_copy(deep=True)
        copy.id, copy.name = "published", "Test MCP (copy)"
        workspace.append(copy)
        return copy

    widget = make_editor(editors, builtin, lambda: workspace, callback)
    button = copy_button(widget)
    load = builtin[0].load_collection
    if failure == "load":
        monkeypatch.setattr(
            builtin[0], "load_collection", MagicMock(side_effect=OSError("PRIVATE_CREDENTIAL"))
        )
    button.click()
    assert workspace == [] and widget._collection_source.currentData() == "builtin"
    assert widget._environment.currentData() == "env" and widget._error.text()
    assert button.isEnabled() and "PRIVATE_CREDENTIAL" not in widget._error.text() + caplog.text
    if failure == "load":
        monkeypatch.setattr(builtin[0], "load_collection", load)
    button.click()
    assert widget._collection_source.currentData() == "workspace"
    assert widget._collection.currentData() == "published" and len(workspace) == 1


def test_controls_and_dialog_forward_canonical_callback(owner, builtin, editors, qapp):
    callback = creation(owner)
    controls = McpControlsPresenter(
        mcp_manager=MagicMock(), settings_provider=AppSettings,
        get_collections=owner._request_manager.get_collections, get_environments=lambda: [],
        current_environment=lambda: None, metrics=MagicMock(), dialog_parent=QWidget(),
    )
    setter = getattr(controls, "set_collection_creator", None)
    assert callable(setter), "Controls must expose canonical collection creation injection"
    setter(callback)
    controls.set_server_controller(MagicMock())
    with patch("pypost.ui.presenters.mcp_controls_presenter.McpServersDialog") as factory:
        controls._open_mcp_servers()
        assert factory.call_args.kwargs["create_collection"] == callback
    assert "create_collection" in inspect.signature(McpServersDialog).parameters
    dialog = McpServersDialog(
        configurations=lambda: [], status_for=MagicMock(), save=MagicMock(), remove=MagicMock(),
        start=MagicMock(), stop=MagicMock(), activity=lambda _: [],
        collections=owner._request_manager.get_collections, environments=lambda: [],
        legacy_environment=lambda: None, legacy_host="127.0.0.1", legacy_port=1080,
        builtin_view=builtin[0], create_collection=callback,
    )
    editors.append(dialog)
    with patch("pypost.ui.dialogs.mcp_servers_dialog._McpServerEditor") as factory:
        factory.return_value.exec.return_value = 0
        dialog._add()
        assert factory.call_args.kwargs["create_collection"] == callback
        assert factory.call_args.kwargs["get_collections"]() == (
            owner._request_manager.get_collections()
        )


def test_main_window_installs_collections_owner_callback(qapp):
    from pypost.ui.main_window import MainWindow

    collections, env = MagicMock(), MagicMock()
    with ExitStack() as stack:
        for name in (
            "StateManager", "TabsPresenter", "HistoryPanel", "McpServerSettingsController"
        ):
            mocked = stack.enter_context(patch(f"pypost.ui.main_window.{name}"))
            if name == "StateManager":
                mocked.return_value.settings = AppSettings()
        stack.enter_context(patch(
            "pypost.ui.main_window.CollectionsPresenter", return_value=collections
        ))
        stack.enter_context(patch("pypost.ui.main_window.EnvPresenter", return_value=env))
        for name in ("_build_layout", "_create_menu_bar", "_setup_shortcuts", "apply_settings"):
            stack.enter_context(patch.object(MainWindow, name))
        stack.enter_context(patch("pypost.ui.main_window.wire_presenter_signals"))
        window = MainWindow(
            metrics=MagicMock(), template_service=MagicMock(), config_manager=MagicMock(),
            history_manager=MagicMock(), storage=MagicMock(), request_manager=MagicMock(),
        )
        try:
            env.mcp_controls.set_collection_creator.assert_called_once_with(
                collections.create_workspace_collection
            )
        finally:
            window.deleteLater()
