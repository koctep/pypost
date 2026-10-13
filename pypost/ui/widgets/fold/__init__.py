"""Code folding for structured body content (JSON/YAML/XML)."""

from __future__ import annotations


from pypost.ui.widgets.fold.fold_controller import FoldController
from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.format_detector import detect_body_format

__all__ = ["BodyFormat", "FoldController", "FoldRegion", "detect_body_format"]
