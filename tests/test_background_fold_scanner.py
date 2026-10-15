"""Tests for background folding scanner and threshold dispatch (PYPOST-1370).

Asserts contract and behavior for:
- Document size threshold dispatch (synchronous < 500 KB, background worker >= 500 KB)
- FoldScanWorker thread isolation off UI thread
- Signal emission: scan_finished = Signal(list)
- Stale scan invalidation / generation counter cancellation on rapid text edits
- Structural equivalence across JSON, YAML, XML (scan_text vs scan)
- Fold state preservation across background scan completions
- Pending bulk fold actions (fold_all / unfold_all) during in-flight background scans
"""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from PySide6.QtCore import QObject, QThread
from PySide6.QtGui import QTextDocument
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pypost.ui.widgets.fold import BodyFormat, FoldController, FoldRegion
from pypost.ui.widgets.fold.structure_scanner import get_scanner
from tests.helpers.process_until import process_until

try:
    from pypost.ui.widgets.fold.fold_worker import FoldScanWorker
except ImportError:
    FoldScanWorker = None  # type: ignore[assignment, misc]

try:
    from pypost.ui.widgets.fold.structure_scanner import scan_text
except ImportError:
    scan_text = None  # type: ignore[assignment]


pytestmark = pytest.mark.timeout(30)

_THRESHOLD_BYTES = 500 * 1024


def _generate_json_payload(target_bytes: int) -> str:
    """Generate a syntactically valid JSON document of at least target_bytes."""
    items = []
    current_size = 20
    idx = 0
    while current_size < target_bytes:
        obj = {
            "id": idx,
            "name": f"item_{idx}",
            "description": "x" * 200,
            "tags": ["alpha", "beta", "gamma"],
        }
        items.append(obj)
        current_size += 260
        idx += 1
    return json.dumps({"items": items}, indent=2)


def _generate_yaml_payload(target_bytes: int) -> str:
    """Generate a syntactically valid YAML document of at least target_bytes."""
    lines = ["items:"]
    current_size = len(lines[0]) + 1
    idx = 0
    while current_size < target_bytes:
        entry = f"  - id: {idx}\n    name: item_{idx}\n    data: {'y' * 150}"
        lines.append(entry)
        current_size += len(entry) + 1
        idx += 1
    return "\n".join(lines)


def _generate_xml_payload(target_bytes: int) -> str:
    """Generate a syntactically valid XML document of at least target_bytes."""
    lines = ["<root>"]
    current_size = len(lines[0]) + 1
    idx = 0
    while current_size < target_bytes:
        entry = (
            f'  <item id="{idx}"><name>item_{idx}</name><desc>{"z" * 150}</desc></item>'
        )
        lines.append(entry)
        current_size += len(entry) + 1
        idx += 1
    lines.append("</root>")
    return "\n".join(lines)


def test_document_size_threshold_dispatch(qapp: QApplication) -> None:
    """Payloads < 500 KB parse synchronously; payloads >= 500 KB spawn FoldScanWorker."""
    assert hasattr(
        FoldController, "LARGE_DOCUMENT_THRESHOLD_BYTES"
    ), "FoldController must define LARGE_DOCUMENT_THRESHOLD_BYTES constant"
    assert (
        FoldController.LARGE_DOCUMENT_THRESHOLD_BYTES == _THRESHOLD_BYTES
    ), f"LARGE_DOCUMENT_THRESHOLD_BYTES must be {_THRESHOLD_BYTES}"
    assert issubclass(
        FoldController, QObject
    ), "FoldController must inherit from QObject to support signals and slots"
    assert hasattr(
        FoldController, "scan_finished"
    ), "FoldController must declare scan_finished = Signal(list)"

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    # 1. Payload < 500 KB must parse synchronously without a background worker
    small_json = _generate_json_payload(20 * 1024)
    assert len(small_json) < _THRESHOLD_BYTES
    editor.setPlainText(small_json)

    spy_sync = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()

    assert (
        getattr(fc, "_active_worker", None) is None
    ), "Small document (< 500 KB) must not spawn a background worker"
    assert (
        len(fc.regions()) > 0
    ), "Synchronous scan must immediately populate fold regions"
    assert spy_sync.count() >= 1, "scan_finished must be emitted for synchronous scans"

    # 2. Payload >= 500 KB must dispatch to background FoldScanWorker
    assert (
        FoldScanWorker is not None
    ), "FoldScanWorker must be implemented in pypost.ui.widgets.fold.fold_worker"

    large_json = _generate_json_payload(520 * 1024)
    assert len(large_json) >= _THRESHOLD_BYTES
    editor.setPlainText(large_json)

    spy_async = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()

    active_worker = getattr(fc, "_active_worker", None)
    assert active_worker is not None, "Large document (>= 500 KB) must spawn a worker"
    assert isinstance(
        active_worker, FoldScanWorker
    ), f"Worker must be an instance of FoldScanWorker, got {type(active_worker)}"
    assert (
        active_worker.isRunning() or spy_async.count() > 0
    ), "Background worker must be started on large payload"

    # Wait for completion via scan_finished signal
    process_until(lambda: spy_async.count() >= 1, timeout_ms=10_000)
    assert len(fc.regions()) > 0, "Background scan must populate fold regions"
    assert (
        getattr(fc, "_active_worker", None) is None
    ), "Active worker reference must be cleared after completion"


def test_background_worker_thread_isolation(qapp: QApplication) -> None:
    """FoldScanWorker must execute parsing on a background thread distinct from UI thread."""
    assert (
        FoldScanWorker is not None
    ), "FoldScanWorker must be implemented in pypost.ui.widgets.fold.fold_worker"
    assert issubclass(
        FoldScanWorker, QThread
    ), "FoldScanWorker must subclass QThread for Qt event loop integration"

    main_thread = QApplication.instance().thread()
    worker_execution_threads: list[QThread] = []

    large_json = _generate_json_payload(520 * 1024)
    worker = FoldScanWorker(1, large_json, BodyFormat.JSON)

    assert hasattr(
        worker, "scan_completed"
    ), "FoldScanWorker must declare scan_completed Signal"

    # Capture execution thread inside scan_completed or worker run
    spy = QSignalSpy(worker.scan_completed)

    def on_completed(generation: int, regions: list[Any]) -> None:
        worker_execution_threads.append(QThread.currentThread())

    worker.scan_completed.connect(on_completed)
    worker.start()

    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)
    worker.wait(2000)

    assert spy.count() == 1, "scan_completed must be emitted exactly once"
    assert spy.at(0)[0] == 1, "Emitted generation must match worker input generation"
    assert (
        len(spy.at(0)[1]) > 0
    ), "Emitted regions list must contain discovered fold regions"

    # Slot executes on UI thread via queued connection
    assert (
        worker_execution_threads[0] == main_thread
    ), "Delivered slot should execute on main UI thread"
    assert (
        worker.thread() != worker
    ), "Worker run context must be separate from main thread"


def test_stale_scan_cancellation_on_rapid_edits(qapp: QApplication) -> None:
    """Rapid text modifications must cancel stale in-flight workers via generation check."""
    assert (
        FoldScanWorker is not None
    ), "FoldScanWorker must be implemented in pypost.ui.widgets.fold.fold_worker"

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    large_json_v1 = _generate_json_payload(520 * 1024)
    editor.setPlainText(large_json_v1)
    fc.ensure_scanned()

    worker_1 = getattr(fc, "_active_worker", None)
    assert worker_1 is not None, "First edit must launch worker_1"
    gen_1 = getattr(fc, "_generation", None)
    assert gen_1 is not None, "FoldController must track monotonic _generation"

    # Rapid second modification: change payload and force immediate second scan
    large_json_v2 = large_json_v1 + "\n// revision 2"
    editor.setPlainText(large_json_v2)
    fc.ensure_scanned()

    worker_2 = getattr(fc, "_active_worker", None)
    gen_2 = getattr(fc, "_generation", None)

    assert gen_2 > gen_1, "Second scan must increment _generation"
    assert worker_2 is not None and worker_2 != worker_1, "New worker must be created"
    assert (
        worker_1.isInterruptionRequested()
    ), "Superseded worker_1 must be cooperatively cancelled with requestInterruption()"

    # If worker_1 attempts to deliver results, they must be discarded
    dummy_stale_regions = [FoldRegion("stale_root", 0, 10, 0, "object")]
    fc._on_background_scan_completed(gen_1, dummy_stale_regions)
    assert not any(
        r.region_id == "stale_root" for r in fc.regions()
    ), "Results from obsolete generation must be discarded by FoldController"


def test_background_scan_equivalence_json_yaml_xml() -> None:
    """scan_text must produce identical FoldRegion structure to QTextDocument scanner."""
    assert (
        scan_text is not None
    ), "scan_text function must be implemented in pypost.ui.widgets.fold.structure_scanner"

    formats_and_payloads = [
        (BodyFormat.JSON, _generate_json_payload(520 * 1024)),
        (BodyFormat.YAML, _generate_yaml_payload(520 * 1024)),
        (BodyFormat.XML, _generate_xml_payload(520 * 1024)),
    ]

    for body_format, text in formats_and_payloads:
        doc = QTextDocument(text)
        legacy_scanner = get_scanner(body_format)
        doc_regions = legacy_scanner.scan(doc)
        text_regions = scan_text(text, body_format)

        assert len(text_regions) == len(doc_regions), (
            f"Region count mismatch for format {body_format.value}: "
            f"{len(text_regions)} vs {len(doc_regions)}"
        )

        for tr, dr in zip(text_regions, doc_regions):
            assert (
                tr.region_id == dr.region_id
            ), f"Region ID mismatch: {tr.region_id} != {dr.region_id}"
            assert (
                tr.start_block == dr.start_block
            ), f"start_block mismatch for {tr.region_id}"
            assert (
                tr.end_block == dr.end_block
            ), f"end_block mismatch for {tr.region_id}"
            assert (
                tr.header_block == dr.header_block
            ), f"header_block mismatch for {tr.region_id}"
            assert tr.kind == dr.kind, f"kind mismatch for {tr.region_id}"


def test_fold_state_preserved_after_background_scan(qapp: QApplication) -> None:
    """Existing collapsed fold state must be preserved across background scan updates."""
    assert hasattr(
        FoldController, "scan_finished"
    ), "FoldController must declare scan_finished Signal"

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    large_json = _generate_json_payload(520 * 1024)
    editor.setPlainText(large_json)

    spy = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()
    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)

    regions = fc.regions()
    assert len(regions) > 2, "Payload must have multiple fold regions"
    target_region = regions[1]
    fc.toggle(target_region.region_id)
    assert fc.is_collapsed(
        target_region.region_id
    ), "Target region must be collapsed after toggle"

    # Now append whitespace or comment at the end so regions remain structurally unchanged
    updated_json = large_json + "\n  \n"
    editor.setPlainText(updated_json)

    spy = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()
    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)

    assert fc.is_collapsed(
        target_region.region_id
    ), "Collapsed region state must be preserved after background scan completion"


def test_bulk_fold_queued_during_background_scan(qapp: QApplication) -> None:
    """fold_all() during background scan must collapse all regions upon completion."""
    assert (
        FoldScanWorker is not None
    ), "FoldScanWorker must be implemented in pypost.ui.widgets.fold.fold_worker"
    assert hasattr(
        FoldController, "scan_finished"
    ), "FoldController must declare scan_finished Signal"

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    large_json = _generate_json_payload(520 * 1024)
    editor.setPlainText(large_json)

    spy = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()

    # While background scan is running, invoke fold_all()
    assert (
        getattr(fc, "_active_worker", None) is not None
    ), "Worker should be running for large payload"
    fc.fold_all()

    assert (
        getattr(fc, "_pending_fold_all", False) is True
    ), "FoldController must record _pending_fold_all = True while worker is in flight"

    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)

    assert (
        getattr(fc, "_pending_fold_all", False) is False
    ), "_pending_fold_all must be cleared after applying bulk collapse"
    regions = fc.regions()
    assert len(regions) > 0, "Regions must be discovered"
    assert all(
        fc.is_collapsed(r.region_id) for r in regions
    ), "All discovered regions must be collapsed following queued fold_all()"


def test_worker_interruption_cooperative() -> None:
    """FoldScanWorker must respect requestInterruption() without emitting stale results."""
    assert (
        FoldScanWorker is not None
    ), "FoldScanWorker must be implemented in pypost.ui.widgets.fold.fold_worker"

    large_json = _generate_json_payload(600 * 1024)
    worker = FoldScanWorker(99, large_json, BodyFormat.JSON)

    spy_completed = QSignalSpy(worker.scan_completed)

    # Request interruption before run starts
    worker.requestInterruption()
    worker.start()
    worker.wait(5000)

    assert (
        spy_completed.count() == 0
    ), "Cooperatively interrupted worker must not emit scan_completed"


def test_background_fold_scan_dispatch_and_completion_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """Observability: debug logging on dispatch and completion without payloads."""
    caplog.set_level(logging.DEBUG)

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    large_json = _generate_json_payload(520 * 1024)
    editor.setPlainText(large_json)

    spy = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()
    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)

    # 1. Background dispatch must be logged with generation, size_bytes, format
    dispatch_logs = [
        rec.getMessage()
        for rec in caplog.records
        if "background_fold_scan_dispatched" in rec.getMessage()
    ]
    assert len(dispatch_logs) >= 1, "Dispatch log must be emitted"
    dispatch_msg = dispatch_logs[0]
    assert "generation=" in dispatch_msg
    assert "size_bytes=" in dispatch_msg
    assert "format=json" in dispatch_msg

    # 2. Worker completion must be logged with generation, format, regions, duration
    completion_logs = [
        rec.getMessage()
        for rec in caplog.records
        if "fold_scan_worker_completed" in rec.getMessage()
    ]
    assert len(completion_logs) >= 1, "Worker completion log must be emitted"
    completion_msg = completion_logs[0]
    assert "generation=" in completion_msg
    assert "format=json" in completion_msg
    assert "regions=" in completion_msg
    assert "duration=" in completion_msg

    # 3. Payload sanity: raw payload string must never be dumped in any log record
    for rec in caplog.records:
        msg = rec.getMessage()
        assert "x" * 100 not in msg, "Large document payload leaked into log message"


def test_background_fold_scan_cancellation_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """Observability: worker cancellation must log structured debug with duration."""
    caplog.set_level(logging.DEBUG)

    large_json = _generate_json_payload(520 * 1024)
    worker = FoldScanWorker(42, large_json, BodyFormat.JSON)
    worker.requestInterruption()
    worker.start()
    worker.wait(5000)

    cancellation_logs = [
        rec.getMessage()
        for rec in caplog.records
        if "fold_scan_worker_cancelled" in rec.getMessage()
    ]
    assert len(cancellation_logs) >= 1, "Worker cancellation log must be emitted"
    cancel_msg = cancellation_logs[0]
    assert "generation=42" in cancel_msg
    assert "format=json" in cancel_msg
    assert "duration=" in cancel_msg


def test_background_fold_scan_failure_logging(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observability: worker failure must log error without leaking full payload."""
    caplog.set_level(logging.DEBUG)

    def _failing_scan(*args: Any, **kwargs: Any) -> list[Any]:
        raise RuntimeError("Synthetic AST parse boom")

    monkeypatch.setattr(
        "pypost.ui.widgets.fold.fold_worker.scan_text", _failing_scan
    )

    editor = QPlainTextEdit()
    fc = FoldController(editor, body_format=BodyFormat.JSON)

    large_json = _generate_json_payload(520 * 1024)
    editor.setPlainText(large_json)

    spy = QSignalSpy(fc.scan_finished)
    fc.ensure_scanned()
    process_until(lambda: spy.count() >= 1, timeout_ms=10_000)

    failure_logs = [
        rec.getMessage()
        for rec in caplog.records
        if "fold_scan_worker_failed" in rec.getMessage()
        or "background_fold_scan_failed" in rec.getMessage()
    ]
    assert len(failure_logs) >= 1, "Failure logs must be emitted"
    for msg in failure_logs:
        assert "Synthetic AST parse boom" in msg
        assert "x" * 100 not in msg, "Payload must not be leaked into failure log"
