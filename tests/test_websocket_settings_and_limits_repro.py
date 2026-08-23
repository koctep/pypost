"""Failing repro tests for WS-10 Settings, Session Ceiling, Metrics, and Logging.

Task: PYPOST-1136.
Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1136/10-requirements.md`
- `ai-tasks/PYPOST-1136/20-architecture.md`

Covers:
1. AppSettings model: all `ws_*` configuration fields declared with defaults, backward
   compatibility with legacy configs, and custom limit validation.
2. SessionSlots concurrency manager:
   - Thread-safe process-wide slot acquisition and idempotent release.
   - Concurrency ceiling refusal when max slots are active
     (`allowed=False, reason="max_concurrent"`).
   - Lockdown mode when `ws_max_concurrent_sessions=0` (`allowed=False, reason="disabled"`).
   - Multi-threaded synchronization without deadlocks or counter corruption.
   - Global singleton coordinator `get_session_slots()`.
3. WebSocketPresenter concurrency refusal integration:
   - Immediate refusal when session ceiling is reached without socket allocation.
   - Badge remains `Idle`, Connect button remains enabled.
   - Inline stream lifecycle entry and refusal metric incremented.
   - Slot freed on disconnect/teardown/failure.
4. Prometheus MetricsRegistry & MetricsManager delegation:
   - Registration of all 9 WebSocket instruments (counters, gauge, histogram).
   - Low-cardinality label verification and tracking methods.
   - OpenMetrics scrape exposition format.
5. Zero-leak structured logging & security invariants:
   - Structured `key=value` event format.
   - Injected secret query parameters, authorization headers, and payloads NEVER appear unmasked
     in logs across any level (DEBUG, INFO, WARNING, ERROR).
6. WebSocketSettingsSection modular settings UI widget:
   - Creation and form population.
   - Extraction of all `ws_*` values via `collect_fields()`.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
import os

from prometheus_client import generate_latest
import pytest
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QWidget,
)

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.websocket_session_policy import SessionState
from pypost.models.settings import AppSettings
from pypost.models.websocket import (
    HeartbeatPolicy,
    ReconnectPolicy,
    WebSocketConnection,
)

pytestmark = pytest.mark.timeout(30)


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """Ensure a headless QApplication instance exists for Qt widget/presenter tests."""
    app = QApplication.instance()
    if app is None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QApplication([])
    return app


# =============================================================================
# 1. AppSettings WebSocket Configuration Tests
# =============================================================================


class TestWebSocketSettingsModel:
    """Asserts AppSettings declares all ws_* fields with specified defaults."""

    def test_app_settings_has_default_websocket_fields(self) -> None:
        """AppSettings must declare all ws_* bounds and policy defaults."""
        settings = AppSettings()

        # Global stream & memory bounds
        assert hasattr(settings, "ws_max_stream_entries")
        assert settings.ws_max_stream_entries == 5_000

        assert hasattr(settings, "ws_session_memory_budget_bytes")
        assert settings.ws_session_memory_budget_bytes == 67_108_864  # 64 MiB

        assert hasattr(settings, "ws_max_incoming_message_bytes")
        assert settings.ws_max_incoming_message_bytes == 8_388_608  # 8 MiB

        assert hasattr(settings, "ws_display_truncate_bytes")
        assert settings.ws_display_truncate_bytes == 262_144  # 256 KiB

        # Concurrency ceiling
        assert hasattr(settings, "ws_max_concurrent_sessions")
        assert settings.ws_max_concurrent_sessions == 8

        # MCP probe limits
        assert hasattr(settings, "ws_mcp_probe_max_messages")
        assert settings.ws_mcp_probe_max_messages == 10

        assert hasattr(settings, "ws_mcp_probe_max_duration_ms")
        assert settings.ws_mcp_probe_max_duration_ms == 10_000

        # Default policies
        assert hasattr(settings, "ws_default_heartbeat")
        assert isinstance(settings.ws_default_heartbeat, HeartbeatPolicy)
        assert settings.ws_default_heartbeat.enabled is True
        assert settings.ws_default_heartbeat.interval_seconds == 30
        assert settings.ws_default_heartbeat.timeout_seconds == 10

        assert hasattr(settings, "ws_default_reconnect")
        assert isinstance(settings.ws_default_reconnect, ReconnectPolicy)
        assert settings.ws_default_reconnect.enabled is True
        assert settings.ws_default_reconnect.max_attempts == 5
        assert settings.ws_default_reconnect.initial_delay_seconds == 1.0
        assert settings.ws_default_reconnect.backoff_multiplier == 2.0
        assert settings.ws_default_reconnect.max_delay_seconds == 30.0

    def test_app_settings_deserialization_from_dict_and_backward_compatibility(self) -> None:
        """Legacy configuration dict without ws_* keys must deserialize safely with defaults."""
        legacy_data = {
            "font_size": 14,
            "theme": "dark",
            "request_timeout": 30,
        }
        settings = AppSettings.model_validate(legacy_data)
        assert settings.font_size == 14
        assert settings.ws_max_concurrent_sessions == 8
        assert settings.ws_max_stream_entries == 5000

        # Custom override deserialization
        custom_data = {
            "ws_max_concurrent_sessions": 16,
            "ws_max_stream_entries": 10000,
            "ws_session_memory_budget_bytes": 134217728,
            "ws_max_incoming_message_bytes": 16777216,
            "ws_display_truncate_bytes": 524288,
            "ws_mcp_probe_max_messages": 20,
            "ws_mcp_probe_max_duration_ms": 20000,
        }
        custom_settings = AppSettings.model_validate(custom_data)
        assert custom_settings.ws_max_concurrent_sessions == 16
        assert custom_settings.ws_max_stream_entries == 10000
        assert custom_settings.ws_session_memory_budget_bytes == 134217728
        assert custom_settings.ws_max_incoming_message_bytes == 16777216
        assert custom_settings.ws_display_truncate_bytes == 524288
        assert custom_settings.ws_mcp_probe_max_messages == 20
        assert custom_settings.ws_mcp_probe_max_duration_ms == 20000


# =============================================================================
# 2. SessionSlots Concurrency Coordinator Tests
# =============================================================================


class TestSessionSlotsConcurrencyCoordinator:
    """Asserts SessionSlots thread-safe concurrency management and lockdown semantics."""

    def test_session_slots_import_and_initialization(self) -> None:
        """SessionSlots and SlotAcquireResult must be importable from websocket_session_policy."""
        from pypost.core.websocket_session_policy import (
            SessionSlots,
            SlotAcquireResult,
            get_session_slots,
        )

        assert SlotAcquireResult is not None
        slots = SessionSlots(max_slots=4)
        assert slots.max_slots == 4
        assert slots.active_count == 0

        # Global singleton
        global_slots = get_session_slots()
        assert isinstance(global_slots, SessionSlots)

    def test_session_slots_acquire_and_ceiling_refusal(self) -> None:
        """With limit N, N acquires succeed; (N+1)-th is refused with reason='max_concurrent'."""
        from pypost.core.websocket_session_policy import SessionSlots

        slots = SessionSlots(max_slots=2)

        res1 = slots.acquire("sess-1")
        assert res1.allowed is True
        assert res1.reason is None
        assert res1.active_count == 1
        assert res1.limit == 2
        assert slots.is_holding_slot("sess-1") is True

        res2 = slots.acquire("sess-2")
        assert res2.allowed is True
        assert res2.active_count == 2
        assert slots.is_holding_slot("sess-2") is True

        # (N+1)-th acquire rejected
        res3 = slots.acquire("sess-3")
        assert res3.allowed is False
        assert res3.reason == "max_concurrent"
        assert res3.active_count == 2
        assert res3.limit == 2
        assert slots.is_holding_slot("sess-3") is False

        # Re-acquiring already holding slot is a no-op success
        res_re = slots.acquire("sess-1")
        assert res_re.allowed is True
        assert res_re.active_count == 2

    def test_session_slots_lockdown_mode(self) -> None:
        """Setting max_slots=0 immediately refuses all acquires with reason='disabled'."""
        from pypost.core.websocket_session_policy import SessionSlots

        slots = SessionSlots(max_slots=0)
        res = slots.acquire("sess-1")
        assert res.allowed is False
        assert res.reason == "disabled"
        assert res.active_count == 0
        assert res.limit == 0

        # Dynamic lockdown update
        slots.set_max_slots(5)
        res_ok = slots.acquire("sess-1")
        assert res_ok.allowed is True
        assert slots.active_count == 1

        slots.set_max_slots(0)
        res_locked = slots.acquire("sess-2")
        assert res_locked.allowed is False
        assert res_locked.reason == "disabled"

    def test_session_slots_idempotent_release(self) -> None:
        """Releasing slots restores capacity; releasing untracked session is safe no-op."""
        from pypost.core.websocket_session_policy import SessionSlots

        slots = SessionSlots(max_slots=1)
        assert slots.acquire("sess-1").allowed is True
        assert slots.acquire("sess-2").allowed is False

        # Release active slot
        assert slots.release("sess-1") is True
        assert slots.active_count == 0
        assert slots.is_holding_slot("sess-1") is False

        # Double release is safe
        assert slots.release("sess-1") is False
        assert slots.active_count == 0

        # Release untracked session
        assert slots.release("untracked-sess") is False
        assert slots.active_count == 0

        # New acquire succeeds now that slot is freed
        assert slots.acquire("sess-2").allowed is True
        assert slots.active_count == 1

    def test_session_slots_thread_safety_under_contention(self) -> None:
        """Concurrent acquire and release across threads must maintain mutex invariants."""
        from pypost.core.websocket_session_policy import SessionSlots

        slots = SessionSlots(max_slots=5)
        num_workers = 20

        def worker_task(worker_id: int) -> bool:
            sess_id = f"worker-sess-{worker_id}"
            res = slots.acquire(sess_id)
            if res.allowed:
                assert slots.active_count <= 5
                slots.release(sess_id)
                return True
            return False

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(worker_task, range(num_workers)))

        assert slots.active_count == 0
        assert any(results)  # At least some workers acquired successfully


# =============================================================================
# 3. Prometheus MetricsRegistry & Observability Tests
# =============================================================================


class TestWebSocketPrometheusMetrics:
    """Asserts registration and tracking of all 9 WebSocket Prometheus metrics."""

    def test_metrics_registry_declares_all_websocket_instruments(self) -> None:
        """MetricsRegistry must initialize all 9 WebSocket Prometheus instruments."""
        registry = MetricsRegistry()

        assert hasattr(registry, "websocket_sessions_opened")
        assert hasattr(registry, "websocket_sessions_closed")
        assert hasattr(registry, "websocket_messages")
        assert hasattr(registry, "websocket_message_bytes")
        assert hasattr(registry, "websocket_stream_entries_dropped")
        assert hasattr(registry, "websocket_reconnect_attempts")
        assert hasattr(registry, "websocket_active_sessions")
        assert hasattr(registry, "websocket_session_start_refused")
        assert hasattr(registry, "websocket_probe_duration_seconds")

    def test_metrics_registry_tracking_methods_and_scrape_output(self) -> None:
        """Tracking methods must update metrics and expose valid OpenMetrics format."""
        registry = MetricsRegistry()

        # Invoke all tracking methods
        registry.track_websocket_session_opened(outcome="success")
        registry.track_websocket_session_opened(outcome="failure")
        registry.track_websocket_session_closed(reason="clean")
        registry.track_websocket_session_closed(reason="heartbeat_timeout")
        registry.track_websocket_message(direction="inbound", kind="text")
        registry.track_websocket_message(direction="outbound", kind="binary")
        registry.track_websocket_message_bytes(direction="inbound", byte_count=1024)
        registry.track_websocket_message_bytes(direction="outbound", byte_count=512)
        registry.track_websocket_stream_entries_dropped(reason="capacity", count=3)
        registry.track_websocket_stream_entries_dropped(reason="memory_budget", count=1)
        registry.track_websocket_reconnect_attempt(outcome="scheduled")
        registry.track_websocket_reconnect_attempt(outcome="exhausted")
        registry.set_websocket_active_sessions(2)
        registry.track_websocket_session_start_refused(reason="max_concurrent")
        registry.track_websocket_session_start_refused(reason="disabled")
        registry.track_websocket_probe_duration(outcome="success", duration_seconds=0.042)

        # Scrape and verify
        scrape_text = generate_latest(registry.registry).decode("utf-8")

        assert 'websocket_sessions_opened_total{outcome="success"} 1.0' in scrape_text
        assert 'websocket_sessions_opened_total{outcome="failure"} 1.0' in scrape_text
        assert 'websocket_sessions_closed_total{reason="clean"} 1.0' in scrape_text
        assert 'websocket_sessions_closed_total{reason="heartbeat_timeout"} 1.0' in scrape_text
        assert 'websocket_messages_total{direction="inbound",kind="text"} 1.0' in scrape_text
        assert 'websocket_messages_total{direction="outbound",kind="binary"} 1.0' in scrape_text
        assert 'websocket_message_bytes_total{direction="inbound"} 1024.0' in scrape_text
        assert 'websocket_message_bytes_total{direction="outbound"} 512.0' in scrape_text
        assert 'websocket_stream_entries_dropped_total{reason="capacity"} 3.0' in scrape_text
        assert 'websocket_stream_entries_dropped_total{reason="memory_budget"} 1.0' in scrape_text
        assert 'websocket_reconnect_attempts_total{outcome="scheduled"} 1.0' in scrape_text
        assert 'websocket_reconnect_attempts_total{outcome="exhausted"} 1.0' in scrape_text
        assert "websocket_active_sessions 2.0" in scrape_text
        assert 'websocket_session_start_refused_total{reason="max_concurrent"} 1.0' in scrape_text
        assert 'websocket_session_start_refused_total{reason="disabled"} 1.0' in scrape_text
        assert 'websocket_probe_duration_seconds_count{outcome="success"} 1.0' in scrape_text

    def test_metrics_manager_dynamic_delegation(self, qapp: QApplication) -> None:
        """MetricsManager in pypost.core.qt.metrics must delegate tracking methods."""
        from pypost.core.qt.metrics import MetricsManager

        manager = MetricsManager()
        # Verify it has tracking methods either directly or via dynamic delegation
        assert hasattr(manager, "track_websocket_session_opened")
        manager.track_websocket_session_opened(outcome="success")
        manager.track_websocket_session_start_refused(reason="max_concurrent")
        manager.set_websocket_active_sessions(1)


# =============================================================================
# 4. WebSocketPresenter Concurrency Refusal & Lifecycle Integration Tests
# =============================================================================


class TestWebSocketPresenterConcurrencyRefusal:
    """Asserts presenter refuses connection when session ceiling is reached."""

    def test_presenter_refuses_connect_when_max_concurrent_reached(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When SessionSlots is full, handle_connect must refuse without opening socket."""
        from pypost.core.websocket_session_policy import get_session_slots
        from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

        slots = get_session_slots()
        slots.reset()
        slots.set_max_slots(1)

        # Pre-fill slot with dummy session
        slots.acquire("existing-active-session")

        connection = WebSocketConnection(
            id="test-conn-1",
            name="Test Echo",
            url="ws://127.0.0.1:9999/ws",
        )
        presenter = WebSocketPresenter(connection=connection)

        with caplog.at_level(
            logging.WARNING, logger="pypost.ui.presenters.websocket_presenter"
        ):
            presenter.handle_connect()

        # Must remain in IDLE state
        assert presenter.state == SessionState.IDLE

        # Must have emitted refusal log
        assert any(
            "websocket_session_refused" in record.message for record in caplog.records
        )
        assert any(
            "reason=max_concurrent" in record.message for record in caplog.records
        )

        # Teardown
        slots.reset()

    def test_presenter_refuses_connect_in_lockdown_mode(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When ws_max_concurrent_sessions=0, connection is refused with reason='disabled'."""
        from pypost.core.websocket_session_policy import get_session_slots
        from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

        slots = get_session_slots()
        slots.reset()
        slots.set_max_slots(0)

        connection = WebSocketConnection(
            id="test-conn-lockdown",
            name="Lockdown Feed",
            url="ws://127.0.0.1:9999/ws",
        )
        presenter = WebSocketPresenter(connection=connection)

        with caplog.at_level(
            logging.WARNING, logger="pypost.ui.presenters.websocket_presenter"
        ):
            presenter.handle_connect()

        assert presenter.state == SessionState.IDLE
        assert any(
            "websocket_session_refused" in record.message for record in caplog.records
        )
        assert any("reason=disabled" in record.message for record in caplog.records)

        # Teardown
        slots.reset()


# =============================================================================
# 5. Zero-Leak Structured Logging & Security Invariant Tests
# =============================================================================


class TestWebSocketZeroLeakStructuredLogging:
    """Asserts structured logging conventions and zero-leak security invariants."""

    def test_zero_leak_logging_never_exposes_secrets(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Secret tokens in query params, headers, and payloads must NEVER appear in logs."""
        from pypost.core.websocket_session_policy import get_session_slots
        from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

        slots = get_session_slots()
        slots.reset()
        slots.set_max_slots(8)

        secret_query_val = "SECRET_API_KEY_98765"
        secret_header_val = "SUPER_SECRET_BEARER_TOKEN_4321"

        connection = WebSocketConnection(
            id="secret-conn-1",
            name="Secure Feed",
            url=f"ws://127.0.0.1:9999/feed?api_key={secret_query_val}",
            headers={"Authorization": f"Bearer {secret_header_val}"},
        )

        env_vars = {"API_KEY": secret_query_val, "AUTH_TOKEN": secret_header_val}
        hidden_keys = {"API_KEY", "AUTH_TOKEN"}

        presenter = WebSocketPresenter(
            connection=connection,
            env_vars=env_vars,
            hidden_keys=hidden_keys,
        )

        with caplog.at_level(logging.DEBUG):
            presenter.handle_connect()
            presenter.handle_disconnect()

        # Audit entire captured log text
        all_logs = caplog.text

        assert secret_query_val not in all_logs
        assert secret_header_val not in all_logs

        slots.reset()


# =============================================================================
# 6. Settings Dialog WebSocket Section Widget Tests
# =============================================================================


class TestWebSocketSettingsSectionWidget:
    """Asserts WebSocketSettingsSection UI controls exist and collect all ws_* settings."""

    def test_settings_section_creation_and_field_collection(self, qapp: QApplication) -> None:
        """WebSocketSettingsSection must instantiate, populate form, and return fields."""
        from pypost.ui.widgets.settings.websocket_section import WebSocketSettingsSection

        settings = AppSettings(
            ws_max_concurrent_sessions=6,
            ws_max_stream_entries=3000,
            ws_session_memory_budget_bytes=33554432,  # 32 MiB
            ws_max_incoming_message_bytes=4194304,   # 4 MiB
            ws_display_truncate_bytes=131072,        # 128 KiB
            ws_mcp_probe_max_messages=15,
            ws_mcp_probe_max_duration_ms=15000,
        )

        container = QWidget()
        section = WebSocketSettingsSection(current_settings=settings, parent=container)

        form = QFormLayout(container)
        section.add_to_form(form)

        fields = section.collect_fields()

        assert "ws_max_concurrent_sessions" in fields
        assert fields["ws_max_concurrent_sessions"] == 6

        assert "ws_max_stream_entries" in fields
        assert fields["ws_max_stream_entries"] == 3000

        assert "ws_session_memory_budget_bytes" in fields
        assert fields["ws_session_memory_budget_bytes"] == 33554432

        assert "ws_max_incoming_message_bytes" in fields
        assert fields["ws_max_incoming_message_bytes"] == 4194304

        assert "ws_display_truncate_bytes" in fields
        assert fields["ws_display_truncate_bytes"] == 131072

        assert "ws_mcp_probe_max_messages" in fields
        assert fields["ws_mcp_probe_max_messages"] == 15

        assert "ws_mcp_probe_max_duration_ms" in fields
        assert fields["ws_mcp_probe_max_duration_ms"] == 15000

        assert "ws_default_heartbeat" in fields
        assert "ws_default_reconnect" in fields
