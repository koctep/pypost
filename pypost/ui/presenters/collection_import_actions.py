"""Import Collection orchestration for the collections sidebar (PYPOST-987).

Split out of ``CollectionsPresenter`` the same way ``CollectionTreeActions`` and
``CollectionsAsyncLoader`` are: the presenter owns the tree and the panel, this
owns the picker → prompt → plan → persist → refresh flow. All decision logic
lives in the Qt-free ``pypost.core.collection_import``; this module only
sequences it against dialogs and app state.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtWidgets import QWidget

from pypost.core.collection_import import (
    CollectionImportFileError,
    find_collection_conflicts,
    format_collection_import_result,
    plan_collection_import,
)
from pypost.core.collection_import_apply import apply_imported_collections
from pypost.core.collection_messages import MSG_IMPORT_NO_VALID_COLLECTIONS
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection
from pypost.ui.collection_item_dialogs import (
    prompt_collection_import_conflict,
    prompt_import_collection_file,
    show_collection_import_invalid_file_error,
    show_collection_import_result,
)

logger = logging.getLogger(__name__)

ReadImportFile = Callable[[Path], "tuple[list[Collection], list[str]]"]


class CollectionImportActions:
    """Runs one Import Collection interaction end to end."""

    def __init__(
        self,
        parent: QWidget,
        request_manager: RequestManager,
        *,
        read_import_file: ReadImportFile,
        refresh_tree: Callable[[], None],
        restore_tree_state: Callable[[], None],
        emit_collections_changed: Callable[[], None],
    ) -> None:
        self._parent = parent
        self._request_manager = request_manager
        self._read_import_file = read_import_file
        self._refresh_tree = refresh_tree
        self._restore_tree_state = restore_tree_state
        self._emit_collections_changed = emit_collections_changed

    def import_collections(self) -> None:
        """Pick a file, resolve name conflicts, persist, and refresh the tree."""
        path = prompt_import_collection_file(self._parent)
        if path is None:
            return

        candidates = self._load(path)
        if candidates is None:
            return
        collections, parse_errors = candidates

        existing = self._request_manager.get_collections()
        decisions = self._resolve_conflicts(existing, collections)
        result = plan_collection_import(existing, collections, decisions)
        result.parse_errors.extend(parse_errors)

        save_errors = apply_imported_collections(
            self._request_manager,
            result.collections,
            result.persisted,
        )
        result.parse_errors.extend(save_errors)

        self._refresh_tree()
        self._restore_tree_state()
        self._emit_collections_changed()

        logger.info(
            "collection_import_completed added_count=%d updated_count=%d "
            "skipped_count=%d renamed_count=%d request_count=%d error_count=%d",
            len(result.added),
            len(result.updated),
            len(result.skipped),
            len(result.renamed),
            result.request_count,
            len(result.parse_errors),
        )
        success = bool(result.added or result.updated or result.renamed) and not save_errors
        show_collection_import_result(
            self._parent,
            format_collection_import_result(result),
            success=success,
        )

    def _load(self, path: Path) -> tuple[list[Collection], list[str]] | None:
        """Parse the picked file, or report why nothing can be imported from it.

        A file that cannot be read at all and a file that yields no usable
        collection get the same "nothing changed" treatment, so app state is
        never touched on either path.
        """
        try:
            collections, parse_errors = self._read_import_file(path)
        except CollectionImportFileError as exc:
            logger.warning("collection_import_file_invalid reason=%s", exc)
            show_collection_import_invalid_file_error(self._parent, str(exc))
            return None

        if not collections:
            logger.warning("collection_import_file_invalid reason=no_valid_collections")
            message = MSG_IMPORT_NO_VALID_COLLECTIONS
            if parse_errors:
                message = "\n".join([message, ""] + parse_errors)
            show_collection_import_invalid_file_error(self._parent, message)
            return None

        return collections, parse_errors

    def _resolve_conflicts(
        self,
        existing: list[Collection],
        candidates: list[Collection],
    ) -> dict[str, ImportConflictDecision]:
        conflicts = find_collection_conflicts(existing, candidates)
        decisions: dict[str, ImportConflictDecision] = {}
        apply_to_all: ImportConflictDecision | None = None
        for i, name in enumerate(conflicts):
            if apply_to_all is not None:
                decisions[name] = apply_to_all
                continue
            remaining_count = len(conflicts) - i - 1
            decision, use_for_all = prompt_collection_import_conflict(
                self._parent, name, remaining_count=remaining_count
            )
            decisions[name] = decision
            if use_for_all:
                apply_to_all = decision
        return decisions
