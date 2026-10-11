"""Editor presentation for a canonical, editable workspace collection copy."""
from __future__ import annotations

from collections.abc import Callable, Iterable
import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QLabel, QPushButton
from shiboken6 import isValid

from pypost.core.collection_creation import CreateWorkspaceCollection
from pypost.models.models import Collection

if TYPE_CHECKING:
    from pypost.ui.dialogs.mcp_servers_dialog import _McpServerEditor

logger = logging.getLogger(__name__)


class BuiltinCollectionCopy:
    """Own the copy action's presentation; persistence remains in the injected owner."""

    def __init__(
        self, editor: _McpServerEditor, create: CreateWorkspaceCollection | None,
        collections: Callable[[], Iterable[Collection]],
    ) -> None:
        self._editor, self._create, self._collections = editor, create, collections
        self._pending = False
        self._copied = False
        self.button = QPushButton("Copy for editing", editor)
        self.button.setAutoDefault(False)
        self.button.clicked.connect(self.copy)
        self.note = QLabel("Workspace copies no longer receive shipped updates.", editor)
        self.note.setWordWrap(True)
        editor._layout.addRow(self.button)
        editor._layout.addRow(self.note)

    def refresh(self) -> None:
        editor = self._editor
        local = editor._server_type.currentData() == "local"
        builtin = editor._collection_source.currentData() == "builtin"
        self.button.setVisible(local and builtin)
        self.button.setEnabled(
            self._create is not None and editor._builtin_collection.currentData() is not None
            and not self._pending and not editor._copy_closed
        )
        self.note.setVisible(local and (builtin or self._copied))

    def copy(self) -> None:
        editor = self._editor
        if (self._create is None or self._pending or editor._copy_closed
                or editor._server_type.currentData() != "local"
                or editor._collection_source.currentData() != "builtin"):
            return
        entry = editor._builtin_collection.currentData()
        if entry is None:
            return
        environment_id = editor._environment.currentData()
        self._pending = True
        self.refresh()
        reason = "load"
        try:
            source = editor._builtin_view.load_collection(entry.collection_path)
            source = source.model_copy(deep=True)
            source.name = entry.name
            reason = "create"
            candidate = self._create(source)
            if not isValid(editor) or editor._copy_closed:
                return
            if candidate is None:
                editor._error.setText("Workspace collections are busy. Please retry.")
                return
            collections = list(self._collections())
            if not any(col.id == candidate.id for col in collections):
                raise ValueError("Creation returned an unpublished collection")
            self._copied = True
            editor._select_data(editor._collection_source, "workspace")
            editor._collection.clear()
            for collection in collections:
                editor._collection.addItem(collection.name, collection.id)
            editor._select_data(editor._collection, candidate.id)
            editor._select_data(editor._environment, environment_id)
            editor._error.clear()
        except Exception:
            logger.warning("builtin_collection_copy_failed reason=%s", reason)
            if isValid(editor) and not editor._copy_closed:
                editor._error.setText(
                    "Could not create the editable collection copy. Please retry."
                )
        finally:
            self._pending = False
            if isValid(editor):
                self.refresh()
