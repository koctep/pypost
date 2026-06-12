"""Strategy registry for collection tree item delete/rename by item_type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from pypost.core.request_manager import RequestManager

DeleteHandler = Callable[["RequestManager", str], bool]
RenameHandler = Callable[["RequestManager", str, str], bool]


@dataclass(frozen=True)
class CollectionItemStrategy:
    """Delete and rename handlers for one collection tree item type."""

    delete: DeleteHandler
    rename: RenameHandler


def _collection_delete(manager: RequestManager, item_id: str) -> bool:
    return manager.delete_collection(item_id)


def _collection_rename(manager: RequestManager, item_id: str, new_name: str) -> bool:
    return manager.rename_collection(item_id, new_name)


def _request_delete(manager: RequestManager, item_id: str) -> bool:
    return manager.delete_request(item_id)


def _request_rename(manager: RequestManager, item_id: str, new_name: str) -> bool:
    return manager.rename_request(item_id, new_name)


DEFAULT_COLLECTION_ITEM_STRATEGIES: dict[str, CollectionItemStrategy] = {
    "collection": CollectionItemStrategy(
        delete=_collection_delete,
        rename=_collection_rename,
    ),
    "request": CollectionItemStrategy(
        delete=_request_delete,
        rename=_request_rename,
    ),
}
