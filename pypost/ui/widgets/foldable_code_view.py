"""Read-only foldable code viewer widget with line numbers and folding chevrons."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

if TYPE_CHECKING:
    from pypost.ui.widgets.response_mask_controller import ResponseMaskController


class FoldableCodeView(FoldablePlainTextEdit):
    """QPlainTextEdit configured with a gutter for line numbers and fold chevrons."""

    def __init__(self, parent: QWidget | None = None, indent_size: int = 2) -> None:
        super().__init__(parent=parent, indent_size=indent_size)
        self._mask_controller: ResponseMaskController | None = None

    def set_mask_controller(self, controller: ResponseMaskController | None) -> None:
        self._mask_controller = controller

    def mask_controller(self) -> ResponseMaskController | None:
        return self._mask_controller
