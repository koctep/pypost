"""Structure scanner protocol and format registry."""

from __future__ import annotations


from collections.abc import Callable
from typing import Protocol

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.json_structure_scanner import JsonStructureScanner
from pypost.ui.widgets.fold.xml_structure_scanner import XmlStructureScanner
from pypost.ui.widgets.fold.yaml_structure_scanner import YamlStructureScanner


class StructureScanner(Protocol):
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        ...

    def scan_text(
        self, text: str, is_interrupted: Callable[[], bool] | None = None
    ) -> list[FoldRegion]:
        ...


_SCANNERS: dict[BodyFormat, StructureScanner] = {
    BodyFormat.JSON: JsonStructureScanner(),
    BodyFormat.YAML: YamlStructureScanner(),
    BodyFormat.XML: XmlStructureScanner(),
}


def get_scanner(body_format: BodyFormat) -> StructureScanner:
    if body_format is BodyFormat.PLAIN:
        return _PlainScanner()
    return _SCANNERS[body_format]


def scan_text(
    text: str,
    body_format: BodyFormat,
    is_interrupted: Callable[[], bool] | None = None,
) -> list[FoldRegion]:
    if body_format is BodyFormat.PLAIN:
        return []
    scanner = _SCANNERS.get(body_format)
    if scanner is None:
        return []
    return scanner.scan_text(text, is_interrupted=is_interrupted)


class _PlainScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        return []

    def scan_text(
        self, text: str, is_interrupted: Callable[[], bool] | None = None
    ) -> list[FoldRegion]:
        return []
