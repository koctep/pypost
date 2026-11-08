"""Tests for background worker thread formatting for medium-size JSON response masking.

Verifies PYPOST-1396 / PYPOST-1312 requirements:
- Threshold boundary dispatch:
    - Small payloads (< 50 KB): synchronous formatting path.
    - Medium payloads (50 KB - 100 KB): background ResponseMaskWorker dispatch.
    - Large payloads (> 100 KB): bypass pretty-printing and masking overhead.
- ResponseMaskWorker QThread lifecycle, signals, and thread isolation off the UI thread.
- Formatting and token span equivalence between synchronous and background formatting.
- Interactive click-to-reveal toggling on background-formatted documents.
- Preemption and cancellation: obsolete in-flight tasks cancelled on rapid successive responses.
- Clean cancellation and view clearing on clear_body().
- Graceful error fallback for malformed JSON without application crashes or hangs.
- Observability and zero secret leakage in logs.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject, QThread
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from pypost.models.response import ResponseData
from pypost.ui.widgets import response_view
from pypost.ui.widgets.response_mask_controller import (
    MaskedTokenSpan,
    format_masked_json,
)
from pypost.ui.widgets.response_mask_worker import ResponseMaskWorker
from pypost.ui.widgets.response_view import (
    LARGE_DOC_CHAR_THRESHOLD,
    ResponseView,
)
from tests.helpers.process_until import process_until


pytestmark = pytest.mark.timeout(30)

_EXPECTED_MEDIUM_THRESHOLD = 50 * 1024
_EXPECTED_LARGE_THRESHOLD = 100 * 1024
_SECRET_KEY = "super_secret_payload_token_xyz"


def _generate_json_payload(target_bytes: int, secret: str = _SECRET_KEY) -> str:
    """Generate a syntactically valid JSON document of approximately target_bytes."""
    item_estimate = 160
    count = max(1, target_bytes // item_estimate)
    items: list[dict[str, Any]] = [
        {
            "id": idx,
            "name": f"item_{idx}",
            "token": secret if idx % 5 == 0 else f"token_value_{idx}",
            "summary": "x" * 60,
            "active": True,
        }
        for idx in range(count)
    ]
    rendered = json.dumps({"items": items}, indent=2)
    if len(rendered) < target_bytes:
        diff = target_bytes - len(rendered)
        items[-1]["summary"] = "x" * (60 + diff)
        rendered = json.dumps({"items": items}, indent=2)
    return rendered


class TestResponseMaskWorkerContract:
    """Contract and unit verification for ResponseMaskWorker."""

    def test_worker_class_definition_and_lifecycle(self) -> None:
        """ResponseMaskWorker must exist, subclass QThread, and declare expected signals."""
        assert ResponseMaskWorker is not None, (
            "ResponseMaskWorker must be implemented in pypost.ui.widgets.response_mask_worker"
        )
        assert issubclass(
            ResponseMaskWorker, QThread
        ), "ResponseMaskWorker must subclass QThread for Qt event loop integration"
        assert issubclass(
            ResponseMaskWorker, QObject
        ), "ResponseMaskWorker must be a QObject subclass"

        assert hasattr(ResponseMaskWorker, "formatting_completed"), (
            "ResponseMaskWorker must declare formatting_completed = Signal(int, str, list)"
        )
        assert hasattr(ResponseMaskWorker, "formatting_failed"), (
            "ResponseMaskWorker must declare formatting_failed = Signal(int, str)"
        )
        assert hasattr(ResponseMaskWorker, "_LIVE_WORKERS"), (
            "ResponseMaskWorker must declare _LIVE_WORKERS ClassVar to prevent premature C++ GC"
        )

        worker = ResponseMaskWorker(
            generation=1,
            raw_body='{"test": 1}',
            hidden_fields=["token"],
            indent=2,
        )
        try:
            assert hasattr(worker, "requestInterruption"), (
                "ResponseMaskWorker must support cooperative requestInterruption"
            )
            assert hasattr(worker, "isInterruptionRequested"), (
                "ResponseMaskWorker must support isInterruptionRequested"
            )
            assert not worker.isInterruptionRequested()
        finally:
            worker.deleteLater()

    def test_worker_off_thread_execution_and_signal_emission(
        self, qapp: QApplication
    ) -> None:
        """Worker must parse and format off the main UI thread and emit completion signal."""
        assert ResponseMaskWorker is not None, "ResponseMaskWorker must be implemented"

        payload = _generate_json_payload(65 * 1024)
        worker = ResponseMaskWorker(
            generation=42,
            raw_body=payload,
            hidden_fields=["token"],
            indent=2,
        )

        main_thread = QApplication.instance().thread()
        completed_spy = QSignalSpy(worker.formatting_completed)
        failed_spy = QSignalSpy(worker.formatting_failed)
        delivered_thread: list[QThread] = []

        def on_completed(generation: int, formatted: str, spans: list[MaskedTokenSpan]) -> None:
            delivered_thread.append(QThread.currentThread())

        worker.formatting_completed.connect(on_completed)
        worker.start()

        process_until(lambda: completed_spy.count() >= 1, timeout_ms=10_000)
        worker.wait(2000)

        assert failed_spy.count() == 0, "formatting_failed should not be emitted on valid JSON"
        assert completed_spy.count() == 1, "formatting_completed must be emitted once"
        args = completed_spy.at(0)
        gen, formatted_text, spans = args[0], args[1], args[2]

        assert gen == 42, f"Expected generation 42, got {gen}"
        assert '"token": "***"' in formatted_text, "Sensitive tokens must be masked in output"
        assert len(spans) > 0, "Worker must return discovered MaskedTokenSpan objects"
        assert delivered_thread[0] == main_thread, "Signal slot must deliver on main UI thread"
        assert worker.thread() != worker, "Worker execution thread must differ from main thread"

    def test_worker_cooperative_interruption(self, qapp: QApplication) -> None:
        """Worker must abort without emitting completion signal when interrupted."""
        assert ResponseMaskWorker is not None, "ResponseMaskWorker must be implemented"

        payload = _generate_json_payload(75 * 1024)
        worker = ResponseMaskWorker(
            generation=7,
            raw_body=payload,
            hidden_fields=["token"],
            indent=2,
        )

        completed_spy = QSignalSpy(worker.formatting_completed)
        worker.requestInterruption()
        worker.start()

        worker.wait(2000)
        assert completed_spy.count() == 0, (
            "Interrupted worker must not emit formatting_completed signal"
        )

    def test_worker_malformed_json_emits_failure(self, qapp: QApplication) -> None:
        """Malformed JSON must trigger formatting_failed signal with raw body."""
        assert ResponseMaskWorker is not None, "ResponseMaskWorker must be implemented"

        corrupt_body = '{"items": [{"token": "secret"},' + (" " * 60000) + "corrupted_syntax"
        worker = ResponseMaskWorker(
            generation=99,
            raw_body=corrupt_body,
            hidden_fields=["token"],
            indent=2,
        )

        completed_spy = QSignalSpy(worker.formatting_completed)
        failed_spy = QSignalSpy(worker.formatting_failed)

        worker.start()
        process_until(lambda: failed_spy.count() >= 1, timeout_ms=10_000)
        worker.wait(2000)

        assert completed_spy.count() == 0, "Completed signal must not fire on malformed JSON"
        assert failed_spy.count() == 1, "formatting_failed must be emitted for malformed JSON"
        gen, returned_body = failed_spy.at(0)[0], failed_spy.at(0)[1]
        assert gen == 99
        assert returned_body == corrupt_body


class TestResponseViewMaskWorkerIntegration:
    """Integration verification of ResponseView operating bands and worker orchestration."""

    def test_threshold_constants_and_dispatch_boundaries(
        self, qapp: QApplication
    ) -> None:
        """ResponseView must route payloads through synchronous, worker, and bypass paths."""
        assert hasattr(response_view, "MEDIUM_DOC_CHAR_THRESHOLD"), (
            "response_view module must define MEDIUM_DOC_CHAR_THRESHOLD constant"
        )
        assert response_view.MEDIUM_DOC_CHAR_THRESHOLD == _EXPECTED_MEDIUM_THRESHOLD, (
            f"MEDIUM_DOC_CHAR_THRESHOLD must be {_EXPECTED_MEDIUM_THRESHOLD}"
        )
        assert LARGE_DOC_CHAR_THRESHOLD == _EXPECTED_LARGE_THRESHOLD, (
            f"LARGE_DOC_CHAR_THRESHOLD must be {_EXPECTED_LARGE_THRESHOLD}"
        )

        view = ResponseView()
        try:
            # 1. Small payload (< 50 KB): must format synchronously without background worker
            small_json = _generate_json_payload(20 * 1024)
            assert len(small_json) < _EXPECTED_MEDIUM_THRESHOLD
            resp_small = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=small_json,
                elapsed_time=0.05,
                size=len(small_json),
            )
            view.display_response(resp_small, hidden_fields=["token"])
            assert '"token": "***"' in view.body_view.toPlainText(), (
                "Small payload must be masked synchronously"
            )
            assert getattr(view, "_mask_worker", None) is None, (
                "Small payload (< 50 KB) must not launch background worker"
            )
            assert len(view.mask_controller.spans()) > 0, "Spans must be registered immediately"

            # 2. Medium payload (50 KB - 100 KB): must dispatch to ResponseMaskWorker
            medium_json = _generate_json_payload(70 * 1024)
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json) <= _EXPECTED_LARGE_THRESHOLD
            resp_medium = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json,
                elapsed_time=0.15,
                size=len(medium_json),
            )
            view.display_response(resp_medium, hidden_fields=["token"])

            worker = getattr(view, "_mask_worker", None)
            assert worker is not None, (
                "Medium payload (50 KB - 100 KB) with hidden_fields must launch ResponseMaskWorker"
            )
            assert isinstance(worker, ResponseMaskWorker), (
                f"_mask_worker must be an instance of ResponseMaskWorker, got {type(worker)}"
            )

            # Wait for background completion
            process_until(
                lambda: getattr(view, "_mask_worker", None) is None,
                timeout_ms=10_000,
            )
            assert '"token": "***"' in view.body_view.toPlainText(), (
                "Medium payload must be formatted with masking after background completion"
            )
            assert len(view.mask_controller.spans()) > 0, (
                "Spans must be applied to mask_controller upon worker completion"
            )

            # 3. Large payload (> 100 KB): must bypass formatting and masking
            large_json = _generate_json_payload(110 * 1024)
            assert len(large_json) > _EXPECTED_LARGE_THRESHOLD
            resp_large = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=large_json,
                elapsed_time=0.35,
                size=len(large_json),
            )
            view.display_response(resp_large, hidden_fields=["token"])
            assert getattr(view, "_mask_worker", None) is None, (
                "Large payload (> 100 KB) must not launch background worker"
            )
            assert view.body_view.toPlainText() == large_json, (
                "Large payload must display raw body without pretty-printing"
            )
            assert len(view.mask_controller.spans()) == 0, (
                "Large payload must bypass mask token indexing"
            )
        finally:
            view.close()

    def test_medium_payload_formatting_and_masking_equivalence(
        self, qapp: QApplication
    ) -> None:
        """Background formatted document and spans must match format_masked_json exactly."""
        view = ResponseView()
        try:
            medium_json = _generate_json_payload(70 * 1024)
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json) <= _EXPECTED_LARGE_THRESHOLD
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json,
                elapsed_time=0.1,
                size=len(medium_json),
            )
            view.display_response(resp, hidden_fields=["token"])

            worker = getattr(view, "_mask_worker", None)
            assert worker is not None, "Worker must be dispatched for medium payload"

            process_until(
                lambda: getattr(view, "_mask_worker", None) is None,
                timeout_ms=10_000,
            )

            expected_text, expected_spans = format_masked_json(
                medium_json, ["token"], indent=view.indent_size
            )
            actual_text = view.body_view.toPlainText()
            actual_spans = view.mask_controller.spans()

            assert actual_text == expected_text, (
                "Background formatted text must match format_masked_json output "
                "character-for-character"
            )
            assert len(actual_spans) == len(expected_spans), (
                f"Span count mismatch: expected {len(expected_spans)}, got {len(actual_spans)}"
            )
            for idx, (actual, expected) in enumerate(zip(actual_spans, expected_spans)):
                assert actual.start_pos == expected.start_pos, f"Span {idx} start_pos mismatch"
                assert actual.end_pos == expected.end_pos, f"Span {idx} end_pos mismatch"
                assert actual.raw_value == expected.raw_value, f"Span {idx} raw_value mismatch"
                assert actual.masked_value == expected.masked_value, (
                    f"Span {idx} masked_value mismatch"
                )
        finally:
            view.close()

    def test_click_to_reveal_on_async_masked_payload(
        self, qapp: QApplication
    ) -> None:
        """Click-to-reveal toggling must function identically on background-formatted views."""
        view = ResponseView()
        try:
            secret = "classified_token_xyz"
            medium_json = _generate_json_payload(65 * 1024, secret=secret)
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json) <= _EXPECTED_LARGE_THRESHOLD
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json,
                elapsed_time=0.1,
                size=len(medium_json),
            )
            view.display_response(resp, hidden_fields=["token"])

            worker = getattr(view, "_mask_worker", None)
            assert worker is not None, "Worker must be dispatched for medium payload"

            process_until(
                lambda: getattr(view, "_mask_worker", None) is None,
                timeout_ms=10_000,
            )

            spans = view.mask_controller.spans()
            assert len(spans) > 0, "Masked spans must be present after background formatting"
            span = spans[0]
            assert not span.is_revealed, "Span should initially be unrevealed"

            # Toggle reveal
            handled = view.mask_controller.handle_click(span.start_pos + 1)
            assert handled is True, "handle_click must succeed on masked span"
            assert span.is_revealed is True, "Span state must be revealed"
            assert secret in view.body_view.toPlainText(), (
                "Secret must be present in document after reveal"
            )

            # Toggle re-mask
            remasked = view.mask_controller.handle_click(span.start_pos + 1)
            assert remasked is True, "handle_click must succeed on revealed span"
            assert span.is_revealed is False, "Span state must revert to unrevealed"
            assert '"***"' in view.body_view.toPlainText(), "Placeholder must be restored"
        finally:
            view.close()

    def test_preemption_and_cancellation_on_rapid_responses(
        self, qapp: QApplication
    ) -> None:
        """Successive rapid responses must cancel prior worker and discard stale generation."""
        view = ResponseView()
        try:
            medium_json_1 = _generate_json_payload(65 * 1024, secret="first_secret")
            medium_json_2 = _generate_json_payload(75 * 1024, secret="second_secret")
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json_1) <= _EXPECTED_LARGE_THRESHOLD
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json_2) <= _EXPECTED_LARGE_THRESHOLD

            resp_1 = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json_1,
                elapsed_time=0.1,
                size=len(medium_json_1),
            )
            resp_2 = ResponseData(
                status_code=201,
                headers={"Content-Type": "application/json"},
                body=medium_json_2,
                elapsed_time=0.2,
                size=len(medium_json_2),
            )

            # Dispatch first response
            view.display_response(resp_1, hidden_fields=["token"])
            worker_1 = getattr(view, "_mask_worker", None)
            gen_1 = getattr(view, "_mask_format_generation", 0)
            assert worker_1 is not None, "Worker 1 must be dispatched"

            # Dispatch second response immediately before worker 1 completes
            view.display_response(resp_2, hidden_fields=["token"])
            worker_2 = getattr(view, "_mask_worker", None)
            gen_2 = getattr(view, "_mask_format_generation", 0)

            assert gen_2 > gen_1, "Generation counter must increment on new response"
            assert worker_1.isInterruptionRequested(), (
                "Worker 1 must be interrupted cooperatively"
            )
            assert worker_2 is not worker_1, "Worker 2 must replace Worker 1"

            # Wait for worker 2 to finish
            process_until(
                lambda: getattr(view, "_mask_worker", None) is None,
                timeout_ms=10_000,
            )

            final_text = view.body_view.toPlainText()
            assert view.status_label.text() == "Status: 201"
            expected_text_2, _ = format_masked_json(
                medium_json_2, ["token"], indent=view.indent_size
            )
            assert final_text == expected_text_2, (
                "Final rendered content must belong exclusively to response 2"
            )
        finally:
            view.close()

    def test_clear_body_cancels_in_flight_worker(
        self, qapp: QApplication
    ) -> None:
        """clear_body() must interrupt running worker and prevent late document rendering."""
        view = ResponseView()
        try:
            medium_json = _generate_json_payload(70 * 1024)
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json) <= _EXPECTED_LARGE_THRESHOLD
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json,
                elapsed_time=0.1,
                size=len(medium_json),
            )
            view.display_response(resp, hidden_fields=["token"])

            worker = getattr(view, "_mask_worker", None)
            assert worker is not None, "Worker must be running"
            gen_before = getattr(view, "_mask_format_generation", 0)

            # Call clear_body while worker is active
            view.clear_body()

            assert worker.isInterruptionRequested(), "clear_body must interrupt running worker"
            assert getattr(view, "_mask_worker", None) is None, (
                "_mask_worker reference must be cleared"
            )
            assert getattr(view, "_mask_format_generation", 0) > gen_before, (
                "Generation must be incremented to invalidate pending emissions"
            )
            assert view.body_view.toPlainText() == "", "body_view must be empty after clear_body"

            # Give thread time to finish and ensure document remains empty
            worker.wait(1000)
            assert view.body_view.toPlainText() == "", (
                "Late completion must not populate cleared body_view"
            )
        finally:
            view.close()

    def test_malformed_json_in_medium_payload_falls_back_to_raw(
        self, qapp: QApplication
    ) -> None:
        """Malformed JSON in medium payload must safely fall back to raw body text."""
        view = ResponseView()
        try:
            corrupted_json = '{"items": [{"token": "sec"},' + (" " * 60000) + "{bad_syntax"
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(corrupted_json) <= _EXPECTED_LARGE_THRESHOLD
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=corrupted_json,
                elapsed_time=0.1,
                size=len(corrupted_json),
            )
            view.display_response(resp, hidden_fields=["token"])

            worker = getattr(view, "_mask_worker", None)
            assert worker is not None, "Worker must be dispatched for medium malformed payload"

            # Wait for failure handling
            process_until(
                lambda: getattr(view, "_mask_worker", None) is None,
                timeout_ms=10_000,
            )

            assert view.body_view.toPlainText() == corrupted_json, (
                "Malformed JSON must fall back to displaying raw unmasked body"
            )
            assert len(view.mask_controller.spans()) == 0, (
                "No spans should be registered on fallback"
            )
        finally:
            view.close()

    def test_observability_logging_and_zero_secret_leakage(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Worker lifecycle logs must capture structured metrics and never leak secrets."""
        mock_metrics = MagicMock()
        view = ResponseView(metrics=mock_metrics)
        try:
            secret = "ultra_sensitive_api_secret_9999"
            medium_json = _generate_json_payload(65 * 1024, secret=secret)
            assert _EXPECTED_MEDIUM_THRESHOLD <= len(medium_json) <= _EXPECTED_LARGE_THRESHOLD
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=medium_json,
                elapsed_time=0.1,
                size=len(medium_json),
            )

            with caplog.at_level(logging.DEBUG):
                view.display_response(resp, hidden_fields=["token"])
                worker = getattr(view, "_mask_worker", None)
                assert worker is not None, "Worker must be dispatched for medium payload"
                process_until(
                    lambda: getattr(view, "_mask_worker", None) is None,
                    timeout_ms=10_000,
                )

            messages = [record.message for record in caplog.records]
            assert any("response_masking_worker_dispatched" in m for m in messages), (
                "Worker dispatch event must be logged"
            )
            assert any("response_mask_worker_started" in m for m in messages), (
                "Worker start event must be logged"
            )
            assert any("response_mask_worker_completed" in m for m in messages), (
                "Worker completion with duration and span count must be logged"
            )
            assert any("response_masking_async_completed" in m for m in messages), (
                "Async formatting completion event must be logged"
            )

            # Telemetry verification
            mock_metrics.track_hidden_value_mask_applied.assert_called_once_with("gui_response")

            # Zero secret leakage verification
            assert not any(secret in record.message for record in caplog.records), (
                "Raw secret must never be emitted in any log record"
            )
            assert not any(medium_json in record.message for record in caplog.records), (
                "Full unmasked payload body must never be emitted in logs"
            )
        finally:
            view.close()

    def test_observability_cancellation_logs_and_zero_leakage(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Worker cancellation and preemption must log structured events without leaking secrets."""
        view = ResponseView()
        try:
            secret_1 = "secret_payload_alpha_1111"
            secret_2 = "secret_payload_beta_2222"
            payload_1 = _generate_json_payload(65 * 1024, secret=secret_1)
            payload_2 = _generate_json_payload(70 * 1024, secret=secret_2)

            resp_1 = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=payload_1,
                elapsed_time=0.1,
                size=len(payload_1),
            )
            resp_2 = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=payload_2,
                elapsed_time=0.1,
                size=len(payload_2),
            )

            with caplog.at_level(logging.DEBUG):
                view.display_response(resp_1, hidden_fields=["token"])
                worker_1 = getattr(view, "_mask_worker", None)
                assert worker_1 is not None

                # Rapid successive dispatch preempting worker_1
                view.display_response(resp_2, hidden_fields=["token"])
                process_until(
                    lambda: getattr(view, "_mask_worker", None) is None,
                    timeout_ms=10_000,
                )

            messages = [record.message for record in caplog.records]
            assert any("response_mask_worker_interruption_requested" in m for m in messages), (
                "Worker interruption request must be logged"
            )
            assert not any(secret_1 in record.message for record in caplog.records), (
                "Preempted task secret must not leak in logs"
            )
            assert not any(secret_2 in record.message for record in caplog.records), (
                "Active task secret must not leak in logs"
            )
        finally:
            view.close()

    def test_observability_failure_warning_logs_and_zero_leakage(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Worker formatting failure must emit structured warnings with zero sensitive leakage."""
        view = ResponseView()
        try:
            secret = "secret_inside_corrupted_json"
            corrupted = (
                f'{{"token": "{secret}", "items": ['
                + (" " * 60000)
                + "malformed_json_syntax"
            )
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=corrupted,
                elapsed_time=0.1,
                size=len(corrupted),
            )

            with caplog.at_level(logging.DEBUG):
                view.display_response(resp, hidden_fields=["token"])
                process_until(
                    lambda: getattr(view, "_mask_worker", None) is None,
                    timeout_ms=10_000,
                )

            warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
            warning_messages = [r.message for r in warning_records]

            assert any("response_mask_worker_failed" in m for m in warning_messages), (
                "Worker formatting failure must be logged at WARNING level"
            )
            assert any(
                "response_masking_async_failed_fallback" in m for m in warning_messages
            ), "Fallback to raw display on worker failure must be logged at WARNING level"

            assert not any(secret in r.message for r in caplog.records), (
                "Secret inside failed payload must not leak in any log level"
            )
            assert not any(corrupted in r.message for r in caplog.records), (
                "Corrupted payload body must not leak in any log level"
            )
        finally:
            view.close()
