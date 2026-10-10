"""PYPOST-1354: durable, sanitized copies of Built-in paired environments."""
from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from cryptography.fernet import Fernet
from PySide6.QtWidgets import QPushButton

from pypost.core.builtin_collections import BuiltinCollectionView
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.core.storage import StorageManager
from pypost.models.models import Collection, Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.mcp_servers_dialog import _McpServerEditor
from pypost.ui.presenters.env_presenter import EnvPresenter
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)
COLLECTION = "collections/test.json"
PAIRED = "environments/test.json"


@pytest.fixture
def builtin(tmp_path):
    """Validate a tiny real bundled library rather than mock template derivation."""
    root = tmp_path / "bundle"
    (root / "collections").mkdir(parents=True)
    (root / "environments").mkdir()
    (root / "collections/test.json").write_text(
        Collection(id="test", name="Test", requests=[]).model_dump_json(), encoding="utf-8"
    )
    (root / "pypost-library.yaml").write_text(
        'schema_version: "1.0.0"\nid: pypost-examples\nname: Test\n'
        'version: "1.0.0"\ncollections: [collections/test.json]\n', encoding="utf-8"
    )
    (root / "builtin-collections.yaml").write_text(
        'entries:\n  - collection: collections/test.json\n'
        '    environment: environments/test.json\n    name: Test MCP\n', encoding="utf-8"
    )
    template = Environment(
        name="Paired", variables={"URL": "https://example.invalid", "TOKEN": "PLACEHOLDER"},
        hidden_keys={"TOKEN"}, mcp_overridable_keys={"URL"}, enable_mcp=True,
    )
    path = root / PAIRED
    path.write_text(json.dumps([template.model_dump(mode="json")]), encoding="utf-8")
    view = BuiltinCollectionView(PredefinedLibraryService(root=root))
    assert len(view.list_entries()) == 1
    assert view.load_paired_environment(COLLECTION).variables == template.variables
    return view, path


@pytest.fixture
def storage(tmp_path, monkeypatch):
    monkeypatch.setattr("pypost.core.storage.user_data_dir", lambda *args: str(tmp_path / "data"))
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager()


@pytest.fixture
def presenter(qapp, storage):
    owner = EnvPresenter(storage, MagicMock(), MagicMock(), AppSettings(), lambda: [], MagicMock())
    original = Environment(id="original", name="Existing", variables={"URL": "old"})
    owner._apply_loaded_environments([original])
    owner._env_selector.setCurrentIndex(1)
    storage.save_environments([original])
    yield owner
    assert owner.wait_storage_idle(timeout_ms=5000)
    owner.teardown(timeout_ms=5000)


def derive(view, existing=()):
    method = getattr(view, "derive_paired_environment", None)
    assert callable(method), "BuiltinCollectionView must expose sanitized paired derivation"
    return method(COLLECTION, existing)


def create(owner, candidate, completion):
    method = getattr(owner, "create_workspace_environment", None)
    assert callable(method), "EnvPresenter must own durable workspace environment creation"
    return method(candidate, completion)


def editor(view, environments, callback=None):
    kwargs = dict(
        collections=[Collection(id="ws", name="Workspace")], environments=environments,
        configuration=None, default_environment=None, default_host="127.0.0.1",
        default_port=1080, builtin_view=view,
    )
    if callback is not None:
        kwargs.update(create_environment=callback, get_environments=lambda: environments)
    result = _McpServerEditor(**kwargs)
    result._collection_source.setCurrentIndex(result._collection_source.findData("builtin"))
    result.show()
    return result


def copy_button(widget):
    buttons = [button for button in widget.findChildren(QPushButton)
               if button.text() == "Create editable copy of paired environment"]
    assert len(buttons) == 1, "Built-in editor must provide the dedicated copy action"
    return buttons[0]


def test_derivation_sanitizes_preserves_and_never_mutates_template(builtin, caplog):
    view, path = builtin
    before = path.read_bytes()
    template = view.load_paired_environment(COLLECTION)
    with caplog.at_level(logging.DEBUG, logger="pypost.core.builtin_collections"):
        first = derive(view)
    messages = [record.getMessage() for record in caplog.records
                if record.name == "pypost.core.builtin_collections"]
    assert any(f"builtin_paired_environment_derived env_id={first.id}" in msg for msg in messages)
    assert all("PLACEHOLDER" not in msg and "example.invalid" not in msg for msg in messages)
    second = derive(view, [first, Environment(name="Paired (2)")])
    assert first.variables == {"URL": "https://example.invalid", "TOKEN": ""}
    assert first.hidden_keys == template.hidden_keys
    assert first.mcp_overridable_keys == template.mcp_overridable_keys
    assert first.enable_mcp is template.enable_mcp
    assert first.builtin_environment_path == PAIRED
    assert first.name == "Paired" and second.name == "Paired (3)"
    assert UUID(first.id) != UUID(second.id)
    assert first.id != template.id
    first.variables["URL"] = "changed"
    first.hidden_keys.clear()
    first.mcp_overridable_keys.clear()
    assert second.variables["URL"] == template.variables["URL"]
    assert second.hidden_keys == {"TOKEN"}
    assert template.variables["TOKEN"] == "PLACEHOLDER"
    assert path.read_bytes() == before


def test_origin_roundtrips_after_rename_and_legacy_records_remain_unmarked(storage):
    env = Environment(name="Renamed", builtin_environment_path=PAIRED)
    storage.save_environments([env, Environment(name="Legacy")])
    loaded = storage.load_environments()
    assert getattr(loaded[0], "builtin_environment_path", None) == PAIRED
    assert loaded[1].builtin_environment_path is None


@pytest.mark.usefixtures("qapp")
def test_missing_owner_disables_copy_and_keeps_manual_selection(builtin):
    view, _ = builtin
    envs = [Environment(id="manual", name="Manual")]
    widget = editor(view, envs)
    button = copy_button(widget)
    assert button.isVisible() and not button.isEnabled()
    handler = getattr(widget, "_create_paired_environment", None)
    assert callable(handler), "Copy handler must also guard missing persistence capability"
    handler()
    assert envs == [envs[0]] and widget._environment.count() == 1
    widget._environment.setCurrentIndex(-1)
    widget._accept_if_complete()
    assert widget.result() == 0 and "required" in widget._error.text().lower()
    widget._environment.setCurrentIndex(widget._environment.findData("manual"))
    widget._accept_if_complete()
    assert widget.configuration().environment_id == "manual"
    widget.close()


@pytest.mark.usefixtures("qapp")
@pytest.mark.parametrize("origin,highlight", [(None, True), ("environments/other.json", True),
                                             (PAIRED, False)])
def test_highlight_uses_exact_persisted_origin_not_names(builtin, storage, origin, highlight):
    view, _ = builtin
    env = Environment(name="Paired (2)", builtin_environment_path=origin)
    storage.save_environments([env])
    widget = editor(view, storage.load_environments(), lambda candidate, done: False)
    button = copy_button(widget)
    assert button.isDefault() is highlight
    widget._collection_source.setCurrentIndex(widget._collection_source.findData("workspace"))
    assert not button.isVisible()
    widget._collection_source.setCurrentIndex(widget._collection_source.findData("builtin"))
    widget._server_type.setCurrentIndex(widget._server_type.findData("proxy"))
    assert not button.isVisible()
    widget.close()


@pytest.mark.usefixtures("qapp")
def test_editor_waits_for_ack_then_refreshes_and_selects(builtin):
    view, _ = builtin
    envs = [Environment(id="old", name="Existing")]
    completions = []

    def admit(candidate, done):
        completions.append((candidate, done))
        return True

    widget = editor(view, envs, admit)
    widget._environment.setCurrentIndex(widget._environment.findData("old"))
    button = copy_button(widget)
    button.click()
    assert len(completions) == 1 and not button.isEnabled()
    assert widget._environment.currentData() == "old" and len(envs) == 1
    candidate, done = completions[0]
    assert widget._environment.findData(candidate.id) == -1
    envs.append(candidate)
    done(candidate, None)
    assert widget._environment.currentData() == candidate.id and button.isEnabled()
    assert not button.isDefault()
    another = editor(view, envs, admit)
    assert another._environment.findData(candidate.id) >= 0
    another.close()
    widget.close()


@pytest.mark.usefixtures("qapp")
@pytest.mark.parametrize("failure", ["reject", "exception", "failed", "incomplete"])
def test_editor_failures_leave_no_ghost_and_retry_is_possible(builtin, failure):
    view, _ = builtin
    envs = [Environment(id="old", name="Existing")]
    attempts = []

    def admit(candidate, done):
        attempts.append(candidate)
        if len(attempts) > 1:
            envs.append(candidate)
            done(candidate, None)
            return True
        if failure == "reject":
            return False
        if failure == "exception":
            raise OSError("Creation unavailable")
        done(None, failure)
        return True

    widget = editor(view, envs, admit)
    widget._environment.setCurrentIndex(widget._environment.findData("old"))
    button = copy_button(widget)
    button.click()
    assert len(envs) == 1 and widget._environment.currentData() == "old"
    assert widget._environment.findData(attempts[0].id) == -1
    assert button.isEnabled() and widget._error.text()
    button.click()
    assert len(envs) == 2 and widget._environment.currentData() == attempts[1].id
    widget.close()


@pytest.mark.usefixtures("qapp")
@pytest.mark.parametrize("change", ["source", "close"])
def test_pending_completion_respects_source_change_or_closed_editor(builtin, change):
    view, _ = builtin
    envs = [Environment(id="old", name="Existing")]
    pending = []
    widget = editor(view, envs, lambda candidate, done: pending.append((candidate, done)) or True)
    widget._environment.setCurrentIndex(widget._environment.findData("old"))
    copy_button(widget).click()
    if change == "source":
        widget._collection_source.setCurrentIndex(widget._collection_source.findData("workspace"))
    else:
        widget.reject()
    candidate, done = pending[0]
    envs.append(candidate)
    done(candidate, None)
    assert widget._environment.currentData() == "old"
    widget.close()


def test_presenter_persists_canonical_list_preserves_selection_and_wires_owner(presenter, storage):
    candidate = Environment(name="Existing", id="original", builtin_environment_path=PAIRED)
    outcomes = []
    assert create(presenter, candidate, lambda env, error: outcomes.append((env, error)))
    assert len(outcomes) == 1 and outcomes[0][1] is None
    published = outcomes[0][0]
    assert published.id != "original" and published.name == "Existing (2)"
    assert presenter.environment_by_id(published.id) is published
    assert presenter._selected_environment().id == "original"
    assert {env.id for env in storage.load_environments()} == {"original", published.id}
    controller = MagicMock()
    presenter.mcp_controls.set_server_controller(controller)
    with patch("pypost.ui.presenters.mcp_controls_presenter.McpServersDialog") as dialog:
        presenter.mcp_controls._open_mcp_servers()
        callback = dialog.call_args.kwargs["create_environment"]
        assert callback == presenter.create_workspace_environment
    with patch("pypost.ui.presenters.env_presenter.EnvironmentDialog") as dialog:
        dialog.return_value.environments = presenter._environments
        presenter._open_env_manager()
        assert any(env.id == published.id for env in dialog.call_args.args[0])


def test_presenter_rejects_teardown_without_writes_or_completion(presenter, storage, caplog):
    before = storage.environments_file.read_bytes()
    presenter.begin_root_teardown()
    outcomes = []
    with caplog.at_level(logging.INFO, logger="pypost.ui.presenters.env_presenter_creation"):
        assert not create(presenter, Environment(name="Copy"), lambda *args: outcomes.append(args))
    assert "workspace_environment_creation_rejected reason=teardown" in caplog.text
    assert "workspace_environment_creation_admitted" not in caplog.text
    assert outcomes == [] and len(presenter._environments) == 1
    assert storage.environments_file.read_bytes() == before


def test_sync_storage_failure_discards_staging_and_allows_retry(
    presenter, storage, monkeypatch, caplog
):
    method = getattr(presenter, "create_workspace_environment", None)
    assert callable(method), "Presenter must own creation failure cleanup"
    candidate = Environment(name="PRIVATE_NAME", variables={"TOKEN": "PRIVATE_VALUE"})
    outcomes = []
    original_save = storage.save_environments

    def fail_save(environments, **kwargs):
        raise OSError("PRIVATE_EXCEPTION_CREDENTIAL")

    monkeypatch.setattr(storage, "save_environments", fail_save)
    with caplog.at_level(logging.INFO, logger="pypost.ui.presenters.env_presenter_creation"):
        with patch("pypost.ui.presenters.env_presenter.show_env_save_failed"):
            admitted = method(candidate, lambda env, error: outcomes.append((env, error)))
    messages = [record.getMessage() for record in caplog.records
                if record.name == "pypost.ui.presenters.env_presenter_creation"]
    assert sum("workspace_environment_creation_admitted" in msg for msg in messages) == 1
    assert sum("workspace_environment_creation_failed" in msg for msg in messages) == 1
    assert any("reason=failed" in msg for msg in messages)
    assert not any("workspace_environment_creation_succeeded" in msg for msg in messages)
    assert all("PRIVATE_" not in msg for msg in messages)
    assert presenter.environment_by_id(candidate.id) is None
    assert [env.id for env in storage.load_environments()] == ["original"]
    assert len(outcomes) == (1 if admitted else 0)
    assert all(env is None and error for env, error in outcomes)
    monkeypatch.setattr(storage, "save_environments", original_save)
    retried = []
    with caplog.at_level(logging.INFO, logger="pypost.ui.presenters.env_presenter_creation"):
        assert method(candidate, lambda env, error: retried.append((env, error)))
    assert f"workspace_environment_creation_succeeded env_id={candidate.id}" in caplog.text
    creation_records = [record for record in caplog.records
                        if record.name == "pypost.ui.presenters.env_presenter_creation"]
    assert all("PRIVATE_" not in record.getMessage() for record in creation_records)
    assert retried == [(presenter.environment_by_id(candidate.id), None)]


@pytest.mark.parametrize("failure", [False, True])
def test_encrypted_ack_preserves_staged_copy_and_unrelated_updates(
    presenter, storage, monkeypatch, failure
):
    """Use the real gateway; hold first worker while a newer canonical save is queued."""
    method = getattr(presenter, "create_workspace_environment", None)
    assert callable(method), "Presenter must expose persistence-correlated creation"
    presenter._settings.env_encryption_enabled = True
    monkeypatch.setenv("PYPOST_ENV_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
    storage.apply_encryption_settings(presenter._settings)
    original_save = storage.save_environments
    started, release = threading.Event(), threading.Event()
    snapshots = []
    outcomes = []
    candidate = Environment(name="Copy", builtin_environment_path=PAIRED)

    def gated_save(environments, **kwargs):
        snapshots.append([env.model_copy(deep=True) for env in environments])
        if len(snapshots) == 1:
            started.set()
            if not release.wait(timeout=5):
                raise TimeoutError("test save gate timed out")
            if failure:
                raise OSError("controlled copy save failure")
        return original_save(environments, **kwargs)

    monkeypatch.setattr(storage, "save_environments", gated_save)
    with patch("pypost.ui.presenters.env_presenter.show_env_save_failed") as message:
        try:
            assert method(candidate, lambda env, error: outcomes.append((env, error)))
            process_until(started.is_set, timeout_ms=3000)
            assert presenter.environment_by_id(candidate.id) is None and outcomes == []
            presenter._storage_gateway.save_outcome.emit(99999, "persisted")
            presenter._storage_gateway.save_outcome.emit(99999, "coalesced_into_newer_save")
            assert outcomes == []
            presenter._environments[0].variables["URL"] = "newer"
            assert presenter._save_environments()
            assert not method(Environment(name="Busy"), lambda *args: pytest.fail("busy callback"))
        finally:
            release.set()
            assert presenter.wait_storage_idle(timeout_ms=5000)
        process_until(lambda: len(outcomes) == 1, timeout_ms=3000)
        reloaded = storage.load_environments()
        assert reloaded[0].variables["URL"] == "newer"
        assert len(snapshots) >= 2
        assert snapshots[0][-1].id == candidate.id
        assert presenter._selected_environment().id == "original"
        if failure:
            assert outcomes[0][0] is None and outcomes[0][1]
            assert presenter.environment_by_id(candidate.id) is None
            assert all(env.id != candidate.id for env in snapshots[-1])
            assert [env.id for env in reloaded] == ["original"]
            assert message.call_count == 1
        else:
            assert outcomes == [(presenter.environment_by_id(candidate.id), None)]
            assert sum(env.id == candidate.id for env in presenter._environments) == 1
            assert all(any(env.id == candidate.id for env in snap) for snap in snapshots)
            assert {env.id for env in reloaded} == {"original", candidate.id}
        retried = []
        assert method(Environment(name="Retry"), lambda env, error: retried.append((env, error)))
        assert presenter.wait_storage_idle(timeout_ms=5000)
        assert len(retried) == 1 and retried[0][1] is None
