"""Real-file cancellation latency regressions for PYPOST-1267.

Fixtures are local UTF-8 files; timing excludes fixture creation and startup.
Observers delegate all reads and decoding, and never manufacture checkpoints.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import sys
import threading
import time
from typing import Any, TextIO

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.qt.collection_import_parse_worker import CollectionImportParseWorker
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(150)

_MIN_BYTES = 16 * 1024 * 1024
_GATE_SECONDS = 60
_CLEANUP_MS = 80000


class _ReadObserver:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self.characters = 0
        self.reads = 0
        self.closed = False

    def read(self, size: int = -1) -> str:
        result = self.stream.read(size)
        self.characters += len(result)
        self.reads += 1
        return result

    def __enter__(self) -> _ReadObserver:
        self.stream.__enter__()
        return self

    def __exit__(self, *args: Any) -> Any:
        try:
            return self.stream.__exit__(*args)
        finally:
            self.closed = True

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)


def _lexical_position() -> int | None:
    # Observe the real scanner's live frame, including helpers introduced by Step 4.
    # Inspect frames without coupling the observer to decoder helper imports.
    frame = sys._getframe(1)
    while frame is not None:
        module = frame.f_globals.get("__name__", "")
        name = frame.f_code.co_name.lower()
        if module.startswith("yaml.") and name in {
            "scan_plain", "scan_flow_scalar_non_spaces", "scan_flow_scalar_spaces",
        }:
            loader = frame.f_locals.get("self")
            length = frame.f_locals.get("length", 0)
            return loader.index + (length if isinstance(length, int) else 0)
        if module == "pypost.core.collection_import_decode" and (
            "string" in name or "scanstr" in name
        ):
            for key in ("end", "pos", "index", "position"):
                position = frame.f_locals.get(key)
                if isinstance(position, int):
                    return position
        frame = frame.f_back
    return None


def _at_yaml_peek_checkpoint() -> bool:
    frame = sys._getframe(1)
    while frame is not None:
        if (frame.f_globals.get("__name__") == "pypost.core.collection_import_decode"
                and frame.f_code.co_name == "peek"):
            return True
        frame = frame.f_back
    return False


def _write_fixture(path: Path, format_name: str, shape: str) -> int:
    # All data lives in retained collection.description fields.
    if shape == "bundle":
        count = _MIN_BYTES // 1024 + 1
        value = "x" * 1024
        if format_name == "json":
            record = '{"name":"Record","description":"' + value + '"}'
            text = "[" + ",".join([record] * count) + "]"
        else:
            record = '- name: Record\n  description: "' + value + '"\n'
            text = record * count
    else:
        value = "x" * _MIN_BYTES
        if format_name == "json":
            text = '{"name":"Large","description":"' + value + '"}'
        elif shape == "plain":
            text = "name: Large\ndescription: " + value + "\n"
        else:
            text = 'name: Large\ndescription: "' + value + '"\n'
    path.write_text(text, encoding="utf-8")
    size = path.stat().st_size
    assert size >= _MIN_BYTES
    return size


def _run_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    record_property: Callable[[str, Any], None],
    phase: str,
    format_name: str,
    shape: str,
) -> None:
    suffix = ".yaml" if format_name == "yaml" else ".json"
    path = tmp_path / ("large" + suffix)
    size = _write_fixture(path, format_name, shape)
    for key, value in {
        "fixture_bytes": size, "shape": shape, "format": format_name,
        "phase": phase, "latency_limit_ms": 1000,
    }.items():
        record_property(key, value)

    streams: list[_ReadObserver] = []
    real_open = Path.open

    def observe_open(selected: Path, *args: Any, **kwargs: Any) -> Any:
        stream = real_open(selected, *args, **kwargs)
        if selected != path:
            return stream
        observed = _ReadObserver(stream)
        streams.append(observed)
        return observed

    monkeypatch.setattr(Path, "open", observe_open)
    reached = threading.Event()
    release = threading.Event()
    finished = threading.Event()
    last_read = -1
    same_read_callbacks = 0
    lexical_callbacks = 0
    position = -1
    gated_position = -1
    gated_characters = -1
    validated: list[int] = []

    def reader(
        selected: Path, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        def forward(done: int, total: int) -> None:
            nonlocal last_read, same_read_callbacks, lexical_callbacks, position
            nonlocal gated_position, gated_characters
            scan_position = _lexical_position()
            if scan_position is not None:
                position = scan_position
            if (done, total) != (0, 0):
                validated.append(done)
            # The real worker checks first. Cancellation is requested only AFTER return.
            on_progress(done, total)
            if (done, total) != (0, 0) or reached.is_set() or not streams:
                return
            stream = streams[-1]
            if phase == "loading":
                if stream.reads == last_read:
                    same_read_callbacks += 1
                else:
                    last_read = stream.reads
                    same_read_callbacks = 1
                eligible = (
                    0 < stream.characters < size
                    and same_read_callbacks == 2
                    and not stream.closed
                )
            else:
                eligible = False
                if stream.closed and stream.characters == size and scan_position is not None:
                    if format_name == "json" or _at_yaml_peek_checkpoint():
                        lexical_callbacks += 1
                        eligible = lexical_callbacks == 256
            if eligible:
                gated_position = position
                gated_characters = stream.characters
                reached.set()
                assert release.wait(5), "test controller did not release active-phase gate"

        try:
            return load_collection_import_candidates(selected, on_progress=forward)
        finally:
            finished.set()

    worker = CollectionImportParseWorker(path, reader)
    cancelled: list[bool] = []
    completed: list[Any] = []
    failed: list[Any] = []
    direct = Qt.ConnectionType.DirectConnection
    worker.parse_cancelled.connect(lambda: cancelled.append(True), direct)
    worker.parse_completed.connect(lambda *args: completed.append(args), direct)
    worker.parse_failed.connect(failed.append, direct)
    worker.start()
    try:
        deadline = time.monotonic() + _GATE_SECONDS
        while not reached.is_set() and not finished.is_set() and time.monotonic() < deadline:
            reached.wait(0.02)
        assert reached.is_set(), (
            f"missing active-{phase} cancellation checkpoint: {format_name}/{shape}; "
            "the production reader consumed or decoded the full file before checking"
        )
        assert validated == [], "gate must precede collection validation"
        started = time.monotonic()
        worker.requestInterruption()
        release.set()
        stopped = worker.wait(1000)
        elapsed_ms = (time.monotonic() - started) * 1000
        record_property("cancellation_latency_ms", round(elapsed_ms, 3))
        assert stopped and elapsed_ms <= 1000, f"worker stop took {elapsed_ms:.3f} ms"
        assert cancelled == [True]
        assert completed == []
        assert failed == []
        assert validated == []
        assert all(stream.closed for stream in streams), "cancelled import leaked its file"
        if phase == "loading":
            assert gated_characters < streams[-1].characters < size, (
                "cancellation must include a real chunk read after gate release, before EOF"
            )
        else:
            assert position > gated_position, (
                "cancellation must include lexical work after release, before its next checkpoint"
            )
    finally:
        release.set()
        worker.requestInterruption()
        assert worker.wait(_CLEANUP_MS), "real-file parse worker cleanup exceeded its budget"


@pytest.mark.parametrize("format_name", ["json", "yaml", "fallback"])
def test_cancellation_during_real_file_loading(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    record_property: Callable[[str, Any], None], format_name: str,
) -> None:
    _run_case(tmp_path, monkeypatch, record_property, "loading", format_name, "bundle")


@pytest.mark.parametrize(
    ("format_name", "shape"),
    [
        ("json", "quoted"), ("json", "bundle"),
        ("yaml", "plain"), ("yaml", "quoted"), ("yaml", "bundle"),
        ("fallback", "plain"), ("fallback", "quoted"), ("fallback", "bundle"),
    ],
)
def test_cancellation_during_active_lexical_scanning(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    record_property: Callable[[str, Any], None], format_name: str, shape: str,
) -> None:
    _run_case(tmp_path, monkeypatch, record_property, "decoding", format_name, shape)
