"""YAML nestable-region detection for code folding."""

from __future__ import annotations


from collections.abc import Callable
import io
import logging

import yaml
from PySide6.QtGui import QTextDocument
from yaml.nodes import MappingNode, SequenceNode

from pypost.ui.widgets.fold.fold_region import FoldRegion
from pypost.ui.widgets.fold.scan_utils import append_region_if_multiline, path_id

logger = logging.getLogger(__name__)


def _collect_regions(
    node: MappingNode | SequenceNode,
    path: list[str | int],
    regions: list[FoldRegion],
) -> None:
    if isinstance(node, MappingNode):
        start = node.start_mark.line
        end = node.end_mark.line
        append_region_if_multiline(
            regions,
            region_id=path_id(path),
            start_line=start,
            end_line=end,
            kind="object",
        )
        for key_node, value_node in node.value:
            key = key_node.value if key_node.value is not None else "?"
            _collect_regions(value_node, [*path, key], regions)
    elif isinstance(node, SequenceNode):
        start = node.start_mark.line
        end = node.end_mark.line
        append_region_if_multiline(
            regions,
            region_id=path_id(path),
            start_line=start,
            end_line=end,
            kind="array",
        )
        for index, child in enumerate(node.value):
            _collect_regions(child, [*path, index], regions)


class YamlStructureScanner:
    def scan_text(
        self, text: str, is_interrupted: Callable[[], bool] | None = None
    ) -> list[FoldRegion]:
        if not text.strip():
            return []
        if is_interrupted is not None and is_interrupted():
            return []
        try:
            stream = io.StringIO(text)
            regions: list[FoldRegion] = []
            for node in yaml.compose_all(stream, Loader=yaml.SafeLoader):
                if is_interrupted is not None and is_interrupted():
                    return []
                _collect_regions(node, [], regions)
            return regions
        except yaml.YAMLError as exc:
            logger.debug("yaml_scan_parse_skipped error=%s", exc)
            return []

    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        return self.scan_text(document.toPlainText())
