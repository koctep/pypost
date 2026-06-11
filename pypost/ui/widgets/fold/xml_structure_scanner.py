"""XML structure scanner stub (PYPOST-513)."""

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import FoldRegion


class XmlStructureScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        return []
