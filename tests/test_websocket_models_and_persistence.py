"""Tests for WebSocket domain models, persistence, and collection interchange (PYPOST-1128).

Red repro tests for:
- WebSocket domain models in pypost/models/websocket.py
- Collection.websockets field and backward compatibility
- Storage invariance in pypost/core/storage.py
- WebSocketRegistry in pypost/core/websocket_registry.py
- Item dispatch & strategies in pypost/core/collection_item_dispatch.py
- Collection export/import interchange in pypost/core/collection_export.py & collection_import.py
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from pypost.core.storage import StorageManager
from pypost.models.models import Collection, McpToolParam, RequestData
from pypost.models.websocket import (
    HeartbeatPolicy,
    ReconnectPolicy,
    WebSocketConnection,
    WebSocketMessagePreset,
    WebSocketSequence,
    WebSocketSequenceStep,
    WsMessageFormat,
)
from pypost.core.websocket_registry import WebSocketRegistry
from pypost.core.collection_item_dispatch import (
    ItemDispatchContext,
    delete_collection_item,
    rename_collection_item,
)
from pypost.core.collection_item_strategies import DEFAULT_COLLECTION_ITEM_STRATEGIES
from pypost.core.collection_export import (
    CollectionExportResult,
    CollectionsExportResult,
    build_export_payload,
    format_all_export_result,
    format_export_result,
    write_export_file,
)
from pypost.core.collection_import import (
    load_collection_import_candidates,
    plan_collection_import,
    format_collection_import_result,
)
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.request_manager import RequestManager
from tests.helpers import FakeStorageManager

pytestmark = pytest.mark.timeout(60)


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.setattr(
        "pypost.core.storage.user_data_dir",
        lambda app_name, app_author: str(tmp_path / "pypost-data"),
    )
    return StorageManager()


# ============================================================================
# 1. Domain Models Tests (pypost/models/websocket.py)
# ============================================================================


class TestWebSocketDomainModels:
    """Validate domain model schemas, defaults, and constraints."""

    def test_ws_message_format_enum_values(self):
        assert WsMessageFormat.TEXT == "text"
        assert WsMessageFormat.JSON == "json"
        assert WsMessageFormat.HEX == "hex"
        assert WsMessageFormat.BASE64 == "base64"
        assert len(WsMessageFormat) == 4

    def test_heartbeat_policy_defaults_and_validation(self):
        policy = HeartbeatPolicy()
        assert policy.enabled is True
        assert policy.interval_seconds == 30
        assert policy.timeout_seconds == 10

        custom = HeartbeatPolicy(enabled=False, interval_seconds=15, timeout_seconds=5)
        assert custom.enabled is False
        assert custom.interval_seconds == 15
        assert custom.timeout_seconds == 5

        # Bounds validation
        with pytest.raises(ValidationError):
            HeartbeatPolicy(interval_seconds=4)  # ge=5
        with pytest.raises(ValidationError):
            HeartbeatPolicy(interval_seconds=3601)  # le=3600
        with pytest.raises(ValidationError):
            HeartbeatPolicy(timeout_seconds=0)  # ge=1
        with pytest.raises(ValidationError):
            HeartbeatPolicy(timeout_seconds=301)  # le=300

    def test_reconnect_policy_defaults_and_validation(self):
        policy = ReconnectPolicy()
        assert policy.enabled is True
        assert policy.max_attempts == 5
        assert policy.initial_delay_seconds == 1.0
        assert policy.backoff_multiplier == 2.0
        assert policy.max_delay_seconds == 30.0

        custom = ReconnectPolicy(
            enabled=False,
            max_attempts=10,
            initial_delay_seconds=0.5,
            backoff_multiplier=1.5,
            max_delay_seconds=10.0,
        )
        assert custom.enabled is False
        assert custom.max_attempts == 10
        assert custom.initial_delay_seconds == 0.5
        assert custom.backoff_multiplier == 1.5
        assert custom.max_delay_seconds == 10.0

        # Bounds validation
        with pytest.raises(ValidationError):
            ReconnectPolicy(max_attempts=-1)  # ge=0
        with pytest.raises(ValidationError):
            ReconnectPolicy(max_attempts=101)  # le=100
        with pytest.raises(ValidationError):
            ReconnectPolicy(initial_delay_seconds=0.0)  # gt=0
        with pytest.raises(ValidationError):
            ReconnectPolicy(backoff_multiplier=0.9)  # ge=1.0
        with pytest.raises(ValidationError):
            ReconnectPolicy(max_delay_seconds=0.0)  # gt=0

    def test_websocket_message_preset_defaults_and_structure(self):
        preset = WebSocketMessagePreset()
        assert len(preset.id) > 0
        assert preset.name == "New Message"
        assert preset.format == WsMessageFormat.JSON
        assert preset.payload == ""

        custom = WebSocketMessagePreset(
            id="preset-1",
            name="Ping Payload",
            format=WsMessageFormat.TEXT,
            payload='{"action": "ping", "token": "{{TOKEN}}"}',
        )
        assert custom.id == "preset-1"
        assert custom.name == "Ping Payload"
        assert custom.format == WsMessageFormat.TEXT
        assert custom.payload == '{"action": "ping", "token": "{{TOKEN}}"}'

    def test_websocket_sequence_step_and_sequence_defaults(self):
        step = WebSocketSequenceStep(
            preset_id="preset-1",
            inline_payload="hello",
            format=WsMessageFormat.TEXT,
            delay_ms=250,
        )
        assert step.preset_id == "preset-1"
        assert step.inline_payload == "hello"
        assert step.format == WsMessageFormat.TEXT
        assert step.delay_ms == 250

        # delay_ms bounds
        with pytest.raises(ValidationError):
            WebSocketSequenceStep(delay_ms=-1)  # ge=0
        with pytest.raises(ValidationError):
            WebSocketSequenceStep(delay_ms=600_001)  # le=600_000

        seq = WebSocketSequence(name="Handshake Flow", steps=[step])
        assert len(seq.id) > 0
        assert seq.name == "Handshake Flow"
        assert len(seq.steps) == 1
        assert seq.steps[0].delay_ms == 250

    def test_websocket_connection_defaults_and_6_mcp_fields(self):
        conn = WebSocketConnection()
        assert len(conn.id) > 0
        assert conn.name == "New WebSocket"
        assert conn.url == ""
        assert conn.headers == {}
        assert conn.params == {}
        assert conn.subprotocols == []
        assert isinstance(conn.heartbeat, HeartbeatPolicy)
        assert isinstance(conn.reconnect, ReconnectPolicy)
        assert conn.presets == []
        assert conn.sequences == []
        assert conn.default_format == WsMessageFormat.JSON

        # 6 MCP fields authoritatively owned by WS-2
        assert conn.expose_as_mcp is False
        assert conn.mcp_description == ""
        assert conn.mcp_params == {}
        assert conn.mcp_probe_preset_id is None
        assert conn.mcp_probe_max_messages is None
        assert conn.mcp_probe_max_duration_ms is None

        # Custom initialization with MCP tool configuration
        custom = WebSocketConnection(
            id="ws-1",
            name="Crypto Ticker",
            url="wss://stream.binance.com/ws/{{SYMBOL}}@trade",
            headers={"Authorization": "Bearer {{SECRET_KEY}}"},
            params={"stream": "true"},
            subprotocols=["graphql-ws", "json"],
            heartbeat=HeartbeatPolicy(interval_seconds=20),
            reconnect=ReconnectPolicy(max_attempts=3),
            presets=[
                WebSocketMessagePreset(
                    id="p-1",
                    name="Subscribe",
                    format=WsMessageFormat.JSON,
                    payload='{"method": "SUBSCRIBE", "params": ["{{SYMBOL}}@trade"]}',
                )
            ],
            expose_as_mcp=True,
            mcp_description="Stream real-time crypto trades",
            mcp_params={
                "SYMBOL": McpToolParam(
                    type="string",
                    description="Trading pair symbol, e.g. btcusdt",
                    required=True,
                )
            },
            mcp_probe_preset_id="p-1",
            mcp_probe_max_messages=10,
            mcp_probe_max_duration_ms=5000,
        )
        assert custom.id == "ws-1"
        assert custom.name == "Crypto Ticker"
        assert custom.subprotocols == ["graphql-ws", "json"]
        assert custom.heartbeat.interval_seconds == 20
        assert custom.expose_as_mcp is True
        assert custom.mcp_params["SYMBOL"].type == "string"
        assert custom.mcp_probe_max_messages == 10
        assert custom.mcp_probe_max_duration_ms == 5000


# ============================================================================
# 2. Collection.websockets Field & Backward Compatibility
# ============================================================================


class TestCollectionWebSocketsFieldAndBackwardCompatibility:
    """Validate Collection model extension and backward-compatibility."""

    def test_collection_defaults_to_empty_websockets_list(self):
        col = Collection(id="c-1", name="API")
        assert hasattr(col, "websockets")
        assert col.websockets == []
        assert col.requests == []

    def test_legacy_collection_json_without_websockets_loads_cleanly(self):
        legacy_data = {
            "id": "col-legacy",
            "name": "Legacy Collection",
            "requests": [
                {
                    "id": "r-1",
                    "name": "Get Users",
                    "method": "GET",
                    "url": "https://api.example.com/users",
                }
            ],
        }
        col = Collection.model_validate(legacy_data)
        assert col.id == "col-legacy"
        assert len(col.requests) == 1
        assert col.websockets == []

    def test_collection_roundtrip_with_websockets(self):
        conn = WebSocketConnection(
            id="ws-roundtrip",
            name="Live Feed",
            url="wss://example.com/ws",
            presets=[
                WebSocketMessagePreset(
                    id="p-rt",
                    name="Ping",
                    payload='{"type":"ping"}',
                )
            ],
        )
        col = Collection(
            id="col-mixed",
            name="Mixed Collection",
            requests=[RequestData(id="r-1", name="Status Check")],
            websockets=[conn],
        )
        dumped = col.model_dump(mode="json")
        assert "websockets" in dumped
        assert len(dumped["websockets"]) == 1
        assert dumped["websockets"][0]["id"] == "ws-roundtrip"

        reloaded = Collection.model_validate(dumped)
        assert len(reloaded.websockets) == 1
        assert reloaded.websockets[0].name == "Live Feed"
        assert len(reloaded.websockets[0].presets) == 1
        assert reloaded.websockets[0].presets[0].payload == '{"type":"ping"}'


# ============================================================================
# 3. Storage Invariance Tests (pypost/core/storage.py)
# ============================================================================


class TestStorageManagerWebSocketInvariance:
    """Verify StorageManager saves and loads WebSocket items without modifications."""

    def test_save_and_load_collection_containing_websockets(self, tmp_path, monkeypatch):
        storage = _make_storage(tmp_path, monkeypatch)
        ws_conn = WebSocketConnection(
            id="ws-stored-1",
            name="Notifications WS",
            url="wss://api.example.com/notifications",
            headers={"X-Auth": "secret"},
            presets=[
                WebSocketMessagePreset(id="pr-1", name="Subscribe", payload='{"sub": 1}')
            ],
        )
        col = Collection(
            id="col-storage-1",
            name="Production Col",
            requests=[RequestData(id="r-1", name="Health check")],
            websockets=[ws_conn],
        )

        storage.save_collection(col)

        file_path = storage.collections_path / "col-storage-1.json"
        assert file_path.exists()
        raw_json = json.loads(file_path.read_text(encoding="utf-8"))
        assert "websockets" in raw_json
        assert raw_json["websockets"][0]["id"] == "ws-stored-1"

        loaded_collections = storage.load_collections()
        assert len(loaded_collections) == 1
        loaded_col = loaded_collections[0]
        assert loaded_col.id == "col-storage-1"
        assert len(loaded_col.requests) == 1
        assert len(loaded_col.websockets) == 1
        assert loaded_col.websockets[0].id == "ws-stored-1"
        assert loaded_col.websockets[0].name == "Notifications WS"
        assert loaded_col.websockets[0].presets[0].payload == '{"sub": 1}'

    def test_legacy_collection_file_persists_safely_when_updated_with_websocket(
        self, tmp_path, monkeypatch
    ):
        storage = _make_storage(tmp_path, monkeypatch)
        legacy_file = storage.collections_path / "legacy-col.json"
        storage.collections_path.mkdir(parents=True, exist_ok=True)
        legacy_file.write_text(
            json.dumps(
                {
                    "id": "legacy-col",
                    "name": "Legacy",
                    "requests": [{"id": "r-1", "name": "Req 1"}],
                }
            ),
            encoding="utf-8",
        )

        loaded = storage.load_collections()
        assert len(loaded) == 1
        col = loaded[0]
        assert col.websockets == []

        # Add a websocket and save
        col.websockets.append(
            WebSocketConnection(id="ws-added", name="Added WS", url="ws://localhost:8080")
        )
        storage.save_collection(col)

        reloaded = storage.load_collections()
        assert len(reloaded[0].websockets) == 1
        assert reloaded[0].websockets[0].id == "ws-added"


# ============================================================================
# 4. WebSocket Registry Tests (pypost/core/websocket_registry.py)
# ============================================================================


class TestWebSocketRegistry:
    """Validate WebSocketRegistry index, CRUD operations, and kind-aware lookup."""

    def test_registry_indexes_collections_and_provides_crud(self):
        ws1 = WebSocketConnection(id="ws-1", name="Stream 1", url="wss://s1.example.com")
        ws2 = WebSocketConnection(id="ws-2", name="Stream 2", url="wss://s2.example.com")
        col1 = Collection(id="c1", name="Col 1", websockets=[ws1])
        col2 = Collection(id="c2", name="Col 2", websockets=[ws2])

        storage = FakeStorageManager([col1, col2])
        req_mgr = RequestManager(storage)
        registry = WebSocketRegistry(request_manager=req_mgr, storage=storage)

        # get_websockets
        websockets = registry.get_websockets()
        assert len(websockets) == 2
        assert {ws.id for ws in websockets} == {"ws-1", "ws-2"}

        # find_websocket
        match = registry.find_websocket("ws-1")
        assert match is not None
        conn, owning_col = match
        assert conn.id == "ws-1"
        assert owning_col.id == "c1"

        assert registry.find_websocket("unknown") is None

        # save_websocket (update)
        conn.name = "Updated Stream 1"
        registry.save_websocket(conn, "c1")
        updated_match = registry.find_websocket("ws-1")
        assert updated_match is not None
        assert updated_match[0].name == "Updated Stream 1"

        # save_websocket (new item into c2)
        ws3 = WebSocketConnection(id="ws-3", name="Stream 3", url="wss://s3.example.com")
        registry.save_websocket(ws3, "c2")
        assert len(registry.get_websockets()) == 3
        assert registry.find_websocket("ws-3")[1].id == "c2"

        # rename_websocket
        renamed = registry.rename_websocket("ws-3", "Renamed Stream 3")
        assert renamed is True
        assert registry.find_websocket("ws-3")[0].name == "Renamed Stream 3"

        # delete_websocket
        deleted = registry.delete_websocket("ws-2")
        assert deleted is True
        assert registry.find_websocket("ws-2") is None
        assert len(registry.get_websockets()) == 2
        assert len(col2.websockets) == 1  # only ws3 remains

    def test_registry_find_item_resolves_requests_and_websockets_in_o1(self):
        req = RequestData(id="req-100", name="HTTP Request", method="GET")
        ws = WebSocketConnection(id="ws-200", name="WS Profile", url="wss://test.com")
        col = Collection(id="c-mixed", name="Mixed Col", requests=[req], websockets=[ws])

        storage = FakeStorageManager([col])
        req_mgr = RequestManager(storage)
        registry = WebSocketRegistry(request_manager=req_mgr, storage=storage)

        # Lookup HTTP request
        req_lookup = registry.find_item("req-100")
        assert req_lookup is not None
        kind, item, owning_col = req_lookup
        assert kind == "request"
        assert isinstance(item, RequestData)
        assert item.id == "req-100"
        assert owning_col.id == "c-mixed"

        # Lookup WebSocket profile
        ws_lookup = registry.find_item("ws-200")
        assert ws_lookup is not None
        kind, item, owning_col = ws_lookup
        assert kind == "websocket"
        assert isinstance(item, WebSocketConnection)
        assert item.id == "ws-200"
        assert owning_col.id == "c-mixed"

        # Missing item
        assert registry.find_item("missing-id") is None

    def test_registry_drop_collection_websockets_from_index(self):
        ws = WebSocketConnection(id="ws-drop-1", name="WS Drop", url="wss://drop.com")
        col = Collection(id="c-drop", name="Col Drop", websockets=[ws])
        storage = FakeStorageManager([col])
        req_mgr = RequestManager(storage)
        registry = WebSocketRegistry(request_manager=req_mgr, storage=storage)

        assert registry.find_websocket("ws-drop-1") is not None
        registry.drop_collection_websockets_from_index(col)
        assert registry.find_websocket("ws-drop-1") is None


# ============================================================================
# 5. Collection Item Dispatch & Strategies Tests
# ============================================================================


class TestCollectionItemDispatchAndStrategies:
    """Validate item dispatch logic and websocket strategy registration."""

    def test_default_strategies_includes_websocket(self):
        assert "collection" in DEFAULT_COLLECTION_ITEM_STRATEGIES
        assert "request" in DEFAULT_COLLECTION_ITEM_STRATEGIES
        assert "websocket" in DEFAULT_COLLECTION_ITEM_STRATEGIES

    def test_item_dispatch_routes_websocket_rename_and_delete(self):
        ws = WebSocketConnection(id="ws-target", name="Initial WS", url="ws://echo.org")
        col = Collection(id="col-d", name="Dispatch Col", websockets=[ws])

        storage = FakeStorageManager([col])
        req_mgr = RequestManager(storage)
        ws_reg = WebSocketRegistry(request_manager=req_mgr, storage=storage)
        ctx = ItemDispatchContext(request_manager=req_mgr, websocket_registry=ws_reg)

        # Rename via dispatch
        renamed = rename_collection_item(ctx, "ws-target", "websocket", "Dispatch Renamed WS")
        assert renamed is True
        assert ws_reg.find_websocket("ws-target")[0].name == "Dispatch Renamed WS"

        # Delete via dispatch
        deleted = delete_collection_item(ctx, "ws-target", "websocket")
        assert deleted is True
        assert ws_reg.find_websocket("ws-target") is None
        assert col.websockets == []


# ============================================================================
# 6. Export / Import Interchange Tests
# ============================================================================


class TestCollectionInterchangeExportImport:
    """Validate export and import handling for collections with WebSocket profiles."""

    def test_build_export_payload_includes_websockets_and_preserves_templates(self):
        ws = WebSocketConnection(
            id="ws-exp",
            name="Ticker Feed",
            url="wss://{{HOST}}/ws/{{PAIR}}",
            headers={"Authorization": "Bearer {{SECRET_TOKEN}}"},
            presets=[
                WebSocketMessagePreset(
                    id="p-exp",
                    name="Ping",
                    payload='{"auth": "{{SECRET_TOKEN}}"}',
                )
            ],
            expose_as_mcp=True,
            mcp_description="Crypto live ticker",
        )
        col = Collection(
            id="col-exp",
            name="Streaming API",
            requests=[RequestData(id="r-exp", name="HTTP Health")],
            websockets=[ws],
        )

        payload = build_export_payload(col)
        assert payload["name"] == "Streaming API"
        assert len(payload["requests"]) == 1
        assert "websockets" in payload
        assert len(payload["websockets"]) == 1

        ws_data = payload["websockets"][0]
        assert ws_data["name"] == "Ticker Feed"
        assert ws_data["url"] == "wss://{{HOST}}/ws/{{PAIR}}"
        assert ws_data["headers"] == {"Authorization": "Bearer {{SECRET_TOKEN}}"}
        assert ws_data["expose_as_mcp"] is True
        # Ensure raw template strings are preserved without evaluating/leaking
        assert ws_data["presets"][0]["payload"] == '{"auth": "{{SECRET_TOKEN}}"}'

    def test_export_results_format_includes_websocket_counts(self):
        single_res = CollectionExportResult(
            collection_name="Trading API",
            request_count=2,
            websocket_count=3,
            path=Path("/tmp/trading.json"),
        )
        single_formatted = format_export_result(single_res)
        assert "Trading API" in single_formatted
        assert "2 request(s)" in single_formatted
        assert "3 websocket(s)" in single_formatted

        all_res = CollectionsExportResult(
            collection_count=2,
            request_count=4,
            websocket_count=5,
            path=Path("/tmp/all.json"),
        )
        all_formatted = format_all_export_result(all_res)
        assert "2 collection(s)" in all_formatted
        assert "4 request(s)" in all_formatted
        assert "5 websocket(s)" in all_formatted

    def test_export_and_import_roundtrip_with_websockets(self, tmp_path):
        ws = WebSocketConnection(
            id="ws-rt-1",
            name="Telemetry Stream",
            url="wss://telemetry.example.com",
            subprotocols=["binary-stream"],
            heartbeat=HeartbeatPolicy(interval_seconds=15),
            presets=[
                WebSocketMessagePreset(id="p-1", name="Init", payload='{"mode": "debug"}')
            ],
        )
        col = Collection(
            id="col-rt-1",
            name="Telemetry Collection",
            requests=[RequestData(id="r-rt-1", name="Get Version")],
            websockets=[ws],
        )

        export_path = tmp_path / "telemetry_export.json"
        write_export_file(export_path, build_export_payload(col))

        imported, parse_errors = load_collection_import_candidates(export_path)
        assert parse_errors == []
        assert len(imported) == 1
        imported_col = imported[0]
        assert imported_col.name == "Telemetry Collection"
        assert len(imported_col.requests) == 1
        assert len(imported_col.websockets) == 1

        imported_ws = imported_col.websockets[0]
        assert imported_ws.name == "Telemetry Stream"
        assert imported_ws.url == "wss://telemetry.example.com"
        assert imported_ws.subprotocols == ["binary-stream"]
        assert imported_ws.heartbeat.interval_seconds == 15
        assert imported_ws.presets[0].payload == '{"mode": "debug"}'

    def test_import_plan_re_keys_colliding_websocket_ids(self):
        existing_ws = WebSocketConnection(id="shared-ws-id", name="Existing WS")
        existing_col = Collection(
            id="c-exist",
            name="Existing Col",
            websockets=[existing_ws],
        )

        incoming_ws = WebSocketConnection(id="shared-ws-id", name="Incoming WS")
        incoming_col = Collection(
            id="c-incoming",
            name="New Col",
            websockets=[incoming_ws],
        )

        plan = plan_collection_import(
            existing=[existing_col],
            incoming=[incoming_col],
            conflict_decisions={},
        )

        assert len(plan.collections) == 2
        # Existing ws id unchanged
        assert plan.collections[0].websockets[0].id == "shared-ws-id"
        # Incoming ws id re-keyed to avoid collision
        imported_ws = plan.collections[1].websockets[0]
        assert imported_ws.id != "shared-ws-id"
        assert imported_ws.name == "Incoming WS"
        assert plan.websocket_count == 1

    def test_import_format_summary_reports_websocket_count_separately(self):
        ws = WebSocketConnection(id="ws-sum", name="Sum WS")
        col = Collection(
            id="col-sum",
            name="Summary API",
            requests=[RequestData(id="r-sum", name="Sum Req")],
            websockets=[ws],
        )

        plan = plan_collection_import(
            existing=[Collection(id="col-prev", name="Summary API")],
            incoming=[col],
            conflict_decisions={"Summary API": ImportConflictDecision.KEEP_BOTH},
        )
        summary = format_collection_import_result(plan)
        assert "Summary API" in summary
        assert "1 request" in summary.lower() or "requests" in summary.lower()
        assert "1 websocket" in summary.lower() or "websockets" in summary.lower()
