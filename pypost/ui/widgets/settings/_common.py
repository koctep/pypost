"""Shared helpers for Settings dialog section builders."""

from PySide6.QtWidgets import QLabel

SECTION_HEADER_STYLE = "font-weight: bold; margin-top: 8px;"


def make_section_header(title: str) -> QLabel:
    label = QLabel(title)
    label.setStyleSheet(SECTION_HEADER_STYLE)
    return label
