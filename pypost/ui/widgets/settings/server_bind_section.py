"""MCP and metrics server bind settings section."""

from __future__ import annotations


import logging
from typing import Any

from PySide6.QtWidgets import QFormLayout, QLineEdit, QSpinBox, QWidget

from pypost.core.bind_address_validation import (
    BindAddressValidationFailure,
    validate_bind_host,
    validate_bind_port,
)
from pypost.models.settings import AppSettings

logger = logging.getLogger("pypost.ui.dialogs.settings_dialog")


class ServerBindSettingsSection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        self.mcp_port_spin = QSpinBox(parent)
        self.mcp_port_spin.setRange(1024, 65535)
        self.mcp_port_spin.setValue(current_settings.mcp_port)

        self.mcp_host_edit = QLineEdit(parent)
        self.mcp_host_edit.setText(current_settings.mcp_host)

        self.metrics_port_spin = QSpinBox(parent)
        self.metrics_port_spin.setRange(1024, 65535)
        self.metrics_port_spin.setValue(current_settings.metrics_port)

        self.metrics_host_edit = QLineEdit(parent)
        self.metrics_host_edit.setText(current_settings.metrics_host)

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow("MCP Server Port:", self.mcp_port_spin)
        form.addRow("MCP Server Host:", self.mcp_host_edit)
        form.addRow("Metrics Server Port:", self.metrics_port_spin)
        form.addRow("Metrics Server Host:", self.metrics_host_edit)

    def validate(self, parent: QWidget) -> tuple[str, int, str, int] | None:
        mcp_host = validate_bind_host(
            self.mcp_host_edit.text(),
            field_label="MCP Server Host",
        )
        if isinstance(mcp_host, BindAddressValidationFailure):
            self._show_validation_failure(parent, mcp_host)
            return None
        mcp_port = validate_bind_port(
            self.mcp_port_spin.value(),
            field_label="MCP Server Port",
        )
        if isinstance(mcp_port, BindAddressValidationFailure):
            self._show_validation_failure(parent, mcp_port)
            return None
        metrics_host = validate_bind_host(
            self.metrics_host_edit.text(),
            field_label="Metrics Server Host",
        )
        if isinstance(metrics_host, BindAddressValidationFailure):
            self._show_validation_failure(parent, metrics_host)
            return None
        metrics_port = validate_bind_port(
            self.metrics_port_spin.value(),
            field_label="Metrics Server Port",
        )
        if isinstance(metrics_port, BindAddressValidationFailure):
            self._show_validation_failure(parent, metrics_port)
            return None
        return mcp_host, mcp_port, metrics_host, metrics_port

    def collect_fields(self) -> dict[str, Any]:
        return {
            "mcp_port": self.mcp_port_spin.value(),
            "mcp_host": self.mcp_host_edit.text(),
            "metrics_port": self.metrics_port_spin.value(),
            "metrics_host": self.metrics_host_edit.text(),
        }

    def collect_validated_fields(
        self,
        bind_values: tuple[str, int, str, int],
    ) -> dict[str, Any]:
        mcp_host, mcp_port, metrics_host, metrics_port = bind_values
        return {
            "mcp_host": mcp_host,
            "mcp_port": mcp_port,
            "metrics_host": metrics_host,
            "metrics_port": metrics_port,
        }

    @staticmethod
    def _show_validation_failure(
        parent: QWidget,
        failure: BindAddressValidationFailure,
    ) -> None:
        logger.warning(
            "bind_address_settings_validation_failed field=%s reason=%s",
            failure.field,
            failure.reason,
        )
        from pypost.ui.dialogs.settings_dialog import show_invalid_bind_address

        show_invalid_bind_address(parent, failure.message)
