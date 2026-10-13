"""Read-only foldable code viewer widget with line numbers and folding chevrons."""

from __future__ import annotations


import logging
from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import (
    QFontMetrics,
    QMouseEvent,
    QPaintEvent,
    QPainter,
)
from PySide6.QtWidgets import QPlainTextEdit

from pypost.ui.widgets.fold.fold_controller import FoldController
from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.line_number_area import LineNumberArea

logger = logging.getLogger(__name__)

_CHEVRON_WIDTH = 14
_CHEVRON_PADDING = 2


class FoldableCodeView(QPlainTextEdit):
    """QPlainTextEdit configured with a gutter for line numbers and fold chevrons."""

    def __init__(self, parent=None, indent_size: int = 2):
        super().__init__(parent)
        self.indent_size = indent_size
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._body_format = BodyFormat.PLAIN
        self._fold_controller = FoldController(self, self._body_format)
        self._line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)
        self.update_indent_size(indent_size)

    def fold_controller(self) -> FoldController:
        return self._fold_controller

    def set_body_format(self, body_format: BodyFormat) -> None:
        self._body_format = body_format
        self._fold_controller.set_body_format(body_format)
        self._update_line_number_area_width(0)

    def body_format(self) -> BodyFormat:
        return self._body_format

    def fold_all(self) -> None:
        self._fold_controller.fold_all()

    def unfold_all(self) -> None:
        self._fold_controller.unfold_all()

    def reveal_block(self, block_number: int) -> None:
        self._fold_controller.reveal_block(block_number)

    def setText(self, text: str) -> None:
        """Compatibility alias for setPlainText()."""
        self.setPlainText(text)

    def setPlainText(self, text: str) -> None:
        self._fold_controller.expand_all()
        super().setPlainText(text)

    def _refresh_font_metrics(self) -> None:
        font_metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(self.indent_size * font_metrics.horizontalAdvance(" "))
        self._update_line_number_area_width(0)

    def update_indent_size(self, new_size: int) -> None:
        self.indent_size = new_size
        self._refresh_font_metrics()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self._refresh_font_metrics()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        font_metrics = QFontMetrics(self.document().defaultFont())
        number_width = font_metrics.horizontalAdvance("9") * digits
        return _CHEVRON_WIDTH + _CHEVRON_PADDING + 3 + number_width

    def chevron_width(self) -> int:
        return _CHEVRON_WIDTH

    def _update_line_number_area_width(self, _block_count: int) -> None:
        width = self.line_number_area_width()
        self.setViewportMargins(width, 0, 0, 0)
        cr = self.contentsRect()
        if cr.height() > 0:
            self._line_number_area.setGeometry(
                QRect(cr.left(), cr.top(), width, cr.height())
            )

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self.palette().color(self.backgroundRole()))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        gutter_color = self.palette().color(self.foregroundRole())
        gutter_color.setAlpha(128)
        painter.setPen(gutter_color)

        number_left = _CHEVRON_WIDTH + _CHEVRON_PADDING

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                region = self._fold_controller.fold_header_at_block(block_number)
                if region is not None:
                    chevron = (
                        "\u25b6"
                        if self._fold_controller.is_collapsed(region.region_id)
                        else "\u25bc"
                    )
                    painter.drawText(
                        0,
                        top,
                        _CHEVRON_WIDTH,
                        self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignCenter,
                        chevron,
                    )

                number = str(block_number + 1)
                painter.drawText(
                    number_left,
                    top,
                    self._line_number_area.width() - number_left - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def _toggle_fold_at_y(
        self, y: float, require_chevron_zone: bool = True, x: float = 0.0
    ) -> None:
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid():
            if block.isVisible() and top <= y <= bottom:
                if not require_chevron_zone or x <= _CHEVRON_WIDTH:
                    region = self._fold_controller.fold_header_at_block(block_number)
                    if region is not None:
                        logger.debug(
                            "foldable_code_view_gutter_toggle block=%d region=%s dblclick=%s",
                            block_number,
                            region.region_id,
                            not require_chevron_zone,
                        )
                        self._fold_controller.toggle(region.region_id)
                        self._line_number_area.update()
                return

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def line_number_area_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        event.accept()
        self._toggle_fold_at_y(
            event.position().y(), require_chevron_zone=True, x=event.position().x()
        )

    def line_number_area_mouse_double_click(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        event.accept()
        self._toggle_fold_at_y(
            event.position().y(), require_chevron_zone=False, x=event.position().x()
        )
