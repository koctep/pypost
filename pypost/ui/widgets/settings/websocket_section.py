"""WebSocket settings section (bounds, session ceiling, heartbeat, reconnect, probe)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QFormLayout, QSpinBox, QWidget

from pypost.models.settings import AppSettings
from pypost.models.websocket import HeartbeatPolicy, ReconnectPolicy
from pypost.ui.widgets.settings._common import make_section_header


class WebSocketSettingsSection:
    """Settings dialog section for global WebSocket limits and defaults."""

    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.max_concurrent_spin = QSpinBox(parent)
        self.max_concurrent_spin.setRange(0, 100)
        self.max_concurrent_spin.setValue(current_settings.ws_max_concurrent_sessions)

        self.max_stream_entries_spin = QSpinBox(parent)
        self.max_stream_entries_spin.setRange(100, 1_000_000)
        self.max_stream_entries_spin.setValue(current_settings.ws_max_stream_entries)

        self.session_memory_budget_spin = QSpinBox(parent)
        self.session_memory_budget_spin.setRange(1024 * 1024, 2_147_483_647)
        self.session_memory_budget_spin.setSingleStep(1024 * 1024)
        self.session_memory_budget_spin.setValue(
            current_settings.ws_session_memory_budget_bytes
        )

        self.max_incoming_spin = QSpinBox(parent)
        self.max_incoming_spin.setRange(1024, 2_147_483_647)
        self.max_incoming_spin.setSingleStep(1024 * 1024)
        self.max_incoming_spin.setValue(
            current_settings.ws_max_incoming_message_bytes
        )

        self.display_truncate_spin = QSpinBox(parent)
        self.display_truncate_spin.setRange(1024, 2_147_483_647)
        self.display_truncate_spin.setSingleStep(1024)
        self.display_truncate_spin.setValue(
            current_settings.ws_display_truncate_bytes
        )

        self.probe_max_messages_spin = QSpinBox(parent)
        self.probe_max_messages_spin.setRange(1, 1000)
        self.probe_max_messages_spin.setValue(
            current_settings.ws_mcp_probe_max_messages
        )

        self.probe_max_duration_spin = QSpinBox(parent)
        self.probe_max_duration_spin.setRange(100, 600_000)
        self.probe_max_duration_spin.setSingleStep(1000)
        self.probe_max_duration_spin.setValue(
            current_settings.ws_mcp_probe_max_duration_ms
        )

        self.default_heartbeat: HeartbeatPolicy = current_settings.ws_default_heartbeat
        self.default_reconnect: ReconnectPolicy = current_settings.ws_default_reconnect

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow(make_section_header("WebSocket Configuration"))
        form.addRow(
            "Max Concurrent Sessions (0 = disabled):",
            self.max_concurrent_spin,
        )
        form.addRow("Max Stream Entries:", self.max_stream_entries_spin)
        form.addRow(
            "Session Memory Budget (bytes):",
            self.session_memory_budget_spin,
        )
        form.addRow(
            "Max Incoming Message Size (bytes):",
            self.max_incoming_spin,
        )
        form.addRow(
            "Display Truncate Threshold (bytes):",
            self.display_truncate_spin,
        )
        form.addRow(
            "MCP Probe Max Messages:",
            self.probe_max_messages_spin,
        )
        form.addRow(
            "MCP Probe Max Duration (ms):",
            self.probe_max_duration_spin,
        )

    def collect_fields(self) -> dict[str, Any]:
        return {
            "ws_max_concurrent_sessions": self.max_concurrent_spin.value(),
            "ws_max_stream_entries": self.max_stream_entries_spin.value(),
            "ws_session_memory_budget_bytes": self.session_memory_budget_spin.value(),
            "ws_max_incoming_message_bytes": self.max_incoming_spin.value(),
            "ws_display_truncate_bytes": self.display_truncate_spin.value(),
            "ws_mcp_probe_max_messages": self.probe_max_messages_spin.value(),
            "ws_mcp_probe_max_duration_ms": self.probe_max_duration_spin.value(),
            "ws_default_heartbeat": self.default_heartbeat,
            "ws_default_reconnect": self.default_reconnect,
        }
