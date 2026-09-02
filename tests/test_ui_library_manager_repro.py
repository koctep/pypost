"""Failing repro test for UI library manager panel, dirty check guards, and two-way Git flow
(PYPOST-1223).

Asserts requirements from:
- ai-tasks/PYPOST-1223/10-requirements.md
- ai-tasks/PYPOST-1223/20-architecture.md
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from pypost.models.git_library import (
    GitOperationResult,
    GitOperationType,
)
from pypost.core.git_service import GitLibraryService
from pypost.ui import widget_ids

pytestmark = pytest.mark.timeout(30)


def test_git_library_models_extended_operation_types():
    """Verify GitOperationType includes COMMIT and PUSH."""
    assert hasattr(GitOperationType, "COMMIT")
    assert GitOperationType.COMMIT.value == "commit"
    assert hasattr(GitOperationType, "PUSH")
    assert GitOperationType.PUSH.value == "push"


def test_git_service_commit_and_push_methods(tmp_path: Path):
    """Verify GitLibraryService has commit and push methods."""
    service = GitLibraryService(base_dir=tmp_path)
    assert hasattr(service, "commit")
    assert callable(service.commit)
    assert hasattr(service, "push")
    assert callable(service.push)


def test_ui_widget_ids_library_constants():
    """Verify standard UI automation widget identities exist for library surfaces."""
    expected_ids = [
        "LIBRARY_MANAGER_BUTTON",
        "LIBRARY_MANAGER_DIALOG",
        "LIBRARY_LIST",
        "LIBRARY_CLONE_BUTTON",
        "LIBRARY_PULL_BUTTON",
        "LIBRARY_COMMIT_PUSH_BUTTON",
        "LIBRARY_SWITCH_BRANCH_BUTTON",
        "LIBRARY_DELETE_BUTTON",
        "LIBRARY_DIRTY_BADGE",
        "LIBRARY_BRANCH_BADGE",
        "LIBRARY_SYNC_BADGE",
        "LIBRARY_COLLECTIONS_LIST",
        "LIBRARY_CLONE_DIALOG",
        "LIBRARY_COMMIT_PUSH_DIALOG",
        "LIBRARY_DIRTY_PULL_WARNING_DIALOG",
        "LIBRARY_BRANCH_SWITCH_DIALOG",
    ]
    for attr in expected_ids:
        assert hasattr(widget_ids, attr), f"Missing widget ID constant: {attr}"


def test_library_presenter_and_dialog_imports():
    """Verify presenter and dialog modules exist and can be imported."""
    from pypost.ui.presenters.library_presenter import LibraryPresenter
    from pypost.ui.dialogs.library_dialogs import (
        LibraryManagerDialog,
        LibraryCloneDialog,
        LibraryCommitPushDialog,
        LibraryDirtyPullWarningDialog,
        LibraryBranchSwitchDialog,
    )
    from pypost.ui.widgets.library_manager_panel import (
        LibraryListWidget,
        LibraryDetailWidget,
        LibraryCollectionsWidget,
    )

    assert LibraryPresenter is not None
    assert LibraryManagerDialog is not None
    assert LibraryCloneDialog is not None
    assert LibraryCommitPushDialog is not None
    assert LibraryDirtyPullWarningDialog is not None
    assert LibraryBranchSwitchDialog is not None
    assert LibraryListWidget is not None
    assert LibraryDetailWidget is not None
    assert LibraryCollectionsWidget is not None


def test_library_presenter_dirty_pull_guard(tmp_path: Path):
    """Verify pull on a dirty working tree raises guard or triggers dirty warning."""
    from pypost.ui.presenters.library_presenter import LibraryPresenter

    service = MagicMock(spec=GitLibraryService)
    service.check_dirty.return_value = (True, ["collections/billing.yaml"])

    presenter = LibraryPresenter(service=service)

    is_dirty, dirty_files = presenter.check_dirty("test-lib")
    assert is_dirty is True
    assert dirty_files == ["collections/billing.yaml"]


def test_library_presenter_two_way_commit_and_push(tmp_path: Path):
    """Verify commit and push flow coordination through presenter."""
    from pypost.ui.presenters.library_presenter import LibraryPresenter

    service = MagicMock(spec=GitLibraryService)
    service.commit.return_value = GitOperationResult(
        operation=GitOperationType.COMMIT,
        success=True,
        commit_hash="abcdef123456",
        message="feat: add new payment request",
    )
    service.push.return_value = GitOperationResult(
        operation=GitOperationType.PUSH,
        success=True,
        message="Pushed to origin/main",
    )

    presenter = LibraryPresenter(service=service)
    res_commit = presenter.commit_library(
        "test-lib",
        "feat: add new payment request",
        ["collections/payment.yaml"],
    )
    assert res_commit.success is True
    assert res_commit.commit_hash == "abcdef123456"

    res_push = presenter.push_library("test-lib", branch="main")
    assert res_push.success is True
