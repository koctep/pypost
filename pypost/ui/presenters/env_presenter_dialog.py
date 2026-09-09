"""Environment manager dialog orchestration for :mod:`env_presenter`."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QDialog

from pypost.core.environment_import import load_import_candidates
from pypost.ui.dialogs.env_dialog import EnvironmentDialog

if TYPE_CHECKING:
    from pypost.ui.presenters.env_presenter import EnvPresenter

logger = logging.getLogger(__name__)


def open_environment_manager(
    presenter: EnvPresenter,
    dialog_factory: Callable[..., EnvironmentDialog] = EnvironmentDialog,
) -> None:
    """Run the dialog and commit only its explicitly accepted working copy."""
    if presenter._admission_closed():
        return
    current_env_name: str | None = presenter._env_selector.currentText()
    if presenter._env_selector.currentIndex() == 0:
        current_env_name = None

    logger.info("env_manager_dialog_opened current_env=%s", current_env_name)
    dialog = dialog_factory(
        presenter._environments,
        presenter._widget,
        current_env_name,
        log_hidden_key_names=presenter._settings.log_hidden_key_names,
        read_import_file=lambda path: load_import_candidates(path, presenter._storage),
        serialize_export_records=presenter._storage.serialize_environment_records,
    )
    result = dialog.exec()
    logger.info("env_manager_dialog_closed")
    if presenter._admission_closed():
        return
    logger.debug("environment_manager_closed_emitted")
    presenter.environment_manager_closed.emit()
    if result != QDialog.DialogCode.Accepted:
        logger.info("env_manager_changes_discarded")
        return

    presenter._environments = dialog.environments
    presenter._save_environments()
    logger.debug("environment_manager_changes_saved")
    if presenter._encryption_enabled():
        presenter._pending_env_manager_refresh = True
    presenter.load_environments()
    if not presenter._encryption_enabled():
        presenter._on_env_changed(presenter._env_selector.currentIndex())
