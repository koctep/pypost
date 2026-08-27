from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Optional

from pypost.core.collection_item_strategies import (
    DEFAULT_COLLECTION_ITEM_STRATEGIES,
    CollectionItemStrategy,
)

if TYPE_CHECKING:
    from pypost.core.mcp_client_registry import McpClientRegistry
    from pypost.core.request_manager import RequestManager
    from pypost.core.websocket_registry import WebSocketRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ItemDispatchContext:
    request_manager: RequestManager
    websocket_registry: Optional[WebSocketRegistry] = None
    mcp_client_registry: Optional[McpClientRegistry] = None


def delete_collection_item(
    context: ItemDispatchContext,
    item_id: str,
    item_type: str,
    strategies: Optional[dict[str, CollectionItemStrategy]] = None,
) -> bool:
    """Deletes a collection item by type using strategy dispatch."""
    logger.info("delete_collection_item_started item_id=%s item_type=%s", item_id, item_type)
    strategy_map = (
        strategies if strategies is not None else DEFAULT_COLLECTION_ITEM_STRATEGIES
    )
    strategy = strategy_map.get(item_type)
    if strategy is None:
        logger.warning(
            "delete_collection_item_unsupported_type item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        return False
    success = strategy.delete(context, item_id)
    logger.info(
        "delete_collection_item_finished item_id=%s item_type=%s success=%s",
        item_id,
        item_type,
        success,
    )
    return success


def rename_collection_item(
    context: ItemDispatchContext,
    item_id: str,
    item_type: str,
    new_name: str,
    strategies: Optional[dict[str, CollectionItemStrategy]] = None,
) -> bool:
    """Renames a collection item by type using strategy dispatch."""
    logger.info("rename_collection_item_started item_id=%s item_type=%s", item_id, item_type)
    strategy_map = (
        strategies if strategies is not None else DEFAULT_COLLECTION_ITEM_STRATEGIES
    )
    strategy = strategy_map.get(item_type)
    if strategy is None:
        logger.warning(
            "rename_collection_item_unsupported_type item_id=%s item_type=%s",
            item_id,
            item_type,
        )
        return False
    success = strategy.rename(context, item_id, new_name)
    logger.info(
        "rename_collection_item_finished item_id=%s item_type=%s success=%s",
        item_id,
        item_type,
        success,
    )
    return success
