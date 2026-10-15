from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QPlainTextEdit

from pypost.ui.widgets.fold.fold_region import BodyFormat, FoldRegion
from pypost.ui.widgets.fold.fold_worker import FoldScanWorker
from pypost.ui.widgets.fold.structure_scanner import scan_text

logger = logging.getLogger(__name__)

_DEBOUNCE_MS = 200


class FoldController(QObject):
    """Controls code folding for a host QPlainTextEdit."""

    LARGE_DOCUMENT_THRESHOLD_BYTES: int = 500 * 1024
    scan_finished = Signal(list)

    def __init__(
        self,
        editor: QPlainTextEdit,
        body_format: BodyFormat = BodyFormat.JSON,
    ) -> None:
        super().__init__(editor)
        self._editor = editor
        self._body_format = body_format
        self._regions: list[FoldRegion] = []
        self._collapsed_ids: set[str] = set()
        self._header_by_block: dict[int, FoldRegion] = {}

        self._generation: int = 0
        self._active_worker: FoldScanWorker | None = None
        self._pending_fold_all: bool = False
        self._pending_unfold_all: bool = False

        self._scan_timer = QTimer(editor)
        self._scan_timer.setSingleShot(True)
        self._scan_timer.setInterval(_DEBOUNCE_MS)
        self._scan_timer.timeout.connect(self._run_scan)

        editor.document().contentsChanged.connect(self._schedule_scan)
        editor.destroyed.connect(self._cleanup_worker)

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
        self._pending_fold_all = False
        if self._active_worker is not None and self._active_worker.isRunning():
            self._pending_unfold_all = True
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
        if self._active_worker is not None and self._active_worker.isRunning():
            self._pending_fold_all = True
            self._pending_unfold_all = False
            return
        self._pending_fold_all = False
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
        self._generation += 1
        generation = self._generation

        if self._active_worker is not None:
            logger.debug(
                "superseding_active_fold_worker next_generation=%d",
                generation,
            )
            self._active_worker.requestInterruption()

        text = self._editor.toPlainText()
        byte_size = len(text.encode("utf-8"))
        is_large = (
            len(text) >= self.LARGE_DOCUMENT_THRESHOLD_BYTES
            or byte_size >= self.LARGE_DOCUMENT_THRESHOLD_BYTES
        )

        if not is_large:
            self._active_worker = None
            logger.debug(
                "synchronous_fold_scan_dispatched size_bytes=%d format=%s",
                byte_size,
                self._body_format.value,
            )
            new_regions = scan_text(text, self._body_format)
            self._apply_scan_results(new_regions)
            self.scan_finished.emit(self._regions)
        else:
            logger.debug(
                "background_fold_scan_dispatched generation=%d size_bytes=%d format=%s",
                generation,
                byte_size,
                self._body_format.value,
            )
            worker = FoldScanWorker(generation, text, self._body_format)
            worker.scan_completed.connect(self._on_background_scan_completed)
            worker.scan_failed.connect(self._on_background_scan_failed)
            worker.finished.connect(worker.deleteLater)
            self._active_worker = worker
            worker.start()

    def _on_background_scan_completed(
        self, generation: int, regions: list[FoldRegion]
    ) -> None:
        if generation != self._generation:
            logger.debug(
                "background_fold_scan_stale_discarded generation=%d current_generation=%d",
                generation,
                self._generation,
            )
            return
        self._active_worker = None
        self._apply_scan_results(regions)
        if self._pending_fold_all:
            self._pending_fold_all = False
            for region in self._regions:
                self._collapsed_ids.add(region.region_id)
            self.apply_visibility()
            self._editor.viewport().update()
        elif self._pending_unfold_all:
            self._pending_unfold_all = False
            self.expand_all()
        self.scan_finished.emit(self._regions)

    def _apply_scan_results(self, new_regions: list[FoldRegion]) -> None:
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

    def _on_background_scan_failed(
        self, generation: int, error_message: str
    ) -> None:
        if generation != self._generation:
            logger.debug(
                "background_fold_scan_stale_error_discarded generation=%d current_generation=%d",
                generation,
                self._generation,
            )
            return
        self._active_worker = None
        logger.warning(
            "background_fold_scan_failed generation=%d error=%s",
            generation,
            error_message,
        )
        self._apply_scan_results([])
        self.scan_finished.emit(self._regions)

    def _cleanup_worker(self, _obj: object = None) -> None:
        if self._active_worker is not None:
            if self._active_worker.isRunning():
                logger.debug("cleaning_up_fold_worker")
                self._active_worker.requestInterruption()
                self._active_worker.wait(500)
            self._active_worker = None

    def __del__(self) -> None:
        try:
            self._cleanup_worker()
        except Exception:
            pass


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
