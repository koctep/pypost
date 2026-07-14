"""JSON nestable-region detection for code folding."""

from __future__ import annotations


import json
from dataclasses import dataclass, field

from PySide6.QtGui import QTextDocument

from pypost.ui.widgets.fold.fold_region import FoldRegion
from pypost.ui.widgets.fold.scan_utils import append_region_if_multiline, line_at_offset, path_id


@dataclass
class _ScanContext:
    kind: str
    path: list[str | int] = field(default_factory=list)
    array_index: int = 0


class JsonStructureScanner:
    def scan(self, document: QTextDocument) -> list[FoldRegion]:
        text = document.toPlainText()
        if not text.strip():
            return []
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return []
        return _scan_regions(text)


def _child_path(
    contexts: list[_ScanContext], key: str | None
) -> list[str | int]:
    if not contexts:
        return []
    parent = contexts[-1]
    if parent.kind == "object":
        if key is not None:
            return list(parent.path) + [key]
        return list(parent.path)
    return list(parent.path) + [parent.array_index]


def _advance_array_index(contexts: list[_ScanContext]) -> None:
    if contexts and contexts[-1].kind == "array":
        contexts[-1].array_index += 1


def _scan_regions(text: str) -> list[FoldRegion]:
    regions: list[FoldRegion] = []
    open_stack: list[tuple[int, str, str]] = []
    contexts: list[_ScanContext] = []

    in_string = False
    escape = False
    string_char = ""
    pending_key: str | None = None
    pending_object_key: str | None = None
    after_colon = False
    i = 0

    while i < len(text):
        ch = text[i]

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_char:
                in_string = False
            i += 1
            continue

        if ch in "\"'":
            if pending_key is None and not after_colon:
                key_start = i + 1
                j = i + 1
                esc = False
                while j < len(text):
                    if esc:
                        esc = False
                    elif text[j] == "\\":
                        esc = True
                    elif text[j] == ch:
                        pending_key = text[key_start:j]
                        break
                    j += 1
            in_string = True
            string_char = ch
            i += 1
            continue

        if ch == "{":
            path = _child_path(contexts, pending_object_key)
            line = line_at_offset(text, i)
            region_id = path_id(path)
            open_stack.append((line, "object", region_id))
            contexts.append(_ScanContext("object", list(path)))
            pending_key = None
            pending_object_key = None
            after_colon = False
        elif ch == "[":
            path = _child_path(contexts, pending_object_key)
            line = line_at_offset(text, i)
            region_id = path_id(path)
            open_stack.append((line, "array", region_id))
            contexts.append(_ScanContext("array", list(path)))
            pending_key = None
            pending_object_key = None
            after_colon = False
        elif ch == "}":
            if not open_stack:
                return []
            start_line, kind, region_id = open_stack.pop()
            contexts.pop()
            append_region_if_multiline(
                regions,
                region_id=region_id,
                start_line=start_line,
                end_line=line_at_offset(text, i),
                kind=kind,
            )
            pending_key = None
            pending_object_key = None
            after_colon = False
        elif ch == "]":
            if not open_stack:
                return []
            start_line, kind, region_id = open_stack.pop()
            contexts.pop()
            append_region_if_multiline(
                regions,
                region_id=region_id,
                start_line=start_line,
                end_line=line_at_offset(text, i),
                kind=kind,
            )
            pending_key = None
            pending_object_key = None
            after_colon = False
        elif ch == ":":
            if pending_key is not None:
                pending_object_key = pending_key
                pending_key = None
            after_colon = True
        elif ch == ",":
            _advance_array_index(contexts)
            after_colon = False
            pending_key = None
            pending_object_key = None
        elif ch not in " \t\r\n":
            after_colon = False

        i += 1

    if open_stack:
        return []

    return regions
