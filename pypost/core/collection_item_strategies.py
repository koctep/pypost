"""Strategy registry for collection tree item delete/rename by item_type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from pypost.core.mcp_client_registry import McpClientRegistry
    from pypost.core.request_manager import RequestManager
    from pypost.core.websocket_registry import WebSocketRegistry

DeleteHandler = Callable[[Any, str], bool]
RenameHandler = Callable[[Any, str, str], bool]


@dataclass(frozen=True)
class CollectionItemStrategy:
    """Delete and rename handlers for one collection tree item type."""

    delete: DeleteHandler
    rename: RenameHandler


def _unpack_context(
    ctx: Any,
) -> tuple[RequestManager, WebSocketRegistry | None, McpClientRegistry | None]:
    if hasattr(ctx, "request_manager"):
        return (
            ctx.request_manager,
            getattr(ctx, "websocket_registry", None),
            getattr(ctx, "mcp_client_registry", None),
        )
    return (
        ctx,
        getattr(ctx, "websocket_registry", None),
        getattr(ctx, "mcp_client_registry", None),
    )


def _collection_delete(ctx: Any, item_id: str) -> bool:
    manager, _ = _unpack_context(ctx)
    return manager.delete_collection(item_id)


def _collection_rename(ctx: Any, item_id: str, new_name: str) -> bool:
    manager, _ = _unpack_context(ctx)
    return manager.rename_collection(item_id, new_name)


def _request_delete(ctx: Any, item_id: str) -> bool:
    manager, _ = _unpack_context(ctx)
    return manager.delete_request(item_id)


def _request_rename(ctx: Any, item_id: str, new_name: str) -> bool:
    manager, _ = _unpack_context(ctx)
    return manager.rename_request(item_id, new_name)


def _websocket_delete(ctx: Any, item_id: str) -> bool:
    _, ws_registry, _ = _unpack_context(ctx)
    if ws_registry is None:
        return False
    return ws_registry.delete_websocket(item_id)


def _websocket_rename(ctx: Any, item_id: str, new_name: str) -> bool:
    _, ws_registry, _ = _unpack_context(ctx)
    if ws_registry is None:
        return False
    return ws_registry.rename_websocket(item_id, new_name)


def _mcp_client_delete(ctx: Any, item_id: str) -> bool:
    _, _, mcp_registry = _unpack_context(ctx)
    if mcp_registry is None:
        return False
    return mcp_registry.delete_mcp_client(item_id)


def _mcp_client_rename(ctx: Any, item_id: str, new_name: str) -> bool:
    _, _, mcp_registry = _unpack_context(ctx)
    if mcp_registry is None:
        return False
    return mcp_registry.rename_mcp_client(item_id, new_name)


DEFAULT_COLLECTION_ITEM_STRATEGIES: dict[str, CollectionItemStrategy] = {
    "collection": CollectionItemStrategy(
        delete=_collection_delete,
        rename=_collection_rename,
    ),
    "request": CollectionItemStrategy(
        delete=_request_delete,
        rename=_request_rename,
    ),
    "websocket": CollectionItemStrategy(
        delete=_websocket_delete,
        rename=_websocket_rename,
    ),
    "mcp_client": CollectionItemStrategy(
        delete=_mcp_client_delete,
        rename=_mcp_client_rename,
    ),
}
