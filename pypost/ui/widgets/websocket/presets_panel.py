"""Messages sub-tab hosting Saved Messages (Presets) and Sequences management (PYPOST-1134 / WS-6).

Provides full master/detail CRUD, reordering, direct transmission ("Send now"),
loading into composer, and sequence execution controls.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
import uuid

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pypost.core.websocket_codec import encode_payload, validate_format
from pypost.core.websocket_session_policy import SessionState
from pypost.models.websocket import (
    WebSocketConnection,
    WebSocketMessagePreset,
    WebSocketSequence,
    WebSocketSequenceStep,
    WsMessageFormat,
)
from pypost.ui.widget_ids import (
    WS_MESSAGES_TAB,
    WS_PRESET_DELETE_BUTTON,
    WS_PRESET_DUPLICATE_BUTTON,
    WS_PRESET_FORMAT_COMBO,
    WS_PRESET_LOAD_BUTTON,
    WS_PRESET_NAME_INPUT,
    WS_PRESET_NEW_BUTTON,
    WS_PRESET_PAYLOAD_EDIT,
    WS_PRESET_SEND_BUTTON,
    WS_PRESETS_LIST,
    WS_SEQUENCE_DELETE_BUTTON,
    WS_SEQUENCE_DUPLICATE_BUTTON,
    WS_SEQUENCE_NEW_BUTTON,
    WS_SEQUENCE_STEP_ADD_BUTTON,
    WS_SEQUENCE_STEP_DOWN_BUTTON,
    WS_SEQUENCE_STEP_REMOVE_BUTTON,
    WS_SEQUENCE_STEP_UP_BUTTON,
    WS_SEQUENCE_STEPS_TABLE,
    WS_SEQUENCES_LIST,
    set_widget_id,
)

if TYPE_CHECKING:
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.composer import WebSocketComposer

logger = logging.getLogger(__name__)

__all__ = ["WebSocketPresetsPanel"]


class WebSocketPresetsPanel(QWidget):
    """Messages panel in detail tabs hosting Presets and Sequences master/detail panes."""

    def __init__(
        self,
        presenter: Optional[WebSocketPresenter] = None,
        composer: Optional[WebSocketComposer] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        set_widget_id(self, WS_MESSAGES_TAB)
        self.presenter: Optional[WebSocketPresenter] = presenter
        self.composer: Optional[WebSocketComposer] = composer
        self._selected_preset_id: Optional[str] = None
        self._selected_sequence_id: Optional[str] = None

        self._init_ui()
        self.refresh_all()

    @property
    def connection(self) -> Optional[WebSocketConnection]:
        if self.presenter is not None:
            return getattr(self.presenter, "connection", None)
        return None

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        v_splitter = QSplitter(Qt.Orientation.Vertical, self)

        # ---------------------------------------------------------------------
        # Top Panel: Presets (Saved Messages)
        # ---------------------------------------------------------------------
        presets_box = QWidget(v_splitter)
        presets_layout = QVBoxLayout(presets_box)
        presets_layout.setContentsMargins(0, 0, 0, 0)
        presets_layout.setSpacing(4)

        presets_header = QLabel("<b>Saved Messages (Presets)</b>", presets_box)
        presets_layout.addWidget(presets_header)

        h_presets_splitter = QSplitter(Qt.Orientation.Horizontal, presets_box)

        # Master list & CRUD buttons
        presets_left = QWidget(h_presets_splitter)
        presets_left_layout = QVBoxLayout(presets_left)
        presets_left_layout.setContentsMargins(0, 0, 0, 0)
        presets_left_layout.setSpacing(4)

        self.presets_list = QListWidget(presets_left)
        set_widget_id(self.presets_list, WS_PRESETS_LIST)
        self.presets_list.currentRowChanged.connect(self._on_preset_row_changed)
        presets_left_layout.addWidget(self.presets_list)

        presets_btn_row = QHBoxLayout()
        self.preset_new_btn = QPushButton("New", presets_left)
        set_widget_id(self.preset_new_btn, WS_PRESET_NEW_BUTTON)
        self.preset_new_btn.clicked.connect(lambda: self.create_new_preset())
        presets_btn_row.addWidget(self.preset_new_btn)

        self.preset_dup_btn = QPushButton("Duplicate", presets_left)
        set_widget_id(self.preset_dup_btn, WS_PRESET_DUPLICATE_BUTTON)
        self.preset_dup_btn.clicked.connect(self._on_preset_duplicate_clicked)
        presets_btn_row.addWidget(self.preset_dup_btn)

        self.preset_del_btn = QPushButton("Delete", presets_left)
        set_widget_id(self.preset_del_btn, WS_PRESET_DELETE_BUTTON)
        self.preset_del_btn.clicked.connect(self._on_preset_delete_clicked)
        presets_btn_row.addWidget(self.preset_del_btn)
        presets_left_layout.addLayout(presets_btn_row)

        h_presets_splitter.addWidget(presets_left)

        # Presets Detail Pane
        presets_right = QWidget(h_presets_splitter)
        presets_right_layout = QVBoxLayout(presets_right)
        presets_right_layout.setContentsMargins(0, 0, 0, 0)
        presets_right_layout.setSpacing(4)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Name:", presets_right))
        self.preset_name_input = QLineEdit(presets_right)
        set_widget_id(self.preset_name_input, WS_PRESET_NAME_INPUT)
        self.preset_name_input.textChanged.connect(self._on_preset_detail_changed)
        name_row.addWidget(self.preset_name_input)

        name_row.addWidget(QLabel("Format:", presets_right))
        self.preset_format_combo = QComboBox(presets_right)
        set_widget_id(self.preset_format_combo, WS_PRESET_FORMAT_COMBO)
        self.preset_format_combo.addItem("Text", WsMessageFormat.TEXT)
        self.preset_format_combo.addItem("JSON", WsMessageFormat.JSON)
        self.preset_format_combo.addItem("Hex", WsMessageFormat.HEX)
        self.preset_format_combo.addItem("Base64", WsMessageFormat.BASE64)
        self.preset_format_combo.currentIndexChanged.connect(self._on_preset_detail_changed)
        name_row.addWidget(self.preset_format_combo)
        presets_right_layout.addLayout(name_row)

        self.preset_payload_edit = QPlainTextEdit(presets_right)
        set_widget_id(self.preset_payload_edit, WS_PRESET_PAYLOAD_EDIT)
        self.preset_payload_edit.setPlaceholderText("Preset payload template...")
        self.preset_payload_edit.textChanged.connect(self._on_preset_detail_changed)
        presets_right_layout.addWidget(self.preset_payload_edit)

        presets_action_row = QHBoxLayout()
        presets_action_row.addStretch()

        self.preset_load_btn = QPushButton("Load into composer", presets_right)
        set_widget_id(self.preset_load_btn, WS_PRESET_LOAD_BUTTON)
        self.preset_load_btn.clicked.connect(self._on_preset_load_clicked)
        presets_action_row.addWidget(self.preset_load_btn)

        self.preset_send_btn = QPushButton("Send now", presets_right)
        set_widget_id(self.preset_send_btn, WS_PRESET_SEND_BUTTON)
        self.preset_send_btn.clicked.connect(self._on_preset_send_clicked)
        presets_action_row.addWidget(self.preset_send_btn)

        presets_right_layout.addLayout(presets_action_row)
        h_presets_splitter.addWidget(presets_right)

        h_presets_splitter.setSizes([180, 320])
        presets_layout.addWidget(h_presets_splitter)
        v_splitter.addWidget(presets_box)

        # ---------------------------------------------------------------------
        # Bottom Panel: Sequences
        # ---------------------------------------------------------------------
        seq_box = QWidget(v_splitter)
        seq_layout = QVBoxLayout(seq_box)
        seq_layout.setContentsMargins(0, 0, 0, 0)
        seq_layout.setSpacing(4)

        seq_header = QLabel("<b>Message Sequences</b>", seq_box)
        seq_layout.addWidget(seq_header)

        h_seq_splitter = QSplitter(Qt.Orientation.Horizontal, seq_box)

        # Sequence Master list & CRUD buttons
        seq_left = QWidget(h_seq_splitter)
        seq_left_layout = QVBoxLayout(seq_left)
        seq_left_layout.setContentsMargins(0, 0, 0, 0)
        seq_left_layout.setSpacing(4)

        self.sequences_list = QListWidget(seq_left)
        set_widget_id(self.sequences_list, WS_SEQUENCES_LIST)
        self.sequences_list.currentRowChanged.connect(self._on_sequence_row_changed)
        seq_left_layout.addWidget(self.sequences_list)

        seq_btn_row = QHBoxLayout()
        self.seq_new_btn = QPushButton("New sequence", seq_left)
        set_widget_id(self.seq_new_btn, WS_SEQUENCE_NEW_BUTTON)
        self.seq_new_btn.clicked.connect(self._on_seq_new_clicked)
        seq_btn_row.addWidget(self.seq_new_btn)

        self.seq_dup_btn = QPushButton("Duplicate", seq_left)
        set_widget_id(self.seq_dup_btn, WS_SEQUENCE_DUPLICATE_BUTTON)
        self.seq_dup_btn.clicked.connect(self._on_seq_dup_clicked)
        seq_btn_row.addWidget(self.seq_dup_btn)

        self.seq_del_btn = QPushButton("Delete", seq_left)
        set_widget_id(self.seq_del_btn, WS_SEQUENCE_DELETE_BUTTON)
        self.seq_del_btn.clicked.connect(self._on_seq_del_clicked)
        seq_btn_row.addWidget(self.seq_del_btn)
        seq_left_layout.addLayout(seq_btn_row)

        h_seq_splitter.addWidget(seq_left)

        # Sequence Detail Pane (Steps table & Step controls)
        seq_right = QWidget(h_seq_splitter)
        seq_right_layout = QVBoxLayout(seq_right)
        seq_right_layout.setContentsMargins(0, 0, 0, 0)
        seq_right_layout.setSpacing(4)

        self.steps_table = QTableWidget(0, 4, seq_right)
        set_widget_id(self.steps_table, WS_SEQUENCE_STEPS_TABLE)
        self.steps_table.setHorizontalHeaderLabels(
            ["#", "Message / Preset", "Format", "Delay (ms)"]
        )
        self.steps_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        seq_right_layout.addWidget(self.steps_table)

        step_btn_row = QHBoxLayout()
        self.step_add_btn = QPushButton("Add step", seq_right)
        set_widget_id(self.step_add_btn, WS_SEQUENCE_STEP_ADD_BUTTON)
        self.step_add_btn.clicked.connect(self._on_step_add_clicked)
        step_btn_row.addWidget(self.step_add_btn)

        self.step_remove_btn = QPushButton("Remove step", seq_right)
        set_widget_id(self.step_remove_btn, WS_SEQUENCE_STEP_REMOVE_BUTTON)
        self.step_remove_btn.clicked.connect(self._on_step_remove_clicked)
        step_btn_row.addWidget(self.step_remove_btn)

        self.step_up_btn = QPushButton("Move Up", seq_right)
        set_widget_id(self.step_up_btn, WS_SEQUENCE_STEP_UP_BUTTON)
        self.step_up_btn.clicked.connect(self._on_step_up_clicked)
        step_btn_row.addWidget(self.step_up_btn)

        self.step_down_btn = QPushButton("Move Down", seq_right)
        set_widget_id(self.step_down_btn, WS_SEQUENCE_STEP_DOWN_BUTTON)
        self.step_down_btn.clicked.connect(self._on_step_down_clicked)
        step_btn_row.addWidget(self.step_down_btn)

        step_btn_row.addStretch()
        seq_right_layout.addLayout(step_btn_row)

        h_seq_splitter.addWidget(seq_right)
        h_seq_splitter.setSizes([180, 320])
        seq_layout.addWidget(h_seq_splitter)

        v_splitter.addWidget(seq_box)
        v_splitter.setSizes([220, 260])
        main_layout.addWidget(v_splitter)

    # -------------------------------------------------------------------------
    # Presets Logic & Actions
    # -------------------------------------------------------------------------

    def refresh_all(self) -> None:
        """Refresh presets and sequences lists from connection."""
        self.refresh_presets()
        self.refresh_sequences()

    def refresh_presets(self) -> None:
        conn = self.connection
        self.presets_list.blockSignals(True)
        self.presets_list.clear()
        if conn and conn.presets:
            for p in conn.presets:
                item = QListWidgetItem(f"{p.name} ({p.format.value})")
                item.setData(Qt.ItemDataRole.UserRole, p.id)
                self.presets_list.addItem(item)
        self.presets_list.blockSignals(False)

        if self.presets_list.count() > 0:
            if self._selected_preset_id:
                for i in range(self.presets_list.count()):
                    item = self.presets_list.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == self._selected_preset_id:
                        self.presets_list.setCurrentRow(i)
                        break
                else:
                    self.presets_list.setCurrentRow(0)
            else:
                self.presets_list.setCurrentRow(0)
        else:
            self._clear_preset_details()

    def _clear_preset_details(self) -> None:
        self.preset_name_input.blockSignals(True)
        self.preset_payload_edit.blockSignals(True)
        self.preset_format_combo.blockSignals(True)
        self.preset_name_input.clear()
        self.preset_payload_edit.clear()
        self.preset_name_input.blockSignals(False)
        self.preset_payload_edit.blockSignals(False)
        self.preset_format_combo.blockSignals(False)

    def _on_preset_row_changed(self, row: int) -> None:
        if row < 0:
            self._clear_preset_details()
            return
        item = self.presets_list.item(row)
        if not item:
            return
        preset_id = item.data(Qt.ItemDataRole.UserRole)
        self._selected_preset_id = preset_id
        conn = self.connection
        if not conn:
            return
        preset = next((p for p in conn.presets if p.id == preset_id), None)
        if preset:
            self.preset_name_input.blockSignals(True)
            self.preset_payload_edit.blockSignals(True)
            self.preset_format_combo.blockSignals(True)

            self.preset_name_input.setText(preset.name)
            self.preset_payload_edit.setPlainText(preset.payload)
            for i in range(self.preset_format_combo.count()):
                if self.preset_format_combo.itemData(i) == preset.format:
                    self.preset_format_combo.setCurrentIndex(i)
                    break

            self.preset_name_input.blockSignals(False)
            self.preset_payload_edit.blockSignals(False)
            self.preset_format_combo.blockSignals(False)

    def _on_preset_detail_changed(self) -> None:
        if not self._selected_preset_id or not self.connection:
            return
        preset = next(
            (p for p in self.connection.presets if p.id == self._selected_preset_id), None
        )
        if preset:
            preset.name = self.preset_name_input.text()
            preset.payload = self.preset_payload_edit.toPlainText()
            fmt = self.preset_format_combo.currentData()
            if fmt:
                preset.format = fmt
            # Update list item text
            row = self.presets_list.currentRow()
            if row >= 0:
                item = self.presets_list.item(row)
                if item:
                    item.setText(f"{preset.name} ({preset.format.value})")
            self._notify_save()

    def create_new_preset(
        self,
        name: str = "New Message",
        format: WsMessageFormat = WsMessageFormat.JSON,
        payload: str = "",
    ) -> WebSocketMessagePreset:
        conn = self.connection
        if conn is None:
            conn = WebSocketConnection(id="ws_temp", name="Temp")
            if self.presenter:
                self.presenter.connection = conn

        new_preset = WebSocketMessagePreset(
            id=str(uuid.uuid4()),
            name=name,
            format=format,
            payload=payload,
        )
        conn.presets.append(new_preset)
        self._selected_preset_id = new_preset.id
        logger.info(
            "preset_created preset_id=%s name=%s format=%s bytes=%d",
            new_preset.id,
            new_preset.name,
            new_preset.format.value,
            len(new_preset.payload.encode("utf-8")),
        )
        self.refresh_presets()
        self._notify_save()
        return new_preset

    def duplicate_preset(self, preset_id: str) -> WebSocketMessagePreset:
        conn = self.connection
        if not conn:
            raise ValueError("No connection available")
        src = next((p for p in conn.presets if p.id == preset_id), None)
        if not src:
            raise ValueError(f"Preset {preset_id} not found")
        dup = WebSocketMessagePreset(
            id=str(uuid.uuid4()),
            name=f"{src.name} (Copy)",
            format=src.format,
            payload=src.payload,
        )
        conn.presets.append(dup)
        self._selected_preset_id = dup.id
        logger.info(
            "preset_duplicated src_id=%s new_id=%s name=%s format=%s",
            src.id,
            dup.id,
            dup.name,
            dup.format.value,
        )
        self.refresh_presets()
        self._notify_save()
        return dup

    def delete_preset(self, preset_id: str) -> None:
        conn = self.connection
        if not conn:
            return
        conn.presets = [p for p in conn.presets if p.id != preset_id]
        if self._selected_preset_id == preset_id:
            self._selected_preset_id = None
        logger.info("preset_deleted preset_id=%s", preset_id)
        self.refresh_presets()
        self._notify_save()

    def _on_preset_duplicate_clicked(self) -> None:
        if self._selected_preset_id:
            self.duplicate_preset(self._selected_preset_id)

    def _on_preset_delete_clicked(self) -> None:
        if self._selected_preset_id:
            self.delete_preset(self._selected_preset_id)

    def _on_preset_load_clicked(self) -> None:
        if self._selected_preset_id:
            self.load_preset_into_composer(self._selected_preset_id)

    def load_preset_into_composer(self, preset_id: str) -> None:
        conn = self.connection
        if not conn:
            return
        preset = next((p for p in conn.presets if p.id == preset_id), None)
        if not preset:
            return
        target_composer = self.composer
        if (
            target_composer is None
            and self.presenter
            and hasattr(self.presenter, "_tab")
            and self.presenter._tab
        ):
            target_composer = getattr(self.presenter._tab, "composer", None)
        if target_composer:
            target_composer.set_format(preset.format)
            target_composer.set_payload(preset.payload)
            logger.info(
                "preset_loaded_into_composer preset_id=%s name=%s format=%s",
                preset.id,
                preset.name,
                preset.format.value,
            )

    def _on_preset_send_clicked(self) -> None:
        if self._selected_preset_id:
            self.send_preset_now(self._selected_preset_id)

    def send_preset_now(self, preset_id: str) -> bool:
        if self.presenter is not None:
            state = getattr(
                self.presenter, "state", getattr(self.presenter, "_current_state", None)
            )
            if state != SessionState.OPEN:
                logger.warning(
                    "send_preset_now_blocked_not_open preset_id=%s state=%s",
                    preset_id,
                    state,
                )
                return False

        conn = self.connection
        if not conn:
            return False
        preset = next((p for p in conn.presets if p.id == preset_id), None)
        if not preset:
            return False

        is_valid, err = validate_format(preset.payload, preset.format)
        if not is_valid:
            logger.warning(
                "send_preset_now_invalid_format preset_id=%s format=%s error=%s",
                preset.id,
                preset.format.value,
                err,
            )
            return False

        try:
            encoded = encode_payload(preset.payload, preset.format)
        except Exception as exc:
            logger.error(
                "send_preset_now_encode_failed preset_id=%s format=%s error=%s",
                preset.id,
                preset.format.value,
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
                    "preset_sent_now preset_id=%s name=%s format=%s bytes=%d is_binary=%s",
                    preset.id,
                    preset.name,
                    preset.format.value,
                    byte_size,
                    isinstance(encoded, bytes),
                )
                return True

        logger.info(
            "preset_sent_now preset_id=%s name=%s format=%s bytes=%d is_binary=%s",
            preset.id,
            preset.name,
            preset.format.value,
            byte_size,
            isinstance(encoded, bytes),
        )
        return True

    def has_presets(self) -> bool:
        conn = self.connection
        return bool(conn and len(conn.presets) > 0)

    def get_empty_presets_notice(self) -> Optional[str]:
        if not self.has_presets():
            return (
                "No saved messages yet. Compose one and choose Save... in the composer, or [New]."
            )
        return None

    # -------------------------------------------------------------------------
    # Sequences Logic & Actions
    # -------------------------------------------------------------------------

    def refresh_sequences(self) -> None:
        conn = self.connection
        self.sequences_list.blockSignals(True)
        self.sequences_list.clear()
        if conn and conn.sequences:
            for s in conn.sequences:
                item = QListWidgetItem(f"{s.name} ({len(s.steps)} steps)")
                item.setData(Qt.ItemDataRole.UserRole, s.id)
                self.sequences_list.addItem(item)
        self.sequences_list.blockSignals(False)

        if self.sequences_list.count() > 0:
            if self._selected_sequence_id:
                for i in range(self.sequences_list.count()):
                    item = self.sequences_list.item(i)
                    if item and item.data(Qt.ItemDataRole.UserRole) == self._selected_sequence_id:
                        self.sequences_list.setCurrentRow(i)
                        break
                else:
                    self.sequences_list.setCurrentRow(0)
            else:
                self.sequences_list.setCurrentRow(0)
        else:
            self._render_steps_table(None)

    def _on_sequence_row_changed(self, row: int) -> None:
        if row < 0:
            self._render_steps_table(None)
            return
        item = self.sequences_list.item(row)
        if not item:
            return
        seq_id = item.data(Qt.ItemDataRole.UserRole)
        self.select_sequence(seq_id)

    def select_sequence(self, sequence_id: str) -> None:
        self._selected_sequence_id = sequence_id
        conn = self.connection
        if not conn:
            return
        seq = next((s for s in conn.sequences if s.id == sequence_id), None)
        self._render_steps_table(seq)

    def _render_steps_table(self, seq: Optional[WebSocketSequence]) -> None:
        self.steps_table.setRowCount(0)
        if not seq or not self.connection:
            return

        presets_map = {p.id: p for p in self.connection.presets}
        self.steps_table.setRowCount(len(seq.steps))
        for i, step in enumerate(seq.steps):
            # Column 0: Step number
            self.steps_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            # Column 1: Message / Preset
            if step.preset_id:
                preset = presets_map.get(step.preset_id)
                disp = (
                    f"{preset.name} (preset)"
                    if preset
                    else f"<missing preset: {step.preset_id}>"
                )
                fmt_str = preset.format.value if preset else step.format.value
            else:
                disp = step.inline_payload or "<inline>"
                fmt_str = step.format.value

            self.steps_table.setItem(i, 1, QTableWidgetItem(disp))
            self.steps_table.setItem(i, 2, QTableWidgetItem(fmt_str))
            self.steps_table.setItem(i, 3, QTableWidgetItem(f"{step.delay_ms} ms"))

    def _on_seq_new_clicked(self) -> None:
        conn = self.connection
        if conn is None:
            return
        new_seq = WebSocketSequence(id=str(uuid.uuid4()), name="New Sequence", steps=[])
        conn.sequences.append(new_seq)
        self._selected_sequence_id = new_seq.id
        logger.info("sequence_created seq_id=%s name=%s", new_seq.id, new_seq.name)
        self.refresh_sequences()
        self._notify_save()

    def _on_seq_dup_clicked(self) -> None:
        if not self._selected_sequence_id or not self.connection:
            return
        src = next(
            (s for s in self.connection.sequences if s.id == self._selected_sequence_id), None
        )
        if not src:
            return
        dup = WebSocketSequence(
            id=str(uuid.uuid4()),
            name=f"{src.name} (Copy)",
            steps=[s.model_copy(deep=True) for s in src.steps],
        )
        self.connection.sequences.append(dup)
        self._selected_sequence_id = dup.id
        logger.info(
            "sequence_duplicated src_id=%s new_id=%s name=%s steps=%d",
            src.id,
            dup.id,
            dup.name,
            len(dup.steps),
        )
        self.refresh_sequences()
        self._notify_save()

    def _on_seq_del_clicked(self) -> None:
        if not self._selected_sequence_id or not self.connection:
            return
        seq_id = self._selected_sequence_id
        self.connection.sequences = [
            s for s in self.connection.sequences if s.id != seq_id
        ]
        self._selected_sequence_id = None
        logger.info("sequence_deleted seq_id=%s", seq_id)
        self.refresh_sequences()
        self._notify_save()

    def add_sequence_step(
        self,
        sequence_id: str,
        preset_id: Optional[str] = None,
        inline_payload: str = "",
        format: WsMessageFormat = WsMessageFormat.JSON,
        delay_ms: int = 0,
    ) -> None:
        conn = self.connection
        if not conn:
            return
        seq = next((s for s in conn.sequences if s.id == sequence_id), None)
        if not seq:
            return
        step = WebSocketSequenceStep(
            preset_id=preset_id,
            inline_payload=inline_payload,
            format=format,
            delay_ms=delay_ms,
        )
        seq.steps.append(step)
        logger.info(
            "sequence_step_added seq_id=%s preset_id=%s format=%s delay_ms=%d total_steps=%d",
            sequence_id,
            preset_id,
            format.value,
            delay_ms,
            len(seq.steps),
        )
        self._render_steps_table(seq)
        self._notify_save()

    def _on_step_add_clicked(self) -> None:
        if self._selected_sequence_id:
            self.add_sequence_step(
                self._selected_sequence_id,
                inline_payload="New Step Payload",
                format=WsMessageFormat.TEXT,
                delay_ms=100,
            )

    def remove_sequence_step(self, sequence_id: str, step_index: int) -> None:
        conn = self.connection
        if not conn:
            return
        seq = next((s for s in conn.sequences if s.id == sequence_id), None)
        if not seq or step_index < 0 or step_index >= len(seq.steps):
            return
        seq.steps.pop(step_index)
        logger.info(
            "sequence_step_removed seq_id=%s step_index=%d remaining_steps=%d",
            sequence_id,
            step_index,
            len(seq.steps),
        )
        self._render_steps_table(seq)
        self._notify_save()

    def _on_step_remove_clicked(self) -> None:
        row = self.steps_table.currentRow()
        if self._selected_sequence_id and row >= 0:
            self.remove_sequence_step(self._selected_sequence_id, row)

    def move_sequence_step_up(self, sequence_id: str, step_index: int) -> None:
        conn = self.connection
        if not conn:
            return
        seq = next((s for s in conn.sequences if s.id == sequence_id), None)
        if not seq or step_index <= 0 or step_index >= len(seq.steps):
            return
        seq.steps[step_index - 1], seq.steps[step_index] = (
            seq.steps[step_index],
            seq.steps[step_index - 1],
        )
        logger.debug(
            "sequence_step_moved_up seq_id=%s step_index=%d",
            sequence_id,
            step_index,
        )
        self._render_steps_table(seq)
        self.steps_table.setCurrentCell(step_index - 1, 0)
        self._notify_save()

    def _on_step_up_clicked(self) -> None:
        row = self.steps_table.currentRow()
        if self._selected_sequence_id and row > 0:
            self.move_sequence_step_up(self._selected_sequence_id, row)

    def move_sequence_step_down(self, sequence_id: str, step_index: int) -> None:
        conn = self.connection
        if not conn:
            return
        seq = next((s for s in conn.sequences if s.id == sequence_id), None)
        if not seq or step_index < 0 or step_index >= len(seq.steps) - 1:
            return
        seq.steps[step_index + 1], seq.steps[step_index] = (
            seq.steps[step_index],
            seq.steps[step_index + 1],
        )
        logger.debug(
            "sequence_step_moved_down seq_id=%s step_index=%d",
            sequence_id,
            step_index,
        )
        self._render_steps_table(seq)
        self.steps_table.setCurrentCell(step_index + 1, 0)
        self._notify_save()

    def _on_step_down_clicked(self) -> None:
        row = self.steps_table.currentRow()
        if self._selected_sequence_id and row >= 0:
            self.move_sequence_step_down(self._selected_sequence_id, row)

    def run_sequence(self, sequence_id: str) -> bool:
        if self.presenter is not None:
            state = getattr(
                self.presenter, "state", getattr(self.presenter, "_current_state", None)
            )
            if state != SessionState.OPEN:
                logger.warning(
                    "run_sequence_blocked_not_open seq_id=%s state=%s",
                    sequence_id,
                    state,
                )
                return False
            logger.info("sequence_run_initiated seq_id=%s", sequence_id)
            if hasattr(self.presenter, "run_sequence"):
                return self.presenter.run_sequence(sequence_id)
        return False

    def stop_sequence(self) -> None:
        logger.info("sequence_stop_initiated")
        if self.presenter and hasattr(self.presenter, "stop_sequence"):
            self.presenter.stop_sequence()

    def _notify_save(self) -> None:
        if self.presenter and getattr(self.presenter, "connection", None):
            self.presenter.connection_saved.emit(self.presenter.connection)
