"""Comprehensive test suite for UI library manager panel, dirty check guards, and two-way Git
flow (PYPOST-1223).

Tests:
1. LibraryPresenter methods, signal emissions, and error mappings.
2. LibraryManagerDialog widget hierarchy, selection changes, and action dispatch.
3. LibraryCloneDialog form validation and hybrid auth config generation.
4. LibraryDirtyPullWarningDialog guard flows.
5. LibraryCommitPushDialog file staging selection and commit message validation.
6. LibraryBranchSwitchDialog branch listing and target selection.
7. Diagnostic error presentation mappings.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from PySide6.QtWidgets import QMessageBox

from pypost.core.git_service import GitLibraryService
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.models.git_library import (
    GitAuthMode,
    GitBranchInfo,
    GitDiagnosticError,
    GitDiagnosticErrorCode,
    GitOperationResult,
    GitOperationType,
    GitRepoStatus,
)
from pypost.models.library_manifest import (
    LibraryManifest,
)
from pypost.ui.dialogs.library_dialogs import (
    LibraryBranchSwitchDialog,
    LibraryCloneDialog,
    LibraryCommitPushDialog,
    LibraryDirtyPullWarningDialog,
    LibraryManagerDialog,
)
from pypost.ui.presenters.library_presenter import LibraryPresenter
from pypost.ui import widget_ids

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def sample_manifest() -> LibraryManifest:
    return LibraryManifest(
        schema_version="1.0.0",
        id="payments-library",
        name="Payments Team Library",
        version="2.1.0",
        description="Shared payment processing and checkout collections.",
        collections=[
            "collections/checkout.json",
            "collections/billing.json",
        ],
    )


@pytest.fixture
def sample_status(tmp_path: Path) -> GitRepoStatus:
    return GitRepoStatus(
        library_id="payments-library",
        repo_path=tmp_path / "payments-library",
        current_branch="main",
        commit_hash="1234567890abcdef",
        commit_message="feat: initial payments library commit",
        tracking_branch="origin/main",
        ahead_count=1,
        behind_count=0,
        is_clean=True,
        dirty_files=[],
        untracked_files=[],
    )


class TestLibraryPresenter:
    def test_load_libraries(self, tmp_path: Path):
        lib1 = tmp_path / "lib1"
        lib1.mkdir()
        (lib1 / ".git").mkdir()

        lib2 = tmp_path / "lib2"
        lib2.mkdir()
        (lib2 / "pypost-library.yaml").write_text("id: lib2\nname: Lib 2\n")

        service = GitLibraryService(base_dir=tmp_path)
        presenter = LibraryPresenter(service=service)

        signal_emitted = []
        presenter.libraries_loaded.connect(lambda libs: signal_emitted.append(libs))

        loaded = presenter.load_libraries()
        assert "lib1" in loaded
        assert "lib2" in loaded
        assert len(signal_emitted) == 1
        assert signal_emitted[0] == loaded

    def test_select_library_and_status(
        self,
        tmp_path: Path,
        sample_manifest: LibraryManifest,
        sample_status: GitRepoStatus,
    ):
        service = MagicMock(spec=GitLibraryService)
        service.status.return_value = sample_status
        service.get_library_dir.return_value = tmp_path / "payments-library"

        presenter = LibraryPresenter(service=service)

        status_signals = []
        presenter.status_updated.connect(lambda st: status_signals.append(st))

        with patch(
            "pypost.ui.presenters.library_presenter.find_and_read_manifest",
            return_value=(sample_manifest, tmp_path / "manifest.yaml"),
        ):
            status = presenter.select_library("payments-library")

        assert status == sample_status
        assert presenter.selected_library_id == "payments-library"
        assert presenter.cached_status == sample_status
        assert presenter.cached_manifest == sample_manifest
        assert len(status_signals) == 1

    def test_pull_library(self, sample_status: GitRepoStatus):
        service = MagicMock(spec=GitLibraryService)
        service.pull.return_value = GitOperationResult(
            operation=GitOperationType.PULL,
            success=True,
            message="Already up to date.",
        )
        service.status.return_value = sample_status

        presenter = LibraryPresenter(service=service)
        presenter.select_library("payments-library")

        completed_signals = []
        presenter.operation_completed.connect(lambda res: completed_signals.append(res))

        result = presenter.pull_library("payments-library")
        assert result.success is True
        assert len(completed_signals) == 1

    def test_pull_library_failure_emits_operation_failed(self):
        service = MagicMock(spec=GitLibraryService)
        service.pull.side_effect = GitDiagnosticError(
            code=GitDiagnosticErrorCode.AUTH_FAILED,
            message="Permission denied (publickey)",
        )

        presenter = LibraryPresenter(service=service)
        failed_signals = []
        presenter.operation_failed.connect(lambda err: failed_signals.append(err))

        with pytest.raises(GitDiagnosticError):
            presenter.pull_library("payments-library")

        assert len(failed_signals) == 1
        assert failed_signals[0].code == GitDiagnosticErrorCode.AUTH_FAILED

    def test_commit_and_push(self, sample_status: GitRepoStatus):
        service = MagicMock(spec=GitLibraryService)
        service.commit.return_value = GitOperationResult(
            operation=GitOperationType.COMMIT,
            success=True,
            commit_hash="abc1234",
            message="feat: new feature",
        )
        service.push.return_value = GitOperationResult(
            operation=GitOperationType.PUSH,
            success=True,
            message="Pushed",
        )
        service.status.return_value = sample_status

        presenter = LibraryPresenter(service=service)
        presenter.select_library("payments-library")

        res_c, res_p = presenter.commit_and_push(
            "payments-library",
            message="feat: new feature",
            files=["collections/checkout.json"],
            branch="main",
        )
        assert res_c.success is True
        assert res_p.success is True

    def test_clone_library(self, tmp_path: Path):
        service = MagicMock(spec=GitLibraryService)
        service.base_dir = tmp_path
        service.clone.return_value = GitOperationResult(
            operation=GitOperationType.CLONE,
            success=True,
            library_id="cloned-lib",
        )

        presenter = LibraryPresenter(service=service)
        res = presenter.clone_library(
            url="https://github.com/org/repo.git",
            library_id="cloned-lib",
        )
        assert res.success is True
        assert res.library_id == "cloned-lib"

    def test_switch_branch(self, sample_status: GitRepoStatus):
        service = MagicMock(spec=GitLibraryService)
        service.checkout.return_value = GitOperationResult(
            operation=GitOperationType.CHECKOUT,
            success=True,
            current_branch="feature-branch",
        )
        service.status.return_value = sample_status

        presenter = LibraryPresenter(service=service)
        res = presenter.switch_branch("payments-library", branch="feature-branch")
        assert res.success is True

    def test_delete_library(self):
        service = MagicMock(spec=GitLibraryService)
        service.delete_library.return_value = True
        service.base_dir = Path("/tmp")
        overlay_mgr = MagicMock(spec=LocalOverlayManager)

        presenter = LibraryPresenter(service=service, overlay_manager=overlay_mgr)
        deleted = presenter.delete_library("payments-library")
        assert deleted is True
        overlay_mgr.delete_overlay.assert_called_once_with("payments-library")

    def test_diagnostic_messages(self):
        for code in GitDiagnosticErrorCode:
            err = GitDiagnosticError(code=code, message="Test error message")
            title, desc = LibraryPresenter.get_diagnostic_message(err)
            assert title
            assert desc


class TestLibraryDialogs:
    def test_dirty_pull_warning_dialog_actions(self, qapp):
        dialog = LibraryDirtyPullWarningDialog(
            library_id="test-lib",
            dirty_files=["collections/payment.json", "overlay.json"],
        )
        assert dialog.action_selected == "cancel"

        dialog._on_commit_first()
        assert dialog.action_selected == "commit_first"

    def test_commit_push_dialog(self, qapp):
        dialog = LibraryCommitPushDialog(
            library_id="test-lib",
            dirty_files=["file1.json", "file2.json"],
            current_branch="main",
        )
        assert dialog.get_selected_files() == ["file1.json", "file2.json"]
        assert dialog.get_commit_message() == ""

        # Validation without commit message
        with patch.object(QMessageBox, "warning") as mock_warn:
            dialog._on_commit_only()
            mock_warn.assert_called_once()

        dialog.message_edit.setText("fix: update headers")
        dialog._on_commit_only()
        assert dialog.selected_action == "commit"

        dialog._on_commit_and_push()
        assert dialog.selected_action == "commit_and_push"

    def test_clone_dialog_auth_modes(self, qapp):
        dialog = LibraryCloneDialog()
        dialog.url_input.setText("https://github.com/org/repo.git")
        dialog.id_input.setText("custom-repo")
        dialog.branch_input.setText("dev")

        # PAT mode
        dialog.auth_mode_combo.setCurrentIndex(1)  # PAT
        dialog.username_input.setText("oauth2")
        dialog.token_input.setText("pat_secret_123")

        url, lib_id, branch, auth = dialog.get_clone_params()
        assert url == "https://github.com/org/repo.git"
        assert lib_id == "custom-repo"
        assert branch == "dev"
        assert auth.mode == GitAuthMode.PAT
        assert auth.username == "oauth2"
        assert auth.token == "pat_secret_123"

        # Custom SSH Key mode
        dialog.auth_mode_combo.setCurrentIndex(2)  # Custom SSH key
        dialog.key_path_input.setText("/home/user/.ssh/id_rsa")
        dialog.passphrase_input.setText("pass123")

        _, _, _, auth_key = dialog.get_clone_params()
        assert auth_key.mode == GitAuthMode.CUSTOM_SSH_KEY
        assert auth_key.key_path == "/home/user/.ssh/id_rsa"
        assert auth_key.passphrase == "pass123"

    def test_branch_switch_dialog(self, qapp):
        branches = [
            GitBranchInfo(name="main", short_name="main", is_current=True),
            GitBranchInfo(name="origin/feature", short_name="feature", is_remote=True),
        ]
        dialog = LibraryBranchSwitchDialog(
            library_id="test-lib",
            branches=branches,
            current_branch="main",
        )
        assert dialog.get_selected_branch() == "main"
        dialog.branch_combo.setCurrentIndex(1)
        assert dialog.get_selected_branch() == "feature"

    def test_library_manager_dialog_integration(
        self,
        qapp,
        tmp_path: Path,
        sample_manifest: LibraryManifest,
        sample_status: GitRepoStatus,
    ):
        service = MagicMock(spec=GitLibraryService)
        service.base_dir = tmp_path
        service.status.return_value = sample_status
        service.get_library_dir.return_value = tmp_path / "payments-library"

        presenter = LibraryPresenter(service=service)
        with patch.object(presenter, "load_libraries", return_value=["payments-library"]):
            dialog = LibraryManagerDialog(presenter=presenter)

        assert dialog.list_panel.list_widget.objectName() == widget_ids.LIBRARY_LIST
        assert dialog.detail_panel.pull_button.objectName() == widget_ids.LIBRARY_PULL_BUTTON
        assert (
            dialog.detail_panel.commit_push_button.objectName()
            == widget_ids.LIBRARY_COMMIT_PUSH_BUTTON
        )
        assert (
            dialog.detail_panel.switch_branch_button.objectName()
            == widget_ids.LIBRARY_SWITCH_BRANCH_BUTTON
        )
        assert dialog.detail_panel.delete_button.objectName() == widget_ids.LIBRARY_DELETE_BUTTON
