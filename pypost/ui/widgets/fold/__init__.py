"""Code folding for structured body content (JSON/YAML/XML)."""

from __future__ import annotations


from pypost.ui.widgets.fold.fold_controller import FoldController
from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.fold_worker import FoldScanWorker
from pypost.ui.widgets.fold.format_detector import detect_body_format
from pypost.ui.widgets.fold.structure_scanner import scan_text

__all__ = [
    "BodyFormat",
    "FoldController",
    "FoldRegion",
    "FoldScanWorker",
    "detect_body_format",
    "scan_text",
]
