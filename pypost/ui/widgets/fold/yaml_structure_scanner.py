"""YAML nestable-region detection for code folding."""

import io

import yaml
from PySide6.QtGui import QTextDocument
from yaml.nodes import MappingNode, SequenceNode

from pypost.ui.widgets.fold.fold_region import FoldRegion


def _path_id(segments: list[str | int]) -> str:
    if not segments:
        return "/"
    return "/" + "/".join(str(segment) for segment in segments)


def _collect_regions(
    node: MappingNode | SequenceNode,
    path: list[str | int],
    regions: list[FoldRegion],
) -> None:
    if isinstance(node, MappingNode):
        start = node.start_mark.line
        end = node.end_mark.line
        if end > start:
            regions.append(
                FoldRegion(
                    region_id=_path_id(path),
                    header_block=start,
                    start_block=start,
                    end_block=end,
                    kind="object",
                )
            )
        for key_node, value_node in node.value:
            key = key_node.value if key_node.value is not None else "?"
            _collect_regions(value_node, [*path, key], regions)
    elif isinstance(node, SequenceNode):
        start = node.start_mark.line
        end = node.end_mark.line
        if end > start:
            regions.append(
                FoldRegion(
                    region_id=_path_id(path),
                    header_block=start,
                    start_block=start,
                    end_block=end,
                    kind="array",
                )
            )
        for index, child in enumerate(node.value):
            _collect_regions(child, [*path, index], regions)


class YamlStructureScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        text = document.toPlainText()
        if not text.strip():
            return []
        try:
            stream = io.StringIO(text)
            regions: list[FoldRegion] = []
            for node in yaml.compose_all(stream, Loader=yaml.SafeLoader):
                _collect_regions(node, [], regions)
            return regions
        except yaml.YAMLError:
            return []
