"""PYPOST-1280 red contracts for library-backed MCP server collections."""

from __future__ import annotations

from pathlib import Path
import json
from tempfile import TemporaryDirectory
from threading import Event
from typing import Any, Callable

import pytest

from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.core.config_manager import ConfigManager
from pypost.core.collection_serializer import write_collection_file
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.ui.dialogs.mcp_servers_dialog import _McpServerEditor
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog
from pypost.ui.mcp_server_controller import ConfigManagerSettingsStore
from pypost.core.mcp_server_registry import McpServerStatus
from PySide6.QtWidgets import QDialogButtonBox

pytestmark = pytest.mark.timeout(60)


class _ControlledWorker:
    """Offline worker double whose completion can be delivered after cancellation."""

    def __init__(self, operation: Callable[[], Any]) -> None:
        self.operation = operation
        self.started = Event()
        self.cancelled = False
        self.result_handler: Callable[[Any], None] | None = None

    def start(self, result_handler: Callable[[Any], None]) -> None:
        self.result_handler = result_handler
        self.started.set()

    def cancel(self) -> None:
        self.cancelled = True

    def deliver_late_result(self) -> None:
        assert self.result_handler is not None
        self.result_handler(self.operation())


class _LibraryService:
    def __init__(self, root: Path):
        self.root = root

    def list_manifest_collections(self, _library_id: str):
        return [_library_selection()]

    def list_connections(self):
        return []


def _editor(qapp):
    return _McpServerEditor(
        collections=[Collection(id="workspace", name="Workspace")],
        environments=[Environment(id="dev", name="Development")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
    )


def _require(module_name: str, attribute: str) -> Any:
    try:
        module = __import__(module_name, fromlist=[attribute])
    except ModuleNotFoundError as error:
        pytest.fail(f"missing PYPOST-1280 contract module: {module_name}: {error}")
    value = getattr(module, attribute, None)
    assert value is not None, f"missing PYPOST-1280 contract: {module_name}.{attribute}"
    return value


def _library_selection() -> dict[str, Any]:
    return {
        "library_id": "library-1",
        "manifest_id": "library-1",
        "path": "collections/orders.json",
        "index": 1,
    }


def _real_library_service(tmp_path: Path) -> LibraryManagerService:
    root = tmp_path / "library"
    (root / "collections").mkdir(parents=True)
    (root / "pypost-library.json").write_text(json.dumps({
        "id": "library-1", "name": "Test library",
        "collections": ["collections/orders.json"],
        "variables": [
            {"name": "host", "type": "string", "default": "default.example"},
            {"name": "token", "type": "string", "secret": True, "required": True},
        ],
        "presets": {"dev": {"token": "library-token"}},
    }), encoding="utf-8")
    write_collection_file(Collection(id="orders", name="Orders"), root / "collections/orders.json")
    service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=LocalOverlayManager(tmp_path / "overlays"),
    )
    service.connect_local_directory(root)
    return service


def test_library_source_picker_is_async_and_discards_cancelled_late_results(qapp):
    with TemporaryDirectory() as directory:
        worker = _ControlledWorker(
            lambda: {
                "library_id": "library-1",
                "manifest_id": "manifest-1",
                "path": "collections/orders.json",
                "index": 1,
            }
        )
        picker = _require(
            "pypost.ui.mcp_library_source_picker", "LibraryMcpSourcePicker"
        )(
            library_service=_LibraryService(Path(directory)),
            worker_factory=lambda operation: worker,
        )

        request_id = picker.begin_manifest_listing("library-1")
        assert worker.started.wait(timeout=1)
        picker.cancel(request_id)
        worker.deliver_late_result()

        assert picker.busy is False
        assert picker.selected_collection is None
        assert picker.overlay_writes == []


def test_library_source_picker_cancels_connected_library_listing(qapp):
    workers = []

    def factory(operation):
        worker = _ControlledWorker(operation)
        workers.append(worker)
        return worker

    picker = _require(
        "pypost.ui.mcp_library_source_picker", "LibraryMcpSourcePicker"
    )(
        library_service=_LibraryService(Path(".")),
        worker_factory=factory,
    )
    received = []
    request_id = picker.begin_library_listing(on_complete=received.append)
    assert workers[0].started.wait(timeout=1)
    picker.cancel(request_id)
    workers[0].deliver_late_result()
    assert received == []
    assert picker.selected_collection is None


def test_valid_library_handoff_propagates_through_controller_registry_and_reload(tmp_path):
    selection = _library_selection()
    for field in (
        "library_id",
        "manifest_id",
        "library_collection_path",
        "library_collection_index",
    ):
        assert field in McpServerConfiguration.model_fields, (
            f"missing persisted library identity field: {field}"
        )
    configuration = McpServerConfiguration(
        id="server-1",
        port=1080,
        environment_id="dev",
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
    )
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    registry = _require("pypost.core.mcp_server_registry", "MCPServerRegistry")
    facade = _require("pypost.core.library_runtime_resolver", "LibraryRuntimeResolver")

    service = _real_library_service(tmp_path)
    handoff = facade(library_service=service).resolve(selection, environment_id="dev")
    registry_instance = registry(library_service=service)
    controller_instance = controller_class(registry=registry_instance, library_service=service)
    controller_instance.save_library_server(configuration, selection, handoff)
    installed = registry_instance.configuration("server-1")
    assert installed.library_selection == selection

    reloaded = controller_instance.reload_mcp_servers()[0]
    assert reloaded.library_selection == selection
    assert reloaded.environment_id == "dev"


def test_library_identity_round_trips_through_real_store_and_second_controller(tmp_path):
    manager = ConfigManager(config_dir=tmp_path)
    selection = _library_selection()
    configuration = McpServerConfiguration(
        id="disk-server", port=1082, environment_id="dev",
        library_id=selection["library_id"], manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"], library_collection_index=selection["index"],
    )
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    service = _real_library_service(tmp_path)
    first = controller_class(config_manager=manager, library_service=service)
    first.save_library_server(configuration, selection, object())

    second = controller_class(config_manager=manager, library_service=service)
    assert second.reload_mcp_servers()[0].library_selection == selection
    assert second.registry.configuration("disk-server").library_selection == selection


def test_library_environment_draft_precedence_masks_secrets_and_validates_types():
    resolver = _require("pypost.core.library_runtime_resolver", "LibraryRuntimeResolver")
    result = resolver().prepare_environment(
        defaults={"host": "default.example", "token": "default-token"},
        profile={"host": "profile.example"},
        overrides={"host": "override.example"},
        secrets={"token": "secret-token"},
        declarations={
            "host": {"type": "string", "required": True},
            "token": {"type": "string", "required": True, "secret": True},
        },
    )
    assert result.values == {"host": "override.example", "token": "secret-token"}
    assert result.provenance == {"host": "override", "token": "secret"}
    assert "secret-token" not in result.safe_diagnostics
    with pytest.raises(ValueError, match="required|type"):
        resolver().prepare_environment(
            defaults={},
            profile={},
            overrides={"host": 42},
            secrets={},
            declarations={"host": {"type": "string", "required": True}},
        )


@pytest.mark.parametrize(("case", "selection", "profile"), [
    ("manifest_invalid", {**_library_selection(), "manifest_id": "wrong-manifest"}, "dev"),
    ("collection_missing", {**_library_selection(), "path": "collections/missing.json"}, "dev"),
    ("profile_missing", _library_selection(), "missing-profile"),
])
def test_invalid_manifest_collection_and_profile_are_distinct_recoverable_errors(
    tmp_path: Path, case: str, selection: dict[str, Any], profile: str
):
    facade = _require("pypost.core.library_runtime_resolver", "LibraryRuntimeResolver")
    service = _real_library_service(tmp_path)
    with pytest.raises(Exception) as error:
        facade(library_service=service).resolve(selection, environment_id=profile)
    assert case in str(error.value).lower()


@pytest.mark.parametrize("candidate", [False, True])
def test_explicit_invalid_overlay_profile_is_never_synthesized(tmp_path, candidate):
    service = _real_library_service(tmp_path)
    overlay = LocalLibraryOverlay(library_id="library-1", active_profile="not-a-profile")
    if not candidate:
        service.overlay_manager.save_overlay(overlay)
    resolver = _require(
        "pypost.core.library_runtime_resolver", "LibraryRuntimeResolver"
    )(library_service=service)
    with pytest.raises(ValueError, match="profile_missing"):
        resolver.resolve(_library_selection(), "dev", candidate_overlay=overlay if candidate else None)


def test_persistence_failure_preserves_prior_row_overlay_and_writes_no_overlay(tmp_path):
    previous = {
        "server": {"id": "server-1", "library_id": "old-library"},
        "overlay": {"host": "old.example", "token": "old-secret"},
    }
    store = _require("pypost.ui.mcp_server_controller", "CheckedSettingsStore")(
        root=tmp_path, fail_commit=True
    )
    transaction = _require(
        "pypost.ui.mcp_server_controller", "LibraryMcpSaveTransaction"
    )(
        store=store,
        previous=previous,
        candidate={"server": {"id": "server-1", "library_id": "new-library"}},
        overlay={"host": "new.example"},
    )
    result = transaction.commit()
    assert result.committed is False
    assert result.category == "persistence_failure"
    assert store.read_snapshot() == previous
    assert store.overlay_write_count == 0
    assert transaction.rollback().restored is True


def test_workspace_and_proxy_rows_are_independent_from_library_validation_failure(qapp):
    registry_class = _require("pypost.core.mcp_server_registry", "MCPServerRegistry")
    registry = registry_class()
    assert hasattr(registry, "install"), "missing registry install contract"
    workspace = McpServerConfiguration(
        id="workspace-server", collection_id="workspace", environment_id="dev", port=1080
    )
    proxy = McpServerConfiguration(
        id="proxy-server", server_type="proxy", upstream_url="http://proxy",
        environment_id="dev", port=1081,
    )
    registry.install(workspace)
    registry.install(proxy)

    with pytest.raises(Exception, match="library|manifest|collection"):
        registry.install_library_candidate(
            {"id": "library-server", "library_id": "missing"}
        )

    assert registry.configuration("workspace-server") == workspace
    assert registry.configuration("proxy-server") == proxy
    assert registry.configuration("library-server") is None


def test_editor_exposes_connected_library_identity(qapp, tmp_path):
    service = _real_library_service(tmp_path)
    workers = []

    def factory(operation):
        worker = _ControlledWorker(operation)
        workers.append(worker)
        return worker

    editor = _McpServerEditor(
        collections=[Collection(id="workspace", name="Workspace")],
        environments=[Environment(id="dev", name="Development")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        library_service=service,
        library_worker_factory=factory,
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    assert len(workers) == 1
    workers[0].deliver_late_result()
    assert editor._library.findData("library-1") >= 0
    assert len(workers) == 2
    workers[1].deliver_late_result()
    assert editor._library_collection.count() == 1
    editor.close()


def test_editor_restores_second_collection_by_full_stable_identity(qapp):
    first = {
        **_library_selection(),
        "path": "collections/first.json",
        "index": 0,
        "name": "First",
    }
    second = {
        **_library_selection(),
        "path": "collections/second.json",
        "index": 1,
        "name": "Second",
    }
    configuration = McpServerConfiguration(
        id="edit-server", port=1086, environment_id="dev",
        library_id="library-1", manifest_id="library-1",
        library_collection_path=second["path"], library_collection_index=second["index"],
    )
    editor = _McpServerEditor(
        collections=[], environments=[Environment(id="dev", name="Development")],
        configuration=configuration, default_environment=None,
        default_host="127.0.0.1", default_port=1080,
        library_selections=[first, second],
    )
    editor._replace_library_selections([first, second])
    assert editor.library_selection() == second
    editor.close()


def test_dialog_refresh_describes_library_collection(qapp, tmp_path):
    service = _real_library_service(tmp_path)
    configuration = McpServerConfiguration(
        id="library-row", port=1087, environment_id="dev",
        library_id="library-1", manifest_id="library-1",
        library_collection_path="collections/orders.json", library_collection_index=0,
    )
    dialog = McpServersDialog(
        configurations=lambda: [configuration],
        status_for=lambda _id: McpServerStatus("library-row", "stopped"),
        save=lambda _config: None, remove=lambda _id: None,
        start=lambda _id: None, stop=lambda _id: None,
        activity=lambda _id: [], collections=lambda: [], environments=lambda: [],
        legacy_environment=lambda: None, legacy_host="127.0.0.1", legacy_port=1080,
        library_service=service,
    )
    target = dialog._table.item(0, dialog._COLUMNS.index("Collection")).text()
    assert "Orders" in target
    assert "library-1" in target
    dialog.close()


def test_editor_library_handoff_contains_profile_overrides_and_masked_secret(qapp, tmp_path):
    service = _real_library_service(tmp_path)
    workers = []

    def factory(operation):
        worker = _ControlledWorker(operation)
        workers.append(worker)
        return worker

    editor = _McpServerEditor(
        collections=[Collection(id="workspace", name="Workspace")],
        environments=[Environment(id="dev", name="Development")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        library_service=service,
        library_worker_factory=factory,
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    workers[0].deliver_late_result()
    workers[1].deliver_late_result()
    editor._library_variable_fields["host"].setText("override.example")
    editor._library_variable_fields["token"].setText("typed-secret")
    assert editor._library_variable_fields["token"].echoMode() != 0
    handoff = editor.library_handoff()
    assert handoff["overlay"]["active_profile"] == "dev"
    assert handoff["overlay"]["overrides"] == {"host": "override.example"}
    assert handoff["overlay"]["secrets"] == {"token": "typed-secret"}
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    controller = controller_class(library_service=service)
    controller.save_library_server(editor.configuration(), editor.library_selection(), handoff)
    saved = service.overlay_manager.get_overlay("library-1")
    assert saved.overrides == {"host": "override.example"}
    assert saved.secrets == {"token": "typed-secret"}
    editor.close()


def test_editor_cancel_button_cancels_active_discovery_and_ignores_late_results(qapp, tmp_path):
    service = _real_library_service(tmp_path)
    workers = []

    def factory(operation):
        worker = _ControlledWorker(operation)
        workers.append(worker)
        return worker

    editor = _McpServerEditor(
        collections=[Collection(id="workspace", name="Workspace")],
        environments=[Environment(id="dev", name="Development")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        library_service=service,
        library_worker_factory=factory,
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    assert workers[0].started.wait(timeout=1)
    workers[0].deliver_late_result()
    assert workers[1].started.wait(timeout=1)
    cancel = editor.findChild(QDialogButtonBox).button(
        QDialogButtonBox.StandardButton.Cancel
    )
    cancel.click()
    assert editor.result() == editor.DialogCode.Rejected
    assert editor._library_picker.busy is False
    assert workers[1].cancelled is True
    workers[1].deliver_late_result()
    assert editor._library_collection.count() == 0
    editor.close()


def test_dialog_save_configuration_passes_actual_editor_handoff(tmp_path, qapp):
    service = _real_library_service(tmp_path)
    workers = []

    def factory(operation):
        worker = _ControlledWorker(operation)
        workers.append(worker)
        return worker

    editor = _McpServerEditor(
        collections=[Collection(id="workspace", name="Workspace")],
        environments=[Environment(id="dev", name="Development")],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1080,
        library_service=service,
        library_worker_factory=factory,
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    workers[0].deliver_late_result()
    workers[1].deliver_late_result()
    editor._library_variable_fields["token"].setText("typed-secret")

    dialog_class = _require("pypost.ui.dialogs.mcp_servers_dialog", "McpServersDialog")
    received = []
    dialog = dialog_class(
        configurations=lambda: [], status_for=lambda _id: None,
        save=lambda _config: None,
        save_library=lambda config, selection, handoff: received.append(
            (config, selection, handoff)
        ),
        remove=lambda _id: None, start=lambda _id: None, stop=lambda _id: None,
        activity=lambda _id: [], collections=lambda: [], environments=lambda: [],
        legacy_environment=lambda: None, legacy_host="127.0.0.1", legacy_port=1080,
        library_service=service,
    )
    dialog._save_configuration(editor, editor.configuration())
    assert len(received) == 1
    assert received[0][2]["overlay"]["secrets"] == {"token": "typed-secret"}
    editor.close()
    dialog.close()


def test_editor_rejects_missing_required_library_variable_inline(qapp):
    selection = {
        **_library_selection(),
        "manifest_variables": [
            {"name": "token", "type": "string", "required": True, "secret": True}
        ],
        "manifest_profiles": {"dev": {}},
        "overlay": {},
    }
    editor = _McpServerEditor(
        collections=[], environments=[Environment(id="dev", name="Development")],
        configuration=None, default_environment=None,
        default_host="127.0.0.1", default_port=1080,
        library_selections=[selection],
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    editor._replace_library_selections([selection])
    editor._library_variable_fields["token"].clear()
    editor._accept_if_complete()
    assert editor.result() == editor.DialogCode.Rejected
    assert "required variable missing" in editor._error.text()
    editor.close()


def test_editor_rejects_mistyped_library_variable_inline(qapp):
    selection = {
        **_library_selection(),
        "manifest_variables": [
            {"name": "retries", "type": "integer", "required": True}
        ],
        "manifest_profiles": {"dev": {"retries": 1}},
        "overlay": {},
    }
    editor = _McpServerEditor(
        collections=[], environments=[Environment(id="dev", name="Development")],
        configuration=None, default_environment=None,
        default_host="127.0.0.1", default_port=1080,
        library_selections=[selection],
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    editor._replace_library_selections([selection])
    editor._library_variable_fields["retries"].setText("not-an-integer")
    editor._accept_if_complete()
    assert editor.result() == editor.DialogCode.Rejected
    assert "Invalid value for library variable" in editor._error.text()
    editor.close()


def test_editor_preserves_unavailable_profile_and_blocks_save_until_reselected(qapp):
    selection = {
        **_library_selection(),
        "manifest_variables": [],
        "manifest_profiles": {"dev": {}},
        "overlay": {"active_profile": "removed-profile"},
    }
    editor = _McpServerEditor(
        collections=[], environments=[Environment(id="dev", name="Development")],
        configuration=None, default_environment=None,
        default_host="127.0.0.1", default_port=1080,
        library_selections=[selection],
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    editor._replace_library_selections([selection])
    assert editor._library_profile.currentData() == "removed-profile"
    editor._accept_if_complete()
    assert editor.result() == editor.DialogCode.Rejected
    assert "unavailable" in editor._error.text()
    editor.close()


def test_service_merges_collection_variables_and_profiles(tmp_path):
    service = _real_library_service(tmp_path)
    root = tmp_path / "library"
    manifest_path = root / "pypost-library.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["presets"]["dev"]["manifest_only"] = "from-manifest"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    write_collection_file(
        Collection(
            id="orders", name="Orders",
            variables=[{"name": "collection_only", "type": "integer", "default": 3}],
            presets={"dev": {"collection_only": 7}},
        ),
        root / "collections/orders.json",
    )
    entry = service.list_manifest_collections("library-1")[0]
    names = {item["name"]: item for item in entry["manifest_variables"]}
    assert names["collection_only"]["default_value"] == 3
    assert entry["manifest_profiles"]["dev"]["collection_only"] == 7
    assert entry["manifest_profiles"]["dev"]["manifest_only"] == "from-manifest"


def test_resolver_accepts_collection_only_profile_and_masks_collection_secrets(tmp_path):
    service = _real_library_service(tmp_path)
    root = tmp_path / "library"
    collection_path = root / "collections/orders.json"
    write_collection_file(
        Collection(
            id="orders",
            name="Orders",
            variables=[
                {"name": "collection_token", "type": "string", "secret": True, "required": True},
            ],
            presets={"collection-only": {
                "token": "collection-profile-token",
                "collection_token": "collection-secret",
            }},
        ),
        collection_path,
    )

    resolver = _require("pypost.core.library_runtime_resolver", "LibraryRuntimeResolver")
    result = resolver(library_service=service).resolve(
        _library_selection(), environment_id="collection-only"
    )

    assert result.environment["collection_token"] == "collection-secret"
    assert "collection_token" in result.hidden_keys
    assert "token" in result.hidden_keys


def test_resolver_resolves_active_collection_only_profile_from_real_library(tmp_path):
    service = _real_library_service(tmp_path)
    root = tmp_path / "library"
    write_collection_file(
        Collection(
            id="orders",
            name="Orders",
            variables=[
                {"name": "collection_token", "type": "string", "required": True},
            ],
            presets={"collection-only": {
                "token": "from-collection-profile",
                "collection_token": "from-collection",
            }},
        ),
        root / "collections/orders.json",
    )
    service.overlay_manager.save_overlay(
        LocalLibraryOverlay(
            library_id="library-1", active_profile="collection-only"
        )
    )

    resolver = _require(
        "pypost.core.library_runtime_resolver", "LibraryRuntimeResolver"
    )
    result = resolver(library_service=service).resolve(
        _library_selection(), environment_id="dev"
    )

    assert result.environment["collection_token"] == "from-collection"
    assert result.environment["token"] == "from-collection-profile"


def test_editor_restores_valid_second_collection_and_rejects_stale_identity(qapp):
    first = {**_library_selection(), "path": "collections/first.json", "index": 0}
    second = {**_library_selection(), "path": "collections/second.json", "index": 1}
    configuration = McpServerConfiguration(
        id="existing", port=1080, environment_id="dev",
        library_id="library-1", manifest_id="library-1",
        library_collection_path=second["path"], library_collection_index=1,
    )
    editor = _McpServerEditor(
        collections=[], environments=[Environment(id="dev", name="Development")],
        configuration=configuration, default_environment=None,
        default_host="127.0.0.1", default_port=1080,
        library_selections=[first],
    )
    editor._collection_source.setCurrentIndex(editor._collection_source.findData("library"))
    editor._replace_library_selections([first, second])
    assert editor.library_selection() == second
    stale = {**second, "path": "collections/gone.json", "index": 9}
    editor._target_collection_identity = editor._selection_identity(stale)
    editor._replace_library_selections([first, second])
    assert editor.library_selection() is None
    assert editor._library_collection_stale is True
    editor._accept_if_complete()
    assert editor.result() == editor.DialogCode.Rejected
    assert "stale" in editor._error.text()
    editor.close()


def test_candidate_overlay_is_validated_before_settings_write(tmp_path):
    service = _real_library_service(tmp_path)
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    controller = controller_class(library_service=service)
    configuration = McpServerConfiguration(
        id="typed-server", port=1085, environment_id="dev",
        library_id="library-1", manifest_id="library-1",
        library_collection_path="collections/orders.json",
    )
    with pytest.raises(ValueError, match="profile_invalid"):
        controller.save_library_server(
            configuration, _library_selection(),
            {"overlay": {"library_id": "library-1", "active_profile": "dev",
                          "overrides": {"host": 42}, "secrets": {}}},
        )
    assert controller.mcp_server_configurations() == []
    assert service.overlay_manager.get_overlay("library-1").overrides == {}


def test_normal_environment_id_resolves_library_runtime(tmp_path):
    service = _real_library_service(tmp_path)
    environment = Environment(
        id="workspace-dev", name="Workspace development", variables={"token": "env-token"}
    )
    runtime = _require(
        "pypost.core.library_runtime_resolver", "LibraryRuntimeResolver"
    )(
        library_service=service, environment_lookup=lambda value: environment if value == environment.id else None
    ).resolve(_library_selection(), environment.id)
    assert runtime.environment["token"] == "env-token"


def test_library_handoff_persists_overlay_and_rollback_uses_snapshot(tmp_path):
    service = _real_library_service(tmp_path)
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    environment = Environment(id="workspace-dev", variables={"token": "env-token"})
    registry = _require("pypost.core.mcp_server_registry", "MCPServerRegistry")(
        library_service=service, environment_lookup=lambda value: environment if value == environment.id else None
    )
    controller = controller_class(
        registry=registry,
        library_service=service,
        environment_lookup=lambda value: environment if value == environment.id else None,
    )
    selection = _library_selection()
    configuration = McpServerConfiguration(
        id="overlay-server", port=1083, environment_id=environment.id,
        library_id="library-1", manifest_id="library-1",
        library_collection_path="collections/orders.json",
    )
    handoff = LocalLibraryOverlay(
        library_id="library-1", active_profile="dev",
        overrides={"host": "override.example"}, secrets={"token": "secret-token"}
    )
    controller.save_library_server(configuration, selection, handoff)
    saved = service.overlay_manager.get_overlay("library-1")
    assert saved.active_profile == "dev"
    assert saved.overrides == {"host": "override.example"}
    assert saved.secrets == {"token": "secret-token"}


def test_library_transaction_rolls_back_persisted_overlay_model(tmp_path):
    class OverlaySpy:
        def __init__(self):
            self.saved = []

        def save_overlay(self, overlay):
            self.saved.append(overlay)

    transaction_class = _require(
        "pypost.ui.mcp_server_controller", "LibraryMcpSaveTransaction"
    )
    store = _require("pypost.ui.mcp_server_controller", "CheckedSettingsStore")(
        root=tmp_path
    )
    spy = OverlaySpy()
    previous_overlay = LocalLibraryOverlay(
        library_id="library-1", active_profile="dev", overrides={"host": "old"}
    )
    transaction = transaction_class(
        store=store,
        previous={"server": {"id": "server-1"}},
        candidate={"server": {"id": "server-1"}},
        overlay={"library_id": "library-1", "overrides": {"host": "new"}},
        overlay_manager=spy,
        overlay_snapshot=previous_overlay,
    )
    assert transaction.commit().committed is True
    assert transaction.rollback().restored is True
    assert isinstance(spy.saved[-1], LocalLibraryOverlay)
    assert spy.saved[-1].overrides == {"host": "old"}


def test_config_settings_and_overlay_restore_after_overlay_write_failure(tmp_path):
    class FailingOverlayManager(LocalOverlayManager):
        def __init__(self, base_dir):
            super().__init__(base_dir)
            self.fail_after_write = False

        def save_overlay(self, overlay):
            result = super().save_overlay(overlay)
            if self.fail_after_write:
                self.fail_after_write = False
                raise OSError("simulated overlay journal failure")
            return result

    overlay_manager = FailingOverlayManager(tmp_path / "overlays")
    previous_overlay = LocalLibraryOverlay(
        library_id="library-1", active_profile="dev", overrides={"host": "old"},
        secrets={"token": "old-secret"},
    )
    overlay_manager.save_overlay(previous_overlay)
    service = _real_library_service(tmp_path)
    service.overlay_manager = overlay_manager
    manager = ConfigManager(config_dir=tmp_path / "settings")
    controller_class = _require(
        "pypost.ui.mcp_server_controller", "McpServerSettingsController"
    )
    controller = controller_class(config_manager=manager, library_service=service)
    selection = _library_selection()
    configuration = McpServerConfiguration(
        id="atomic-server", port=1084, environment_id="dev",
        library_id="library-1", manifest_id="library-1",
        library_collection_path="collections/orders.json",
    )
    overlay_manager.fail_after_write = True
    with pytest.raises(ValueError, match="persistence_failure"):
        controller.save_library_server(
            configuration,
            selection,
            LocalLibraryOverlay(
                library_id="library-1", active_profile="dev",
                overrides={"host": "new"}, secrets={"token": "new-secret"},
            ),
        )
    assert controller.mcp_server_configurations() == []
    assert manager.load_config_strict().mcp_servers == []
    assert overlay_manager.get_overlay("library-1").model_dump(mode="json") == (
        previous_overlay.model_dump(mode="json")
    )


def test_durable_journal_recovers_settings_and_overlay_on_store_initialization(tmp_path):
    settings_manager = ConfigManager(config_dir=tmp_path / "settings")
    overlay_manager = LocalOverlayManager(tmp_path / "overlays")
    old_configuration = McpServerConfiguration(
        id="old", port=1088, environment_id="dev", collection_id="workspace"
    )
    old_settings = AppSettings(mcp_servers=[old_configuration])
    settings_manager.save_config(old_settings)
    old_overlay = LocalLibraryOverlay(
        library_id="library-1", active_profile="dev", overrides={"host": "old"},
        secrets={"token": "old-secret"},
    )
    overlay_manager.save_overlay(old_overlay)
    store = ConfigManagerSettingsStore(settings_manager, overlay_manager)
    journal = store._stage_journal(
        LocalLibraryOverlay(library_id="library-1", active_profile="dev").model_dump(
            mode="json"
        )
    )
    settings_manager.save_config(AppSettings())
    overlay_manager.save_overlay(
        LocalLibraryOverlay(
            library_id="library-1", active_profile="other", secrets={"token": "new"}
        )
    )
    assert Path(journal["backup_dir"]).is_dir()

    recovered = ConfigManagerSettingsStore(settings_manager, overlay_manager)
    assert recovered is not None
    assert settings_manager.load_config_strict().mcp_servers == [old_configuration]
    assert overlay_manager.get_overlay("library-1").model_dump(mode="json") == (
        old_overlay.model_dump(mode="json")
    )
    assert not store._journal_path.exists()
