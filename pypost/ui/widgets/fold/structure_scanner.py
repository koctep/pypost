"""Structure scanner protocol and format registry."""

from __future__ import annotations


from typing import Protocol

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.json_structure_scanner import JsonStructureScanner
from pypost.ui.widgets.fold.xml_structure_scanner import XmlStructureScanner
from pypost.ui.widgets.fold.yaml_structure_scanner import YamlStructureScanner


class StructureScanner(Protocol):
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
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


class _PlainScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        return []
