from __future__ import annotations

import logging

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QPlainTextEdit

from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.structure_scanner import get_scanner

logger = logging.getLogger(__name__)

_DEBOUNCE_MS = 200


class FoldController:
    def __init__(
        self,
        editor: QPlainTextEdit,
        body_format: BodyFormat = BodyFormat.JSON,
    ):
        self._editor = editor
        self._body_format = body_format
        self._regions: list[FoldRegion] = []
        self._collapsed_ids: set[str] = set()
        self._header_by_block: dict[int, FoldRegion] = {}

        self._scan_timer = QTimer(editor)
        self._scan_timer.setSingleShot(True)
        self._scan_timer.setInterval(_DEBOUNCE_MS)
        self._scan_timer.timeout.connect(self._run_scan)

        editor.document().contentsChanged.connect(self._schedule_scan)

    def set_body_format(self, body_format: BodyFormat) -> None:
        self._body_format = body_format
        self._schedule_scan()

    def body_format(self) -> BodyFormat:
        return self._body_format

    def regions(self) -> list[FoldRegion]:
        return list(self._regions)

    def is_collapsed(self, region_id: str) -> bool:
        return region_id in self._collapsed_ids

    def toggle(self, region_id: str) -> None:
        if region_id in self._collapsed_ids:
            self._collapsed_ids.discard(region_id)
            collapsed = False
        else:
            self._collapsed_ids.add(region_id)
            collapsed = True
        logger.debug("fold_region_toggled region_id=%s collapsed=%s", region_id, collapsed)
        self.apply_visibility()
        self._editor.viewport().update()

    def expand_all(self) -> None:
        count = len(self._collapsed_ids)
        self._collapsed_ids.clear()
        block = self._editor.document().firstBlock()
        while block.isValid():
            block.setVisible(True)
            block = block.next()
        logger.debug("fold_all_expanded previously_collapsed=%d", count)
        self._editor.viewport().update()

    def collapse_all(self) -> None:
        if self._scan_timer.isActive():
            self._scan_timer.stop()
            self._run_scan()
        for region in self._regions:
            self._collapsed_ids.add(region.region_id)
        logger.debug("fold_all_collapsed total_regions=%d", len(self._regions))
        self.apply_visibility()
        self._editor.viewport().update()

    def fold_all(self) -> None:
        self.collapse_all()

    def unfold_all(self) -> None:
        self.expand_all()

    def reveal_block(self, block_number: int) -> None:
        """Expand any collapsed fold regions that enclose the given block."""
        if not self._collapsed_ids:
            return
        region_by_id = {r.region_id: r for r in self._regions}
        to_unfold: list[str] = []
        for region_id in self._collapsed_ids:
            region = region_by_id.get(region_id)
            if region is not None and region.start_block <= block_number <= region.end_block:
                to_unfold.append(region_id)
        if to_unfold:
            for rid in to_unfold:
                self._collapsed_ids.discard(rid)
            logger.debug(
                "fold_block_revealed block=%d revealed_regions=%s",
                block_number,
                to_unfold,
            )
            self.apply_visibility()
            self._editor.viewport().update()

    def ensure_scanned(self) -> None:
        """Run scan immediately if scheduled."""
        if self._scan_timer.isActive():
            self._scan_timer.stop()
            self._run_scan()
        elif not self._regions and self._editor.toPlainText().strip():
            self._run_scan()

    def fold_header_at_block(self, block_number: int) -> FoldRegion | None:
        return self._header_by_block.get(block_number)

    def apply_visibility(self) -> None:
        doc = self._editor.document()
        block = doc.firstBlock()
        while block.isValid():
            block.setVisible(True)
            block = block.next()

        collapsed_ranges: list[tuple[int, int]] = []
        region_by_id = {r.region_id: r for r in self._regions}
        for region_id in self._collapsed_ids:
            region = region_by_id.get(region_id)
            if region is None:
                continue
            collapsed_ranges.append((region.start_block, region.end_block))

        if not collapsed_ranges:
            return

        collapsed_ranges.sort()
        block = doc.firstBlock()
        block_number = 0
        range_idx = 0
        while block.isValid():
            while (
                range_idx < len(collapsed_ranges)
                and block_number > collapsed_ranges[range_idx][1]
            ):
                range_idx += 1

            if range_idx < len(collapsed_ranges):
                start, end = collapsed_ranges[range_idx]
                if start <= block_number <= end and block_number != start:
                    block.setVisible(False)

            block = block.next()
            block_number += 1

    def _schedule_scan(self) -> None:
        self._scan_timer.start()

    def _run_scan(self) -> None:
        scanner = get_scanner(self._body_format)
        new_regions = scanner.scan(self._editor.document())
        new_ids = {r.region_id for r in new_regions}
        old_by_id = {r.region_id: r for r in self._regions}

        self._collapsed_ids = {
            rid
            for rid in self._collapsed_ids
            if rid in new_ids and _region_unchanged(old_by_id.get(rid), new_regions)
        }

        self._regions = new_regions
        self._header_by_block = {r.header_block: r for r in new_regions}
        logger.debug(
            "fold_scan_completed format=%s regions=%d collapsed=%d",
            self._body_format.value,
            len(new_regions),
            len(self._collapsed_ids),
        )
        self.apply_visibility()
        self._editor.viewport().update()


def _region_unchanged(
    old: FoldRegion | None, new_regions: list[FoldRegion]
) -> bool:
    if old is None:
        return False
    for region in new_regions:
        if region.region_id == old.region_id:
            return (
                region.start_block == old.start_block
                and region.end_block == old.end_block
            )
    return False
