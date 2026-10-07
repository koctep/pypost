"""Reader contract regressions for background collection import (PYPOST-1266)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.qt.collection_import_parse_worker import (
    CollectionImportParseWorker,
    ReadImportFile,
)
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)


def _reader_for_shape(shape: str, processed: list[int]) -> ReadImportFile:
    def read(
        path: Path, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        assert path == Path("/dummy/import.json")
        for record in range(1, 4):
            processed.append(record)
            on_progress(record, 3)
        return [Collection(id="c1", name="C1")], ["record warning"]

    def positional_or_keyword(
        path: Path, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        return read(path, on_progress=on_progress)

    def forwarding(
        path: Path, **kwargs: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        return read(path, on_progress=kwargs["on_progress"])

    class Reader:
        def __call__(
            self, path: Path, *, on_progress: Callable[[int, int], None]
        ) -> tuple[list[Collection], list[str]]:
            return read(path, on_progress=on_progress)

    class OpaqueReader(Reader):
        __signature__ = "unavailable"

    return {
        "keyword_only": read,
        "positional_or_keyword": positional_or_keyword,
        "bound_method": Reader().__call__,
        "callable_object": Reader(),
        "keyword_forwarding": forwarding,
        "opaque_callable": OpaqueReader(),
    }[shape]


def test_opaque_reader_observes_cancellation_at_first_checkpoint(qapp: QApplication) -> None:
    processed: list[int] = []

    class OpaqueReader:
        # Real call compatibility must not depend on introspection metadata.
        __signature__ = "unavailable"

        def __call__(
            self,
            path: Path,
            *,
            on_progress: Callable[[int, int], None] | None = None,
        ) -> tuple[list[Collection], list[str]]:
            assert path == Path("/dummy/import.json")
            for record in range(1, 4):
                processed.append(record)
                if on_progress is not None:
                    on_progress(record, 3)
            return [Collection(id="c1", name="C1")], []

    worker = CollectionImportParseWorker(Path("/dummy/import.json"), OpaqueReader())
    progress: list[tuple[int, int]] = []
    cancelled: list[bool] = []
    completed: list[tuple[list[Collection], list[str]]] = []
    failed: list[Exception] = []

    def interrupt_at_checkpoint(done: int, total: int) -> None:
        progress.append((done, total))
        worker.requestInterruption()

    # Direct delivery interrupts inside _emit_progress before its cancellation check.
    worker.parse_progress.connect(interrupt_at_checkpoint, Qt.ConnectionType.DirectConnection)
    worker.parse_cancelled.connect(
        lambda: cancelled.append(True), Qt.ConnectionType.DirectConnection
    )
    worker.parse_completed.connect(
        lambda cols, errors: completed.append((cols, errors)), Qt.ConnectionType.DirectConnection
    )
    worker.parse_failed.connect(failed.append, Qt.ConnectionType.DirectConnection)
    worker.start()
    try:
        assert worker.wait(5000), "opaque reader worker did not finish"
        assert processed == [1], "reader bypassed the supplied cancellation checkpoint"
        assert progress == [(1, 3)]
        assert cancelled == [True]
        assert completed == []
        assert failed == []
    finally:
        worker.requestInterruption()
        assert worker.wait(5000), "opaque reader worker cleanup did not finish"


@pytest.mark.parametrize("cancel_at", [None, 1, 2])
def test_production_json_reader_contract(
    qapp: QApplication, tmp_path: Path, cancel_at: int | None
) -> None:
    path = tmp_path / "collections.json"
    path.write_text(
        json.dumps(
            [
                {"id": "c1", "name": "First"},
                {"id": "invalid", "requests": []},
                {"id": "c3", "name": "Third"},
            ]
        ),
        encoding="utf-8",
    )
    progress, cancelled, completed, failed = _run_reader(
        load_collection_import_candidates, path, cancel_at
    )
    assert failed == []
    if cancel_at is None:
        assert progress == [(1, 3), (2, 3), (3, 3)]
        assert cancelled == []
        assert len(completed) == 1
        collections, errors = completed[0]
        assert [(col.id, col.name) for col in collections] == [("c1", "First"), ("c3", "Third")]
        assert len(errors) == 1
        assert "name" in errors[0]
    else:
        assert progress == [(done, 3) for done in range(1, cancel_at + 1)]
        assert cancelled == [True]
        assert completed == []


def _run_reader(
    reader: ReadImportFile, path: Path, cancel_at: int | None
) -> tuple[
    list[tuple[int, int]],
    list[bool],
    list[tuple[list[Collection], list[str]]],
    list[Exception],
]:
    worker = CollectionImportParseWorker(path, reader)
    progress: list[tuple[int, int]] = []
    cancelled: list[bool] = []
    completed: list[tuple[list[Collection], list[str]]] = []
    failed: list[Exception] = []

    def checkpoint(done: int, total: int) -> None:
        progress.append((done, total))
        if done == cancel_at:
            worker.requestInterruption()

    worker.parse_progress.connect(checkpoint, Qt.ConnectionType.DirectConnection)
    worker.parse_cancelled.connect(
        lambda: cancelled.append(True), Qt.ConnectionType.DirectConnection
    )
    worker.parse_completed.connect(
        lambda cols, errors: completed.append((cols, errors)), Qt.ConnectionType.DirectConnection
    )
    worker.parse_failed.connect(failed.append, Qt.ConnectionType.DirectConnection)
    worker.start()
    try:
        assert worker.wait(5000), "reader worker did not finish"
        return progress, cancelled, completed, failed
    finally:
        worker.requestInterruption()
        assert worker.wait(5000), "reader worker cleanup did not finish"


@pytest.mark.parametrize(
    "shape",
    [
        "keyword_only",
        "positional_or_keyword",
        "bound_method",
        "callable_object",
        "keyword_forwarding",
        "opaque_callable",
    ],
)
@pytest.mark.parametrize("cancel_at", [None, 1])
def test_supported_reader_shapes(
    qapp: QApplication, shape: str, cancel_at: int | None
) -> None:
    processed: list[int] = []
    progress, cancelled, completed, failed = _run_reader(
        _reader_for_shape(shape, processed), Path("/dummy/import.json"), cancel_at
    )
    assert failed == []
    if cancel_at is None:
        assert processed == [1, 2, 3]
        assert progress == [(1, 3), (2, 3), (3, 3)]
        assert cancelled == []
        assert completed == [([Collection(id="c1", name="C1")], ["record warning"])]
    else:
        assert processed == [1]
        assert progress == [(1, 3)]
        assert cancelled == [True]
        assert completed == []
