"""Applying a planned collection import to live app state (PYPOST-987).

A free function over ``RequestManager``'s public surface rather than a method on
it, following the same shape as ``collection_item_strategies``: it keeps
``request_manager.py`` within its SOLID audit cap
(``scripts/audit_baseline_metrics.py``) and keeps the only bulk collection-write
loop in the codebase independently testable.

Deliberately not routed through ``RequestManager.create_collection``, which
rejects duplicate names: an import resolves name conflicts through an explicit
user decision and may legitimately produce a name that ``create_collection``
would refuse.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pypost.core.collection_messages import format_collection_entry_error
from pypost.models.models import Collection

if TYPE_CHECKING:
    from pypost.core.request_manager import RequestManager

logger = logging.getLogger(__name__)

MSG_SAVE_FAILED = "could not be saved ({reason})"


def apply_imported_collections(
    manager: "RequestManager",
    collections: list[Collection],
    persisted: list[Collection],
) -> list[str]:
    """Swap in the imported collection list and persist the changed subset.

    On any ``OSError`` during persist, reloads collections from durable storage
    so in-memory state matches disk before returning (PYPOST-1004). Happy path
    does not reload.

    Args:
        manager: The request manager owning the live collection list.
        collections: The complete list the app should hold afterwards.
        persisted: The subset whose files must be written. Collections the user
            chose to skip are absent, so their stored files stay untouched.

    Returns:
        One formatted message per collection that could not be written; empty
        when every write succeeded.
    """
    manager.apply_loaded_collections(collections)

    failures: list[str] = []
    for col in persisted:
        try:
            manager.storage.save_collection(col)
        except OSError as exc:
            logger.error(
                "collection_import_save_failed collection_id=%s error=%s",
                col.id,
                exc,
            )
            failures.append(
                format_collection_entry_error(col.name, MSG_SAVE_FAILED.format(reason=exc))
            )

    if failures:
        # Durable storage is source of truth after any mid-write save failure
        # (PYPOST-1004 approach C): align memory before callers refresh the tree.
        manager.reload_collections()
        logger.warning(
            "collection_import_reconciled failed_count=%d collection_count=%d",
            len(failures),
            len(manager.get_collections()),
        )

    logger.info(
        "collection_import_applied collection_count=%d persisted_count=%d failed_count=%d",
        len(collections),
        len(persisted),
        len(failures),
    )
    return failures
