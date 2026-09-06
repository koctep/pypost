"""Failing repro tests for the PYPOST-1278 Library Manager enhancement.

The tests use deterministic records and fake Git boundaries.  They describe the
new presenter/widget seams without importing proposed production modules that do
not exist before Step 4.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Optional
from unittest.mock import MagicMock

import pytest
from prometheus_client import generate_latest

from pypost.core.git_service import GitLibraryService
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.metrics_registry import MetricsRegistry
from pypost.models.git_library import GitOperationResult, GitOperationType
from pypost.models.library_manifest import ManifestDiagnosticError
from pypost.models.library_manager import LibraryConnectionRecord, LibrarySourceType
from pypost.ui.presenters.library_presenter import LibraryPresenter
from pypost.ui.widgets.library_manager_panel import LibraryListWidget
from tests.helpers.qt_wait import wait_until

pytestmark = pytest.mark.timeout(30)


@dataclass(frozen=True)
class _FakeLibraryEntry:
    """Small row record used to keep the repro independent of production models."""

    stable_id: str
    display_name: Optional[str]
    source_type: str
    local_path: Path
    sync_status: str
    conditions: tuple[str, ...] = ()
    is_clean: bool = True
    last_modified: Optional[datetime] = None


def _require_callable(target: object, name: str) -> Callable[..., Any]:
    """Fail clearly when the Step 4 seam is absent, rather than as a harness error."""
    method = getattr(target, name, None)
    assert callable(method), f"Missing PYPOST-1278 behavior: callable {name}"
    return method


def _entries(tmp_path: Path) -> list[_FakeLibraryEntry]:
    """Return fixed rows covering both library source types and status values."""
    return [
        _FakeLibraryEntry(
            stable_id="team-payments",
            display_name="Payments Team",
            source_type="Cloned managed copy",
            local_path=tmp_path / "team-payments",
            sync_status="Current",
            last_modified=datetime(2026, 1, 3, tzinfo=timezone.utc),
        ),
        _FakeLibraryEntry(
            stable_id="local-archive",
            display_name=None,
            source_type="Registered local directory",
            local_path=tmp_path / "archive",
            sync_status="Unknown",
            conditions=("Offline", "Stale"),
            is_clean=False,
            last_modified=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
    ]


def test_manageable_rows_keep_identity_fallback_and_status_badges(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Rows expose one stable entry each, including fallback identity and badges."""
    widget = LibraryListWidget()
    entries = _entries(tmp_path)

    _require_callable(widget, "set_entries")(entries)
    visible_ids = _require_callable(widget, "visible_library_ids")()
    assert visible_ids == ["team-payments", "local-archive"]

    missing_name_row = _require_callable(widget, "row_for_library")("local-archive")
    assert missing_name_row["display_name"] == "local-archive"
    assert missing_name_row["source_type"] == "Registered local directory"
    assert set(missing_name_row["badges"]) >= {"Unknown", "Offline", "Stale"}


def test_search_and_exact_status_filter_update_visible_rows(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Search matches identity case-insensitively and status filters match exact labels."""
    widget = LibraryListWidget()
    _require_callable(widget, "set_entries")(_entries(tmp_path))

    _require_callable(widget, "set_search_query")("PAYMENTS")
    assert _require_callable(widget, "visible_library_ids")() == ["team-payments"]

    _require_callable(widget, "set_search_query")("LOCAL-ARCHIVE")
    _require_callable(widget, "set_status_filter")(None)
    assert _require_callable(widget, "visible_library_ids")() == ["local-archive"]

    _require_callable(widget, "set_search_query")("")
    _require_callable(widget, "set_status_filter")("Offline")
    assert _require_callable(widget, "visible_library_ids")() == ["local-archive"]

    _require_callable(widget, "set_status_filter")(None)
    assert _require_callable(widget, "visible_library_ids")() == [
        "team-payments",
        "local-archive",
    ]


def test_sorting_and_selection_use_deterministic_stable_id_rules(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Primary sort direction changes only its key and selection follows stable IDs."""
    entries = [
        _FakeLibraryEntry(
            stable_id="same-z",
            display_name="Same",
            source_type="Cloned managed copy",
            local_path=tmp_path / "same-z",
            sync_status="Current",
            last_modified=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
        _FakeLibraryEntry(
            stable_id="same-a",
            display_name="same",
            source_type="Cloned managed copy",
            local_path=tmp_path / "same-a",
            sync_status="Current",
            last_modified=datetime(2026, 1, 2, tzinfo=timezone.utc),
        ),
        _FakeLibraryEntry(
            stable_id="older",
            display_name="Older",
            source_type="Registered local directory",
            local_path=tmp_path / "older",
            sync_status="Checking",
            last_modified=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
        _FakeLibraryEntry(
            stable_id="missing",
            display_name=None,
            source_type="Registered local directory",
            local_path=tmp_path / "missing",
            sync_status="Unknown",
        ),
        _FakeLibraryEntry(
            stable_id="newer",
            display_name="Newer",
            source_type="Cloned managed copy",
            local_path=tmp_path / "newer",
            sync_status="Current",
            last_modified=datetime(2026, 1, 3, tzinfo=timezone.utc),
        ),
    ]
    widget = LibraryListWidget()
    _require_callable(widget, "set_entries")(entries)
    set_sort = _require_callable(widget, "set_sort")
    visible_ids = _require_callable(widget, "visible_library_ids")

    set_sort("status", descending=False)
    assert visible_ids() == ["older", "missing", "newer", "same-a", "same-z"]

    set_sort("status", descending=True)
    assert visible_ids() == ["newer", "same-a", "same-z", "missing", "older"]

    set_sort("last_modified", descending=True)
    assert visible_ids() == ["newer", "same-a", "same-z", "older", "missing"]

    _require_callable(widget, "select_library")("same-z")
    assert widget.selected_library_id == "same-z"
    _require_callable(widget, "set_search_query")("newer")
    assert widget.selected_library_id is None
    assert "select" in widget.selection_guidance.lower()


def test_offline_refresh_retains_last_known_data_and_marks_stale(
    qapp: object,
    tmp_path: Path,
) -> None:
    """A failed refresh is Unknown/Offline/Stale and does not clear the row."""
    library_path = tmp_path / "offline-library"
    checked_at = datetime(2026, 1, 4, 12, 0, tzinfo=timezone.utc)
    modified_at = datetime(2026, 1, 3, 12, 0, tzinfo=timezone.utc)
    known_status = SimpleNamespace(
        library_id="offline-library",
        display_name="Offline Library",
        repo_path=library_path,
        local_path=library_path,
        last_modified=modified_at,
        last_successful_check=checked_at,
        current_branch="main",
        is_clean=False,
        dirty_files=["collections/request.json"],
    )
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    service.get_library_dir.return_value = library_path
    service.status.return_value = known_status
    presenter = LibraryPresenter(service=service, clock=lambda: checked_at)
    presenter.select_library("offline-library")

    service.status.side_effect = OSError("network unavailable")
    stale_status = presenter.refresh_status("offline-library")

    assert stale_status is not None
    assert stale_status.display_name == "Offline Library"
    assert stale_status.local_path == library_path
    assert stale_status.last_modified == modified_at
    assert stale_status.last_successful_check == checked_at
    assert stale_status.is_stale is True
    assert stale_status.sync_status == "Unknown"
    condition_labels = {
        getattr(condition, "value", condition) for condition in stale_status.conditions
    }
    assert condition_labels >= {"Offline", "Stale"}
    assert stale_status.sync_status != "Current"


def test_clone_validation_failure_removes_unregistered_clone(
    qapp: object,
    tmp_path: Path,
) -> None:
    """A clone that fails manifest validation is cleaned up before it is registered."""
    clone_path = tmp_path / "invalid-clone"
    clone_path.mkdir()
    service = MagicMock(spec=GitLibraryService)
    service.clone.return_value = GitOperationResult(
        operation=GitOperationType.CLONE,
        success=True,
        library_id="invalid-clone",
    )
    service.base_dir = tmp_path
    service.get_library_dir.return_value = clone_path
    service.delete_library_at.return_value = True
    store = LibraryConnectionStore(path=tmp_path / "connections.json")
    manager = LibraryManagerService(git_service=service, connection_store=store)

    with pytest.raises(ManifestDiagnosticError):
        manager.clone("https://example.invalid/library.git", "invalid-clone")

    service.delete_library_at.assert_called_once_with(clone_path, "invalid-clone")
    assert store.load() == []


def test_managed_library_paths_reject_traversal_and_nested_ids(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Managed clone paths accept only one ID component below the configured root."""
    service = GitLibraryService(base_dir=tmp_path)
    for library_id in ("../outside", "nested/library", r"nested\library", ".", "..", ""):
        with pytest.raises(ValueError):
            service.get_library_dir(library_id)


def test_clone_registration_failure_removes_valid_unregistered_clone(
    qapp: object,
    tmp_path: Path,
) -> None:
    """A registry collision also cleans up the newly cloned directory."""
    managed_root = tmp_path / "managed"
    clone_path = managed_root / "duplicate-clone"
    (clone_path / "collections").mkdir(parents=True)
    (clone_path / "pypost-library.yaml").write_text(
        "id: duplicate-clone\n"
        "name: Duplicate Clone\n"
        "collections:\n"
        "  - collections/request.json\n",
        encoding="utf-8",
    )
    (clone_path / "collections" / "request.json").write_text("{}\n", encoding="utf-8")
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = managed_root
    service.clone.return_value = GitOperationResult(
        operation=GitOperationType.CLONE,
        success=True,
        library_id="duplicate-clone",
    )
    service.get_library_dir.return_value = clone_path
    service.delete_library_at.return_value = True
    store = LibraryConnectionStore(path=tmp_path / "connections.json")
    store.add(
        LibraryConnectionRecord(
            stable_id="duplicate-clone",
            manifest_id="duplicate-clone",
            local_path=tmp_path / "existing",
            source_type=LibrarySourceType.CLONED,
        )
    )
    manager = LibraryManagerService(git_service=service, connection_store=store)

    with pytest.raises(ValueError, match="already connected"):
        manager.clone("https://example.invalid/library.git", "duplicate-clone")

    service.delete_library_at.assert_called_once_with(clone_path, "duplicate-clone")


def test_pull_and_branch_switch_stop_before_git_when_local_changes_exist(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Dirty safeguards expose affected files and make no mutating Git call."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    service.check_dirty.return_value = (
        True,
        ["collections/request.json", "collections/response.json"],
    )
    service.pull.return_value = GitOperationResult(
        operation=GitOperationType.PULL,
        success=True,
    )
    service.checkout.return_value = GitOperationResult(
        operation=GitOperationType.CHECKOUT,
        success=True,
    )
    presenter = LibraryPresenter(service=service)

    guard = _require_callable(presenter, "guard_operation")
    pull_guard = guard("library-id", "pull")
    checkout_guard = guard("library-id", "switch_branch")
    assert pull_guard.is_blocked is True
    assert checkout_guard.is_blocked is True
    assert pull_guard.files == ["collections/request.json", "collections/response.json"]
    assert checkout_guard.files == pull_guard.files

    assert service.pull.call_count == 0
    assert service.checkout.call_count == 0


def test_operation_admission_rejects_duplicate_work_for_one_connection(
    qapp: object,
) -> None:
    """The same operation is admitted once while another library remains usable."""
    presenter = LibraryPresenter(service=MagicMock(spec=GitLibraryService))
    request_operation = _require_callable(presenter, "request_operation")
    finish_operation = _require_callable(presenter, "finish_operation")

    assert request_operation("library-a", "refresh") is True
    assert request_operation("library-a", "refresh") is False
    assert request_operation("library-a", "pull") is True
    assert request_operation("library-b", "refresh") is True

    finish_operation("library-a", "refresh")
    assert request_operation("library-a", "refresh") is True


def test_library_operation_observability_tracks_outcomes_without_sensitive_labels(
    qapp: object,
    caplog: pytest.LogCaptureFixture,
    tmp_path: Path,
) -> None:
    """Async library operations emit useful logs and bounded Prometheus labels."""
    metrics = MetricsRegistry()
    presenter = LibraryPresenter(
        service=MagicMock(spec=GitLibraryService),
        metrics=metrics,
    )
    with caplog.at_level(logging.INFO, logger="pypost.ui.presenters.library_presenter"):
        assert presenter.run_operation_async(
            "library-a",
            "check_dirty",
            lambda: (False, []),
        ) is True
        wait_until(
            lambda: ("library-a", "check_dirty") not in presenter._active_operations,
            timeout=5.0,
            message="library operation did not settle",
            condition_name="library_operation_settled",
        )

    output = generate_latest(metrics.registry).decode("utf-8")
    assert 'operation="check_dirty",outcome="started"' in output
    assert 'operation="check_dirty",outcome="success"' in output
    assert "library_operation_started library_id=library-a operation=check_dirty" in caplog.text
    assert "library_operation_completed library_id=library-a operation=check_dirty" in caplog.text

    library_path = tmp_path / "private" / "library"
    (library_path / "collections").mkdir(parents=True)
    (library_path / "pypost-library.yaml").write_text(
        "id: private-library\n"
        "name: Private Library\n"
        "collections:\n"
        "  - collections/request.json\n",
        encoding="utf-8",
    )
    (library_path / "collections" / "request.json").write_text("{}\n", encoding="utf-8")
    sensitive_path = str(library_path)
    with caplog.at_level(logging.INFO, logger="pypost.ui.presenters.library_presenter"):
        assert presenter.connect_local_library_async(library_path) is True
        wait_until(
            lambda: not presenter._active_operations,
            timeout=5.0,
            message="local connect operation did not settle",
            condition_name="local_connect_settled",
        )
    presenter_logs = [
        record.getMessage()
        for record in caplog.records
        if record.name == "pypost.ui.presenters.library_presenter"
    ]
    assert sensitive_path not in "\n".join(presenter_logs)
    assert any("library_operation_started library_id=opaque-" in message for message in presenter_logs)

    assert presenter.delete_library_async("registered-id", confirmed=True) is False
    output = generate_latest(metrics.registry).decode("utf-8")
    assert 'operation="delete",outcome="rejected"' in output
    assert "library_operation_rejected library_id=registered-id operation=delete" in caplog.text

    metrics.track_gui_library_operation("https://user:secret@example.invalid", "secret")
    output = generate_latest(metrics.registry).decode("utf-8")
    assert 'operation="unknown",outcome="unknown"' in output


def test_connect_local_library_validates_in_place_without_writing_selected_directory(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Connecting a valid local manifest registers its path without file mutation."""
    library_path = tmp_path / "existing-library"
    collections_path = library_path / "collections"
    collections_path.mkdir(parents=True)
    (library_path / "pypost-library.yaml").write_text(
        "id: existing-library\n"
        "name: Existing Library\n"
        "collections:\n"
        "  - collections/request.json\n",
        encoding="utf-8",
    )
    (collections_path / "request.json").write_text("{}\n", encoding="utf-8")
    before = {
        path.relative_to(library_path): path.read_bytes()
        for path in library_path.rglob("*")
        if path.is_file()
    }

    service = MagicMock(spec=GitLibraryService)
    presenter = LibraryPresenter(service=service)
    result = _require_callable(presenter, "connect_local_library")(library_path)

    assert result.local_path == library_path
    assert result.source_type == "Registered local directory"
    after = {
        path.relative_to(library_path): path.read_bytes()
        for path in library_path.rglob("*")
        if path.is_file()
    }
    assert after == before
    service.clone.assert_not_called()


def test_disconnect_preserves_data_and_delete_is_clone_only(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Disconnect removes metadata only, while confirmed deletion is clone-only."""
    registered_path = tmp_path / "registered-library"
    registered_path.mkdir()
    registered_file = registered_path / "keep-me.json"
    registered_file.write_text("{}\n", encoding="utf-8")
    cloned_path = tmp_path / "cloned-library"
    cloned_path.mkdir()

    service = MagicMock()
    service.disconnect_library.return_value = True
    service.delete_library.return_value = True
    overlay_manager = MagicMock()
    presenter = LibraryPresenter(service=service, overlay_manager=overlay_manager)

    disconnect = _require_callable(presenter, "disconnect_library")
    assert disconnect("registered-id") is True
    assert registered_file.read_text(encoding="utf-8") == "{}\n"
    service.disconnect_library.assert_called_once_with("registered-id")

    delete = _require_callable(presenter, "delete_library")
    assert delete(
        "registered-id",
        source_type="Registered local directory",
        confirmed=True,
    ) is False
    service.delete_library.assert_not_called()

    assert delete(
        "cloned-id",
        source_type="Cloned managed copy",
        confirmed=True,
    ) is True
    service.delete_library.assert_called_once_with("cloned-id")
    overlay_manager.delete_overlay.assert_called_once_with("cloned-id")


def test_source_specific_actions_and_copy_path_are_safe(
    qapp: object,
    tmp_path: Path,
) -> None:
    """Registered rows disconnect but never delete; copying uses the exact local path."""
    widget = LibraryListWidget()
    entries = _entries(tmp_path)
    _require_callable(widget, "set_entries")(entries)

    actions = _require_callable(widget, "actions_for_library")
    assert set(actions("team-payments")) >= {
        "refresh",
        "pull",
        "switch_branch",
        "copy_path",
        "disconnect",
        "delete",
    }
    assert "delete" not in set(actions("local-archive"))

    copied = _require_callable(widget, "copy_library_path")("local-archive")
    assert copied == str(tmp_path / "archive")
    assert qapp.clipboard().text() == str(tmp_path / "archive")
    assert "copied" in widget.last_confirmation.lower()
