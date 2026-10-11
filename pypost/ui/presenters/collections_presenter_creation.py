"""Save-before-publication collection creation owned by CollectionsPresenter."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pypost.core.collection_creation import prepare_workspace_collection
from pypost.models.models import Collection

if TYPE_CHECKING:
    from pypost.ui.presenters.collections_presenter import CollectionsPresenter

logger = logging.getLogger(__name__)


def create_workspace_collection(
    presenter: CollectionsPresenter, source: Collection
) -> Collection | None:
    """Return a canonical saved copy, or reject a busy/disposed presenter."""
    reason = (
        "teardown" if presenter._collection_creation_closed else
        "import_busy" if presenter._import_actions.is_busy() else
        "load_busy" if presenter._async_loader is not None and presenter._async_loader.is_busy()
        else None
    )
    if reason is not None:
        logger.info("workspace_collection_creation_rejected reason=%s", reason)
        return None
    manager = presenter._request_manager
    existing = manager.get_collections()
    plan = prepare_workspace_collection(source, existing)
    candidate = plan.persisted[0]
    logger.info(
        "workspace_collection_creation_admitted collection_id=%s "
        "existing_count=%d request_count=%d",
        candidate.id, len(existing), len(candidate.requests),
    )
    try:
        manager.storage.save_collection(candidate)
    except Exception:
        logger.warning(
            "workspace_collection_creation_failed collection_id=%s reason=save", candidate.id
        )
        try:
            # Never pass collection_name: legacy name files can belong to other data.
            manager.storage.delete_collection(candidate.id)
        except Exception:
            logger.error("workspace_collection_cleanup_failed collection_id=%s", candidate.id)
        raise
    manager.apply_loaded_collections(plan.collections)
    presenter.refresh_tree()
    presenter.restore_tree_state()
    presenter.collections_changed.emit()
    logger.info(
        "workspace_collection_creation_succeeded collection_id=%s "
        "request_count=%d collection_count=%d",
        candidate.id, len(candidate.requests), len(plan.collections),
    )
    return candidate
