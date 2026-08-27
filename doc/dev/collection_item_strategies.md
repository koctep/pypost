# Collection Item Strategies and Dispatch Context

## Overview

Collection tree delete and rename are routed by `item_type` through a strategy
registry. `RequestManager.delete_collection_item` /
`rename_collection_item` build an `ItemDispatchContext`, then
`collection_item_dispatch` looks up a handler in
`DEFAULT_COLLECTION_ITEM_STRATEGIES`.

Handlers that call `_unpack_context` **must** unpack the full **3-tuple**.
Unpacking two values raises `ValueError: too many values to unpack (expected 2)`
and aborts delete/rename before any persistence (PYPOST-1193).

## Architecture

| Component | Role |
| --- | --- |
| `ItemDispatchContext` (`collection_item_dispatch.py`) | Carries `request_manager` plus optional `websocket_registry` and `mcp_client_registry` |
| `delete_collection_item` / `rename_collection_item` | Type → strategy lookup; logs `*_started` / `*_finished` / `*_unsupported_type` |
| `_unpack_context` (`collection_item_strategies.py`) | Returns a fixed 3-tuple for every built-in handler |
| Built-in handlers | Per-type delete/rename; ignore unused tuple slots with `_` |

```text
UI / CollectionTreeActions
  → RequestManager.delete_collection_item / rename_collection_item
    → ItemDispatchContext
      → collection_item_dispatch (type → strategy)
        → handler via _unpack_context → 3-tuple
```

## API / Usage

### `ItemDispatchContext`

```python
@dataclass(frozen=True)
class ItemDispatchContext:
    request_manager: RequestManager
    websocket_registry: Optional[WebSocketRegistry] = None
    mcp_client_registry: Optional[McpClientRegistry] = None
```

`RequestManager._item_dispatch_context()` fills all three fields when registries
are available.

### `_unpack_context(ctx) -> tuple[...]`

Always returns:

```text
(RequestManager, WebSocketRegistry | None, McpClientRegistry | None)
```

**Contract:** every handler that unpacks this return value must bind **three**
targets. Use `_` for slots the handler does not need.

| Item type | Correct unpack | Uses |
| --- | --- | --- |
| `"collection"` / `"request"` | `manager, _, _ = _unpack_context(ctx)` | `RequestManager` |
| `"websocket"` | `_, ws_registry, _ = _unpack_context(ctx)` | `WebSocketRegistry` |
| `"mcp_client"` | `_, _, mcp_registry = _unpack_context(ctx)` | `McpClientRegistry` |

Incorrect (breaks collection/request delete and rename):

```python
manager, _ = _unpack_context(ctx)  # ValueError: too many values to unpack
```

Correct:

```python
manager, _, _ = _unpack_context(ctx)
return manager.delete_request(item_id)
```

When adding a new optional field to `ItemDispatchContext`, grow
`_unpack_context` and update **all** handlers to the new arity in the same
change, or prefer attribute access on `ctx` instead of tuple unpacking.

## Configuration

None. Strategy map defaults to `DEFAULT_COLLECTION_ITEM_STRATEGIES`; callers may
pass an override map into dispatch for tests.

## Troubleshooting

### Delete/rename raises `ValueError: too many values to unpack (expected 2)`

A strategy handler still unpacks `_unpack_context` as two values. Align to the
3-tuple (`manager, _, _` or the registry pattern above).

### WebSocket or MCP rename/delete returns `False` without persistence

Context may lack the matching registry (`websocket_registry` /
`mcp_client_registry` is `None`). Confirm `RequestManager._item_dispatch_context`
attaches both registries.

### Unsupported type returns `False`

`item_type` is missing from the strategy map. Built-in keys:
`"collection"`, `"request"`, `"websocket"`, `"mcp_client"`.

## Testing

Regression coverage for the unpack contract and type routing:

```bash
make test PYTEST_ARGS="tests/test_collection_item_strategies.py tests/test_request_manager_delete.py"
```

Named checks include built-in strategy delegation, delete by type (request and
collection), collection-type rename, and empty-name rejection.

## Related docs

- [Collection Item Delete](collection_item_delete.md)
- [Collection Item Rename](collection_item_rename.md)
- [WebSocket Persistence and Interchange](websocket_persistence_and_interchange.md)
- [Collections WebSocket Context Menu](websocket_collections_menu.md)
