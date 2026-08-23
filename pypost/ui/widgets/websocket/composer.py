"""Multi-format WebSocket message composer widget (PYPOST-1134 / WS-6).

Provides payload editing across Text, JSON, Hex, and Base64 formats with
real-time syntax validation, quick preset/sequence controls, and dispatch actions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from pypost.core.websocket_codec import encode_payload, validate_format
from pypost.core.websocket_session_policy import SessionState
from pypost.models.websocket import (
    WebSocketMessagePreset,
    WsMessageFormat,
)
from pypost.ui.widget_ids import (
    WS_COMPOSER_EDIT,
    WS_COMPOSER_FORMAT_COMBO,
    WS_PRESET_COMBO,
    WS_PRESET_SAVE_BUTTON,
    WS_SEND_MESSAGE_BUTTON,
    WS_SEQUENCE_COMBO,
    WS_SEQUENCE_RUN_BUTTON,
    WS_SEQUENCE_STOP_BUTTON,
    set_widget_id,
)

if TYPE_CHECKING:
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

logger = logging.getLogger(__name__)

__all__ = ["WebSocketComposer"]


class WebSocketComposer(QWidget):
    """Interactive multi-format composer for outgoing WebSocket frames."""

    def __init__(
        self,
        presenter: Optional[WebSocketPresenter] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.presenter: Optional[WebSocketPresenter] = presenter
        self._current_format: WsMessageFormat = WsMessageFormat.TEXT
        self._validation_error: Optional[str] = None
        self._is_valid: bool = True

        self._init_ui()
        self._sync_presets_and_sequences()
        self._revalidate()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Top control bar: Format, Presets, Sequences
        control_bar = QHBoxLayout()
        control_bar.setSpacing(8)

        # Format selector
        fmt_label = QLabel("Format:", self)
        control_bar.addWidget(fmt_label)

        self.format_combo = QComboBox(self)
        set_widget_id(self.format_combo, WS_COMPOSER_FORMAT_COMBO)
        self.format_combo.addItem("Text", WsMessageFormat.TEXT)
        self.format_combo.addItem("JSON", WsMessageFormat.JSON)
        self.format_combo.addItem("Hex", WsMessageFormat.HEX)
        self.format_combo.addItem("Base64", WsMessageFormat.BASE64)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        control_bar.addWidget(self.format_combo)

        # Separator / Spacing
        control_bar.addSpacing(8)

        # Preset selector & Save button
        preset_label = QLabel("Preset:", self)
        control_bar.addWidget(preset_label)

        self.preset_combo = QComboBox(self)
        set_widget_id(self.preset_combo, WS_PRESET_COMBO)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        control_bar.addWidget(self.preset_combo)

        self.save_preset_btn = QPushButton("Save...", self)
        set_widget_id(self.save_preset_btn, WS_PRESET_SAVE_BUTTON)
        self.save_preset_btn.clicked.connect(self._on_save_preset_clicked)
        control_bar.addWidget(self.save_preset_btn)

        control_bar.addSpacing(8)

        # Sequence selector & Run / Stop buttons
        seq_label = QLabel("Sequence:", self)
        control_bar.addWidget(seq_label)

        self.seq_combo = QComboBox(self)
        set_widget_id(self.seq_combo, WS_SEQUENCE_COMBO)
        control_bar.addWidget(self.seq_combo)

        self.run_seq_btn = QPushButton("Run", self)
        set_widget_id(self.run_seq_btn, WS_SEQUENCE_RUN_BUTTON)
        self.run_seq_btn.clicked.connect(self._on_run_sequence_clicked)
        control_bar.addWidget(self.run_seq_btn)

        self.stop_seq_btn = QPushButton("Stop", self)
        set_widget_id(self.stop_seq_btn, WS_SEQUENCE_STOP_BUTTON)
        self.stop_seq_btn.clicked.connect(self._on_stop_sequence_clicked)
        control_bar.addWidget(self.stop_seq_btn)

        control_bar.addStretch()
        layout.addLayout(control_bar)

        # Payload editor
        self.payload_edit = QTextEdit(self)
        set_widget_id(self.payload_edit, WS_COMPOSER_EDIT)
        self.payload_edit.setPlaceholderText("Enter message payload...")
        self.payload_edit.textChanged.connect(self._revalidate)
        layout.addWidget(self.payload_edit)

        # Bottom status and send bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(8)

        self.validation_label = QLabel(self)
        bottom_bar.addWidget(self.validation_label)
        bottom_bar.addStretch()

        self.send_btn = QPushButton("Send Message", self)
        set_widget_id(self.send_btn, WS_SEND_MESSAGE_BUTTON)
        self.send_btn.clicked.connect(self._on_send_clicked)
        bottom_bar.addWidget(self.send_btn)

        layout.addLayout(bottom_bar)

    def _on_send_clicked(self) -> None:
        if self.presenter is not None and hasattr(self.presenter, "handle_send_message"):
            self.presenter.handle_send_message()
        else:
            self.send_current_payload()

    def set_format(self, format: WsMessageFormat | str) -> None:
        """Set the active message composition format."""
        fmt = WsMessageFormat(format) if isinstance(format, str) else format
        self._current_format = fmt
        for i in range(self.format_combo.count()):
            if self.format_combo.itemData(i) == fmt:
                self.format_combo.blockSignals(True)
                self.format_combo.setCurrentIndex(i)
                self.format_combo.blockSignals(False)
                break
        self._revalidate()

    def get_format(self) -> WsMessageFormat:
        """Return the active message composition format."""
        return self._current_format

    def set_payload(self, payload: str) -> None:
        """Set the payload text in the editor."""
        self.payload_edit.setPlainText(payload)

    def get_payload(self) -> str:
        """Get the payload text from the editor."""
        return self.payload_edit.toPlainText()

    def is_payload_valid(self) -> bool:
        """Return True if the current payload is syntactically valid for the format."""
        return self._is_valid

    def get_validation_error(self) -> Optional[str]:
        """Return format validation error message if invalid, or None."""
        return self._validation_error

    def _on_format_changed(self, index: int) -> None:
        fmt = self.format_combo.itemData(index)
        if fmt is not None:
            self._current_format = fmt
            self._revalidate()

    def _revalidate(self) -> None:
        payload = self.payload_edit.toPlainText()
        is_valid, err = validate_format(payload, self._current_format)
        self._is_valid = is_valid
        self._validation_error = err

        if is_valid:
            self.validation_label.setText(f"✓ Valid {self._current_format.value.upper()}")
            self.validation_label.setStyleSheet("color: #4CAF50;")
        else:
            logger.warning(
                "composer_format_validation_failed format=%s error=%s",
                self._current_format.value,
                err,
            )
            self.validation_label.setText(f"⚠ {err}")
            self.validation_label.setStyleSheet("color: #F44336;")

    def _sync_presets_and_sequences(self) -> None:
        """Populate preset and sequence dropdowns from presenter connection."""
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Select Preset --", None)

        self.seq_combo.blockSignals(True)
        self.seq_combo.clear()
        self.seq_combo.addItem("-- Select Sequence --", None)

        if self.presenter and getattr(self.presenter, "connection", None):
            conn = self.presenter.connection
            for p in conn.presets:
                self.preset_combo.addItem(f"{p.name} ({p.format.value})", p.id)
            for s in conn.sequences:
                self.seq_combo.addItem(f"{s.name} ({len(s.steps)} steps)", s.id)

        self.preset_combo.blockSignals(False)
        self.seq_combo.blockSignals(False)

    def _on_preset_selected(self, index: int) -> None:
        preset_id = self.preset_combo.itemData(index)
        if not preset_id or not self.presenter or not getattr(self.presenter, "connection", None):
            return
        preset = next((p for p in self.presenter.connection.presets if p.id == preset_id), None)
        if preset:
            self.set_format(preset.format)
            self.set_payload(preset.payload)

    def _on_save_preset_clicked(self) -> None:
        if not self.presenter or not getattr(self.presenter, "connection", None):
            return
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset Name:")
        if ok and name.strip():
            preset = WebSocketMessagePreset(
                name=name.strip(),
                format=self.get_format(),
                payload=self.get_payload(),
            )
            self.presenter.connection.presets.append(preset)
            logger.info(
                "composer_preset_saved name=%s format=%s bytes=%d",
                preset.name,
                preset.format.value,
                len(preset.payload.encode("utf-8")),
            )
            self._sync_presets_and_sequences()
            # Select the new preset
            idx = self.preset_combo.findData(preset.id)
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
            self.presenter.connection_saved.emit(self.presenter.connection)

    def _on_run_sequence_clicked(self) -> None:
        seq_id = self.seq_combo.currentData()
        if seq_id and self.presenter:
            logger.info("composer_sequence_run_clicked seq_id=%s", seq_id)
            if hasattr(self.presenter, "run_sequence"):
                self.presenter.run_sequence(seq_id)

    def _on_stop_sequence_clicked(self) -> None:
        logger.info("composer_sequence_stop_clicked")
        if self.presenter and hasattr(self.presenter, "stop_sequence"):
            self.presenter.stop_sequence()

    def send_current_payload(self) -> bool:
        """Transmit current composer payload over the active connection."""
        if self.presenter is not None:
            # Check state
            state = getattr(
                self.presenter, "state", getattr(self.presenter, "_current_state", None)
            )
            if state != SessionState.OPEN:
                logger.warning("composer_send_blocked_not_open state=%s", state)
                return False

        if not self.is_payload_valid():
            logger.warning(
                "composer_send_blocked_invalid_format format=%s error=%s",
                self._current_format.value,
                self.get_validation_error(),
            )
            return False

        payload = self.get_payload()
        try:
            encoded = encode_payload(payload, self._current_format)
        except Exception as exc:
            logger.error(
                "composer_encode_failed format=%s error=%s",
                self._current_format.value,
                exc,
            )
            return False

        byte_size = len(encoded) if isinstance(encoded, bytes) else len(encoded.encode("utf-8"))
        if self.presenter is not None:
            controller = getattr(self.presenter, "_controller", None) or getattr(
                self.presenter, "session_controller", None
            )
            if controller is not None:
                if isinstance(encoded, bytes):
                    controller.send_binary(encoded)
                else:
                    controller.send_text(encoded)
                logger.info(
                    "composer_payload_dispatched format=%s bytes=%d is_binary=%s",
                    self._current_format.value,
                    byte_size,
                    isinstance(encoded, bytes),
                )
                return True

        logger.info(
            "composer_payload_dispatched format=%s bytes=%d is_binary=%s",
            self._current_format.value,
            byte_size,
            isinstance(encoded, bytes),
        )
        return True
