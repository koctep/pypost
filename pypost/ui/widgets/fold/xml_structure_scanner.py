"""XML nestable-region detection for code folding."""

import xml.etree.ElementTree as ET
from collections import defaultdict

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import FoldRegion


def _line_at_offset(text: str, offset: int) -> int:
    return text[:offset].count("\n")


def _path_id(segments: list[str]) -> str:
    if not segments:
        return "/"
    return "/" + "/".join(segments)


def _scan_regions(text: str) -> list[FoldRegion]:
    regions: list[FoldRegion] = []
    stack: list[tuple[str, int, list[str]]] = []
    sibling_counts: dict[tuple[str, ...], dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    index = 0
    length = len(text)

    while index < length:
        if text[index] != "<":
            index += 1
            continue

        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            if end == -1:
                return []
            index = end + 3
            continue

        if text.startswith("<![CDATA[", index):
            end = text.find("]]>", index + 9)
            if end == -1:
                return []
            index = end + 3
            continue

        if index + 1 < length and text[index + 1] in "?!":
            end = text.find(">", index)
            if end == -1:
                return []
            index = end + 1
            continue

        closing = text[index + 1] == "/"
        cursor = index + (2 if closing else 1)
        name_start = cursor
        while cursor < length and text[cursor] not in " \t\r\n>/":
            cursor += 1
        if cursor == name_start:
            return []
        tag_name = text[name_start:cursor]

        in_quote: str | None = None
        while cursor < length:
            character = text[cursor]
            if in_quote:
                if character == in_quote:
                    in_quote = None
            elif character in "\"'":
                in_quote = character
            elif character == ">":
                break
            cursor += 1
        if cursor >= length:
            return []

        tag_text = text[index : cursor + 1]
        self_closing = tag_text.rstrip().endswith("/>")
        line = _line_at_offset(text, index)

        if closing:
            if not stack or stack[-1][0] != tag_name:
                return []
            _, start_line, path = stack.pop()
            end_line = _line_at_offset(text, cursor)
            if end_line > start_line:
                regions.append(
                    FoldRegion(
                        region_id=_path_id(path),
                        header_block=start_line,
                        start_block=start_line,
                        end_block=end_line,
                        kind="element",
                    )
                )
        elif not self_closing:
            parent_path = stack[-1][2] if stack else []
            sibling_index = sibling_counts[tuple(parent_path)][tag_name]
            sibling_counts[tuple(parent_path)][tag_name] += 1
            if parent_path:
                path = [*parent_path, f"{tag_name}[{sibling_index}]"]
            else:
                path = [tag_name]
            stack.append((tag_name, line, path))

        index = cursor + 1

    if stack:
        return []
    return regions


class XmlStructureScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        text = document.toPlainText()
        if not text.strip():
            return []
        try:
            ET.fromstring(text)
        except ET.ParseError:
            return []
        return _scan_regions(text)
