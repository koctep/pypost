"""Schema-guided argument form, JSON fallback, and Invoke control."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.mcp_client_arg_schema import (
    ArgFieldSpec,
    ArgSchemaKind,
    ArgValidationError,
    classify_arg_schema,
    list_arg_fields,
)
from pypost.models.mcp_client import McpRemoteTool
from pypost.ui.widget_ids import (
    MCP_CLIENT_ARG_FORM,
    MCP_CLIENT_ARG_JSON,
    MCP_CLIENT_INVOKE_BUTTON,
    set_widget_id,
)

__all__ = ["McpClientToolInvokeForm"]


class McpClientToolInvokeForm(QWidget):
    """Argument inputs for the selected remote tool plus Invoke."""

    invoke_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._kind = ArgSchemaKind.JSON_ONLY
        self._fields: dict[str, tuple[ArgFieldSpec, QWidget]] = {}
        self._has_tool = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._hint = QLabel("", self)
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

        self._form = QWidget(self)
        set_widget_id(self._form, MCP_CLIENT_ARG_FORM)
        self._form_layout = QFormLayout(self._form)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._form)

        self._use_json = QCheckBox("Use JSON", self)
        layout.addWidget(self._use_json)

        self._json = QPlainTextEdit(self)
        self._json.setPlaceholderText("{}")
        set_widget_id(self._json, MCP_CLIENT_ARG_JSON)
        layout.addWidget(self._json)

        button_row = QHBoxLayout()
        self._invoke_btn = QPushButton("Invoke", self)
        set_widget_id(self._invoke_btn, MCP_CLIENT_INVOKE_BUTTON)
        self._invoke_btn.clicked.connect(self.invoke_clicked.emit)
        button_row.addWidget(self._invoke_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self._use_json.toggled.connect(self._sync_mode_widgets)
        self.bind_tool(None)

    def bind_tool(self, tool: McpRemoteTool | None) -> None:
        """Replace argument widgets for the selected catalog entry."""
        self._clear_fields()
        self._has_tool = tool is not None
        if tool is None:
            self._kind = ArgSchemaKind.JSON_ONLY
            self._hint.setText("Select a remote tool to invoke.")
            self._json.setPlainText("{}")
            self._use_json.setChecked(False)
            self._use_json.setVisible(False)
            self._form.setVisible(False)
            self._json.setVisible(False)
            self._invoke_btn.setEnabled(False)
            return
        self._kind = classify_arg_schema(tool.input_schema)
        self._invoke_btn.setEnabled(True)
        if self._kind == ArgSchemaKind.NO_ARGS:
            self._hint.setText("This tool takes no arguments.")
            self._form.setVisible(False)
            self._use_json.setVisible(False)
            self._use_json.setChecked(False)
            self._json.setPlainText("{}")
            self._json.setVisible(False)
            return
        if self._kind == ArgSchemaKind.JSON_ONLY:
            self._hint.setText("Arguments (JSON object)")
            self._form.setVisible(False)
            self._use_json.setVisible(False)
            self._use_json.setChecked(True)
            self._json.setPlainText("{}")
            self._json.setVisible(True)
            return
        self._hint.setText("Arguments")
        self._form.setVisible(True)
        self._use_json.setVisible(True)
        self._use_json.setChecked(False)
        self._json.setPlainText("{}")
        for spec in list_arg_fields(tool.input_schema):
            editor = self._make_editor(spec)
            label = spec.name + (" *" if spec.required else "")
            self._form_layout.addRow(label, editor)
            self._fields[spec.name] = (spec, editor)
        self._sync_mode_widgets()

    def set_invoke_enabled(self, enabled: bool) -> None:
        """Enable Invoke when connected, idle, and a tool is selected."""
        self._invoke_btn.setEnabled(bool(enabled) and self._has_tool)

    def collect_arguments(self) -> dict[str, Any]:
        """Return a JSON object payload or raise ArgValidationError."""
        if self._kind == ArgSchemaKind.NO_ARGS:
            return {}
        if self._kind == ArgSchemaKind.JSON_ONLY or self._use_json.isChecked():
            return self._collect_json()
        return self._collect_form()

    def apply_arguments(self, arguments: dict[str, Any]) -> None:
        """Pre-fill argument editors (legacy MCP migration or saved state)."""
        if not self._has_tool:
            return
        if self._kind == ArgSchemaKind.NO_ARGS:
            return
        if self._kind == ArgSchemaKind.JSON_ONLY or self._use_json.isChecked():
            self._json.setPlainText(json.dumps(arguments, indent=2))
            return
        for name, (spec, editor) in self._fields.items():
            if name not in arguments:
                continue
            value = arguments[name]
            if isinstance(editor, QLineEdit):
                editor.setText("" if value is None else str(value))
            elif isinstance(editor, QCheckBox):
                editor.setChecked(bool(value))
            elif isinstance(editor, QComboBox):
                editor.setCurrentText("" if value is None else str(value))

    def _sync_mode_widgets(self) -> None:
        if self._kind != ArgSchemaKind.SIMPLE_FORM:
            return
        json_mode = self._use_json.isChecked()
        self._form.setVisible(not json_mode)
        self._json.setVisible(json_mode)

    def _clear_fields(self) -> None:
        while self._form_layout.rowCount():
            self._form_layout.removeRow(0)
        self._fields.clear()

    def _make_editor(self, spec: ArgFieldSpec) -> QWidget:
        if spec.json_type == "boolean":
            return QCheckBox(self._form)
        if spec.enum_values:
            combo = QComboBox(self._form)
            if not spec.required:
                combo.addItem("", "")
            for value in spec.enum_values:
                combo.addItem(value, value)
            return combo
        return QLineEdit(self._form)

    def _collect_form(self) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        for name, (spec, editor) in self._fields.items():
            value = self._editor_value(spec, editor)
            if value is _MISSING:
                if spec.required:
                    raise ArgValidationError(
                        f"Required field {name!r} is empty.",
                    )
                continue
            payload[name] = value
        return payload

    def _collect_json(self) -> dict[str, Any]:
        text = self._json.toPlainText().strip()
        if not text:
            raise ArgValidationError("Arguments must be a JSON object.")
        try:
            parsed: object = json.loads(text)
        except json.JSONDecodeError as err:
            raise ArgValidationError("Arguments must be a JSON object.") from err
        if not isinstance(parsed, dict):
            raise ArgValidationError("Arguments must be a JSON object.")
        return parsed

    def _editor_value(self, spec: ArgFieldSpec, editor: QWidget) -> object:
        if isinstance(editor, QCheckBox):
            return editor.isChecked()
        if isinstance(editor, QComboBox):
            text = str(editor.currentData() or editor.currentText() or "")
            if not text:
                return _MISSING
            return text
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if not text:
                return _MISSING
            return _parse_scalar(spec, text)
        return _MISSING


_MISSING = object()


def _parse_scalar(spec: ArgFieldSpec, text: str) -> object:
    if spec.json_type == "integer":
        try:
            return int(text)
        except ValueError as err:
            raise ArgValidationError(
                f"Field {spec.name!r} must be an integer.",
            ) from err
    if spec.json_type == "number":
        try:
            return float(text)
        except ValueError as err:
            raise ArgValidationError(
                f"Field {spec.name!r} must be a number.",
            ) from err
    return text
