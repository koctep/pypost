# PYPOST-1128: WebSocket connection profile model, persistence and collection interchange

## Programming Language

Python is the implementation language for the application runtime, data models, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost is expanding beyond one-shot HTTP request/response execution to support persistent, real-time WebSocket communication (Epic PYPOST-1123). To make WebSocket endpoints first-class entities in PyPost, users must be able to configure, save, organize, and share WebSocket connection profiles alongside HTTP requests within collections.

This story (WS-2) establishes the domain models, storage persistence, indexing, item-type dispatch, and collection import/export mechanisms for WebSocket connection profiles:
- **Unified collection organization:** Users can save WebSocket connection profiles with complete configuration (endpoints, headers, query parameters, subprotocols, heartbeat policies, reconnect policies, message presets, sequences, and MCP metadata) inside collections next to HTTP requests.
- **Safe data interchange:** Collections containing both HTTP requests and WebSocket endpoints can be exported to JSON files and imported into other PyPost workspaces seamlessly, with separate item counts and automatic ID collision avoidance.
- **Backward compatibility and isolation:** Older collection files lacking WebSocket data load without error. The WebSocket domain model is cleanly separated from `RequestData` to avoid inflating memory copies during HTTP tab operations, and storage mechanisms persist data without leaking resolved environment secrets.
- **Extensible collection item dispatch:** Renaming, deleting, and resolving items by ID across heterogeneous collection contents (HTTP requests vs WebSocket profiles) operate uniformly and efficiently.

## User Stories

- As an **API developer / tester**, I want to save a WebSocket endpoint configuration—including URL, headers, query parameters, subprotocols, heartbeat settings, reconnection policies, reusable message presets, and test sequences—into a collection, so that I do not have to reconfigure connection parameters every time I test a real-time service.
- As a **collection author / team member**, I want to export collections containing both HTTP requests and WebSocket endpoints to a standard interchange file, so that I can share comprehensive API suites with my team.
- As a **user importing a collection**, I want the import process to report WebSocket profiles distinctly in the import summary and automatically assign fresh IDs if an imported profile collides with an existing ID, so that my existing saved endpoints are never accidentally overwritten or corrupted.
- As an **application operator / user**, I want older collection files created before WebSocket support to load cleanly with an empty list of WebSocket profiles without crashing or losing data.
- As a **security steward**, I want saved collection files and exported collections to store only raw template strings and variable placeholders (never resolved secrets or runtime values), ensuring credentials are not leaked during file sharing.
- As a **platform developer / maintainer**, I want collection item lookups and lifecycle actions (rename, delete, find by ID) to operate seamlessly across both HTTP requests and WebSocket endpoints through unified item dispatch with O(1) lookup performance.
- As an **AI agent workflow designer**, I want the six MCP tool configuration fields (`expose_as_mcp`, `mcp_description`, `mcp_params`, `mcp_probe_preset_id`, `mcp_probe_max_messages`, `mcp_probe_max_duration_ms`) defined and persisted on WebSocket profiles now, so that real-time endpoints are ready for agent probe integration in subsequent stories without schema migration.

## Definition of Done

- [ ] WebSocket domain models (`WebSocketConnection`, `HeartbeatPolicy`, `ReconnectPolicy`, `WebSocketMessagePreset`, `WebSocketSequence`, `WebSocketSequenceStep`, `WsMessageFormat`) are defined with comprehensive field validations.
- [ ] `Collection` model is extended with a `websockets` list, defaulting to an empty list.
- [ ] The six MCP configuration fields (`expose_as_mcp`, `mcp_description`, `mcp_params`, `mcp_probe_preset_id`, `mcp_probe_max_messages`, `mcp_probe_max_duration_ms`) are defined and persisted on `WebSocketConnection` as their single authoritative owner.
- [ ] A WebSocket connection profile with message presets and sequences survives a complete save -> load -> export -> import round trip unchanged.
- [ ] Collection export serializes `websockets` alongside `requests` in the exported JSON payload.
- [ ] Collection import parses `websockets`, reserves IDs to prevent collisions, assigns fresh IDs when collisions occur, and reports WebSocket profile counts distinctly from HTTP request counts in the import summary.
- [ ] Legacy collection files lacking a `websockets` key load cleanly with an empty list and re-save without corruption.
- [ ] No resolved variable values or environment secrets are written into collection files or exports (raw template expressions are strictly preserved).
- [ ] `WebSocketRegistry` maintains an in-memory index over collection WebSocket items and provides O(1) item resolution (`find_item`) resolving an ID to its kind (`"request"` or `"websocket"`), entity object, and owning collection.
- [ ] Item-type strategy dispatch for renaming and deleting collection items is cleanly extracted into a dedicated dispatch module and extended with `"websocket"` support.
- [ ] Existing `pypost/core/storage.py` logic remains unchanged and continues to round-trip collections via standard Pydantic serialization.
- [ ] Code metrics baseline check (`scripts/audit_baseline_metrics.py --check`) passes with `pypost/core/request_manager.py` under its re-derived cap and new modules registered with their respective caps.
- [ ] Comprehensive unit and integration tests verify all models, registry operations, import/export scenarios, backward compatibility, and dispatch mechanisms.

## Task Description

**Problem:**
PyPost currently supports saving only HTTP requests (`RequestData`) inside collections (`Collection.requests`). There is no data model, storage structure, or interchange support for saving WebSocket endpoints. Attempting to overload `RequestData` with WebSocket properties would violate design boundaries (deep-copy overhead on HTTP tabs, HTTP-specific semantics like status codes and methods). Furthermore, collection import/export routines and item management actions (rename, delete, find) only know about HTTP requests.

**Scope (In):**
- Domain models in `pypost/models/websocket.py` covering WebSocket connection settings, message formats, heartbeat and reconnect policies, presets, sequences, and the six MCP metadata fields.
- Extension of `Collection` in `pypost/models/models.py` with `websockets: List[WebSocketConnection]`.
- WebSocket profile indexing, CRUD operations, and kind-aware `find_item` in `pypost/core/websocket_registry.py`.
- Extraction of item-type dispatch from `RequestManager` into `pypost/core/collection_item_dispatch.py`, adding the `"websocket"` item strategy in `pypost/core/collection_item_strategies.py`, and re-deriving the LOC cap for `request_manager.py`.
- Collection export and import enhancements in `pypost/core/collection_export.py`, `pypost/core/collection_import.py`, and `pypost/core/collection_import_apply.py` to support WebSocket entries, ID reservation, collision re-keying, and distinct summary counts.
- Verification that `pypost/core/storage.py` requires no code changes to round-trip collections with WebSocket items.
- Full test coverage for models, registry, import/export, and baseline metrics compliance.

**Scope (Out):**
- User interface widgets, tabs, tree row rendering, or presenter components (covered in WS-4, WS-5, WS-6).
- Live socket networking, frame transport, event loops, or active session connections (covered in WS-1, WS-4).
- In-memory message ring buffer, streaming codecs, or stream export (covered in WS-3).
- MCP server tool registration, probe execution, or tool schema exposure behavior (covered in WS-9).

**Constraints and Assumptions:**
- Models in `pypost/models/websocket.py` must use standard library and Pydantic only (no Qt dependencies).
- Core registry and dispatch modules in `pypost/core/` must remain Qt-free and fully testable without a `QApplication`.
- `pypost/core/request_manager.py` has 0 lines of headroom; item dispatch extraction must re-derive its cap and register new modules in `scripts/audit_baseline_metrics.py`.
- `pypost/core/storage.py` must not be modified; existing `model_dump_json` and `Collection(**data)` must handle the new list naturally.
- Downgrade to older PyPost versions is lossy on re-save (Pydantic ignores unknown keys on load and drops them on subsequent write); this is expected behavior.
- All testing must be offline, deterministic, and enforce standard timeout constraints.

## Main Entities and Interactions

- **WebSocketConnection (Domain Model):** Represents a persistent configuration for connecting to a WebSocket endpoint.
  - Attributes: `id`, `name`, `url`, `headers`, `params`, `subprotocols`, `heartbeat` (`HeartbeatPolicy`), `reconnect` (`ReconnectPolicy`), `presets` (`List[WebSocketMessagePreset]`), `sequences` (`List[WebSocketSequence]`), `default_format` (`WsMessageFormat`), and MCP metadata fields (`expose_as_mcp`, `mcp_description`, `mcp_params`, `mcp_probe_preset_id`, `mcp_probe_max_messages`, `mcp_probe_max_duration_ms`).
- **HeartbeatPolicy:** Configures keep-alive ping interval and response timeout (`enabled`, `interval_seconds`, `timeout_seconds`).
- **ReconnectPolicy:** Configures automatic reconnection parameters (`enabled`, `max_attempts`, `initial_delay_seconds`, `backoff_multiplier`, `max_delay_seconds`).
- **WebSocketMessagePreset:** A saved message template with `id`, `name`, `format` (`WsMessageFormat`), and `payload` template.
- **WebSocketSequence & WebSocketSequenceStep:** Multi-step message transmission workflow with per-step delays (`delay_ms`), format, and preset reference or inline payload.
- **Collection (Extended Model):** Contains both `requests: List[RequestData]` and `websockets: List[WebSocketConnection]`.
- **WebSocketRegistry (Core Service):** In-memory indexing service that maintains lookups for WebSocket profiles across collections and provides O(1) kind-aware `find_item(item_id)` resolution returning `("request" | "websocket", object, owning_collection)`.
- **Collection Item Dispatcher:** Dispatches item-level actions (delete, rename) to appropriate handlers based on item kind (`"request"` or `"websocket"`).
- **Collection Import / Export Engine:** Serializes heterogeneous collection contents to/from JSON, reserves existing IDs, regenerates colliding IDs, and generates import summary statistics.

**Interaction Flow:**
1. A user creates or updates a WebSocket connection profile in a collection.
2. `WebSocketRegistry` updates its internal index mapping the profile ID to the connection object and its parent collection.
3. The storage layer writes the parent `Collection` model (including both `requests` and `websockets`) to disk as JSON.
4. When exporting a collection, the export engine produces a JSON structure containing both HTTP requests and WebSocket profiles.
5. When importing a collection, the import processor inspects both `requests` and `websockets`, reserves IDs to detect conflicts, generates fresh IDs where collisions exist, saves the collections, and returns a summary detailing imported requests and WebSocket profiles separately.
6. When an item action (rename, delete, open tab lookup) occurs by ID, the system calls `find_item` or item strategy dispatch to route the operation to the appropriate handler.

## Non-Functional Requirements

- **Data Integrity & Consistency:** Saved WebSocket profiles must deserialize identically upon loading and across export/import cycles.
- **Security & Secret Safety:** Only raw template strings are persisted; no resolved secrets or environment variable values are written to disk.
- **Performance & Efficiency:** Item lookups by ID across all loaded collections must execute in O(1) time without iterating through entire collection trees.
- **Backward Compatibility:** Existing collection JSON files without `websockets` must load without validation errors, initializing `websockets` to an empty list.
- **Architecture & Modularity:** Clean layering must be maintained: pure Python/Pydantic models in `pypost/models/`, Qt-free indexing and dispatch in `pypost/core/`, zero additions to `pypost/core/storage.py`, and strict enforcement of module size caps in `scripts/audit_baseline_metrics.py`.
- **Testability & Determinism:** All functionality must be verifiable via unit tests without GUI dependencies or live network connections.

## Q&A

**Q: Why is WebSocket connection data stored in a separate list (`Collection.websockets`) instead of reusing `Collection.requests`?**
**A:** `RequestData` is deep-copied during tab isolation in PyPost. Adding WebSocket presets, sequences, and connection policies to `RequestData` would bloat every HTTP tab. Moreover, a separate list ensures older PyPost builds safely ignore WebSocket entries without misinterpreting them as invalid HTTP requests.

**Q: Why are the six MCP fields defined in this story (WS-2) rather than in WS-9 (MCP Tool Exposure)?**
**A:** WS-2 is the single authoritative owner of the `WebSocketConnection` model and its persistence schema. Defining the MCP fields now ensures that the data model and storage schema are complete and stable, allowing WS-9 to implement MCP tool execution behavior without performing schema migrations or modifying model definitions.

**Q: Why is item-type dispatch being extracted from `RequestManager` into a new module?**
**A:** `pypost/core/request_manager.py` has 0 lines of headroom under the project's LOC caps enforced by `scripts/audit_baseline_metrics.py`. Extracting the item dispatch logic into `pypost/core/collection_item_dispatch.py` frees headroom in `request_manager.py` while providing a clean, dedicated dispatch seam for all collection item types.

**Q: Why does `pypost/core/storage.py` require no changes?**
**A:** `storage.py` uses `Collection.model_dump_json()` for serialization and `Collection(**data)` for deserialization. Since `Collection` is a Pydantic model with default values, extending it with `websockets: List[WebSocketConnection] = Field(default_factory=list)` automatically enables full serialization and deserialization without modifying storage logic.

**Q: How are ID collisions handled during collection import?**
**A:** The import planning process checks all imported request and WebSocket IDs against existing workspace IDs. If a collision is detected, a new UUID is generated for the colliding item before the collection is written, ensuring existing items are never overwritten.
