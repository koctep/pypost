"""Focused tests for process_until timeout diagnostics (PYPOST-828)."""

from __future__ import annotations

import time

import pytest

from tests.helpers.process_until import (
    format_storage_async_timeout_detail,
    gateway_timeout_detail,
    process_until,
)

pytestmark = pytest.mark.timeout(30)


def test_format_storage_async_timeout_detail_omits_none_fields():
    assert format_storage_async_timeout_detail() == ""
    assert (
        format_storage_async_timeout_detail(is_busy=True, has_pending_work=False)
        == "busy=True pending=False"
    )
    assert (
        format_storage_async_timeout_detail(
            worker_running=True,
            worker_operation="load",
        )
        == "worker_running=True worker_operation=load"
    )


def test_gateway_timeout_detail_reads_busy_pending_and_worker():
    class FakeWorker:
        def isRunning(self) -> bool:
            return True

    class FakeGateway:
        _worker = FakeWorker()

        def is_busy(self) -> bool:
            return True

        def has_pending_work(self) -> bool:
            return False

    detail = gateway_timeout_detail(FakeGateway())
    assert detail() == "busy=True pending=False worker_running=True"

    class IdleGateway:
        _worker = None

        def is_busy(self) -> bool:
            return False

        def has_pending_work(self) -> bool:
            return False

    idle = gateway_timeout_detail(IdleGateway())
    assert idle() == "busy=False pending=False worker_running=False"


def test_process_until_default_timeout_message_is_neutral(qapp):
    with pytest.raises(AssertionError, match="predicate still false") as exc_info:
        process_until(lambda: False, timeout_ms=300)
    message = str(exc_info.value)
    assert "condition not met within 300ms" in message
    assert "wall-clock deadline" in message
    assert "load_completed" not in message
    assert "load_failed" not in message


def test_process_until_timeout_includes_busy_pending_detail(qapp):
    with pytest.raises(AssertionError, match=r"busy=True pending=False") as exc_info:
        process_until(
            lambda: False,
            timeout_ms=300,
            timeout_detail=lambda: format_storage_async_timeout_detail(
                is_busy=True,
                has_pending_work=False,
            ),
        )
    assert "condition not met within 300ms" in str(exc_info.value)


def test_process_until_timeout_includes_worker_only_detail(qapp):
    with pytest.raises(AssertionError, match=r"worker_running=True") as exc_info:
        process_until(
            lambda: False,
            timeout_ms=300,
            timeout_detail=lambda: format_storage_async_timeout_detail(
                worker_running=True,
            ),
        )
    message = str(exc_info.value)
    assert "busy=" not in message
    assert "pending=" not in message


def test_process_until_timeout_detail_failure_does_not_mask_timeout(qapp):
    def boom() -> str:
        raise RuntimeError("detail boom")

    with pytest.raises(AssertionError, match="timeout_detail failed") as exc_info:
        process_until(lambda: False, timeout_ms=300, timeout_detail=boom)
    message = str(exc_info.value)
    assert "condition not met within 300ms" in message
    assert "RuntimeError" in message


def test_process_until_does_not_call_timeout_detail_on_success(qapp):
    called = []

    def detail() -> str:
        called.append(True)
        return "should-not-appear"

    process_until(lambda: True, timeout_ms=300, timeout_detail=detail)
    assert called == []


def test_process_until_hang_defense_still_exits_near_deadline(qapp):
    started = time.monotonic()
    with pytest.raises(AssertionError, match="condition not met within 300ms"):
        process_until(lambda: False, timeout_ms=300)
    elapsed_s = time.monotonic() - started
    assert elapsed_s < 2.0, f"wait hung for {elapsed_s:.2f}s; expected ~0.3s fail"
