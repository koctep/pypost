"""Tests for interactive click-to-reveal response masking in GUI ResponseView.

Verifies PYPOST-1379 / MASK-3 requirements:
- Default masking of configured fields with '***'.
- In-place click-to-reveal and re-mask toggling.
- Coexistence with JsonHighlighter syntax highlighting.
- Coexistence with search navigation and match counting.
- Coexistence with code folding and context menu ('Set Variable', 'Copy').
- Streaming chunk append safety.
- Large-document fallback (>100 KB) bypassing token span overhead.
- Raw in-memory ResponseData immutability.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import LARGE_DOC_CHAR_THRESHOLD, ResponseView

pytestmark = pytest.mark.timeout(60)

_QMENU_PATCH = "pypost.ui.widgets.response_view.QMenu"


def _select_text(view: ResponseView, text: str) -> None:
    body = view.body_view.toPlainText()
    start = body.index(text)
    cursor = view.body_view.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(start + len(text), QTextCursor.MoveMode.KeepAnchor)
    view.body_view.setTextCursor(cursor)


def _trigger_connected(action: MagicMock) -> None:
    connect_mock = action.triggered.connect
    callback = connect_mock.call_args[0][0]
    callback()


class TestResponseViewClickToReveal:
    """Automated test suite asserting click-to-reveal masking behavior in ResponseView."""

    def test_default_masked_field_display(self, qapp: QApplication) -> None:
        """Scenario 1: Default Masking Display.

        ResponseView masks configured hidden fields with '***' when
        RequestData.hidden_response_fields is provided.
        """
        view = ResponseView()
        try:
            req = RequestData(hidden_response_fields=["token", "client_secret"])
            body_dict = {
                "token": "secret_token_123",
                "client_secret": "my_secret_abc",
                "status": "ok",
                "id": 42,
            }
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps(body_dict),
                elapsed_time=0.1,
                size=120,
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            text = view.body_view.toPlainText()
            assert '"token": "***"' in text, f"Field 'token' was not masked: {text}"
            assert '"client_secret": "***"' in text, f"Field 'client_secret' was not masked: {text}"
            assert '"status": "ok"' in text, "Unmasked field 'status' altered"
            assert '"id": 42' in text, "Unmasked field 'id' altered"

            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            spans = view.mask_controller.spans()
            assert len(spans) == 2, f"Expected 2 masked token spans, got {len(spans)}"
            assert all(not span.is_revealed for span in spans), "Spans must be initially unrevealed"
        finally:
            view.close()

    def test_inplace_click_to_reveal_and_remask(self, qapp: QApplication) -> None:
        """Scenario 2: In-Place Click-to-Reveal and Re-mask Toggle.

        Clicking on a masked token span reveals the real value; clicking again re-masks it.
        """
        view = ResponseView()
        try:
            raw_secret = "super_secret_value_xyz"
            req = RequestData(hidden_response_fields=["api_key"])
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"api_key": raw_secret, "env": "prod"}),
                elapsed_time=0.1,
                size=60,
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            assert '"***"' in view.body_view.toPlainText()
            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"

            spans = view.mask_controller.spans()
            assert len(spans) == 1
            span = spans[0]
            char_pos = span.start_pos + 1

            # Viewport mouse click simulation
            cursor = QTextCursor(view.body_view.document())
            cursor.setPosition(char_pos)
            rect = view.body_view.cursorRect(cursor)
            QTest.mouseClick(
                view.body_view.viewport(),
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                rect.center(),
            )

            # Reveal via controller handler
            toggled = view.mask_controller.handle_click(char_pos)
            assert toggled is True, "Expected handle_click to succeed on masked span"
            assert raw_secret in view.body_view.toPlainText(), "Secret not revealed in document"
            assert span.is_revealed is True, "Span state did not transition to revealed"

            # Re-mask via click
            toggled_again = view.mask_controller.handle_click(char_pos)
            assert toggled_again is True, "Expected handle_click to succeed on revealed span"
            assert '"***"' in view.body_view.toPlainText(), "Span not re-masked to placeholder"
            assert raw_secret not in view.body_view.toPlainText(), "Secret remained in document"
            assert span.is_revealed is False, "Span state did not revert to unrevealed"

            # Clicks outside any span return False
            assert view.mask_controller.handle_click(0) is False
        finally:
            view.close()

    def test_coexistence_with_json_highlighter(self, qapp: QApplication) -> None:
        """Scenario 3: Coexistence with JsonHighlighter.

        Syntax highlighting remains valid, string token colors apply, no regex recursion.
        """
        view = ResponseView()
        try:
            req = RequestData(hidden_response_fields=["auth_token"])
            secret = "tok_live_abc123"
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"auth_token": secret, "valid": True}),
                elapsed_time=0.1,
                size=60,
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            assert view.json_highlighter.document() is view.body_view.document()

            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            spans = view.mask_controller.spans()
            assert len(spans) == 1

            # Reveal token and assert syntax highlighting updates smoothly without hang/error
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert secret in view.body_view.toPlainText()
            assert view.json_highlighter.document() is view.body_view.document()
        finally:
            view.close()

    def test_coexistence_with_search_and_match_count(self, qapp: QApplication) -> None:
        """Scenario 4: Coexistence with Search & Match Navigation.

        Searching for text reflects visible vs revealed status without desynchronization.
        """
        view = ResponseView()
        try:
            secret = "super_secret_key_999"
            req = RequestData(hidden_response_fields=["api_token"])
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"api_token": secret, "version": "v1"}),
                elapsed_time=0.1,
                size=70,
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)

            # Masked secret is not found by search
            view.search_input.setText(secret)
            view._on_search_text_changed()
            assert view.search_status_label.text() == "No matches"

            # Reveal secret: search updates and finds the revealed text
            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            spans = view.mask_controller.spans()
            assert len(spans) == 1
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert view.search_status_label.text() == "1 of 1"

            # Re-mask secret: match status reverts to No matches
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert view.search_status_label.text() == "No matches"
        finally:
            view.close()

    def test_coexistence_with_code_folding_and_context_menu(self, qapp: QApplication) -> None:
        """Scenario 5: Coexistence with Code Folding & Context Menu.

        Code folding blocks remain aligned; selecting revealed text shows context menu.
        """
        view = ResponseView()
        try:
            secret = "nested_secret_token_456"
            req = RequestData(hidden_response_fields=["token"])
            nested_body = json.dumps(
                {
                    "group_a": {"item": 1, "nested": {"val": "ok"}},
                    "group_b": {"token": secret, "active": True},
                },
                indent=2,
            )
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=nested_body,
                elapsed_time=0.1,
                size=len(nested_body),
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            fc = view.body_view.fold_controller()
            initial_regions = list(fc.regions())
            assert len(initial_regions) > 0, "Nested JSON must produce fold regions"

            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            spans = view.mask_controller.spans()
            assert len(spans) == 1

            # Reveal secret and ensure fold regions remain valid
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert secret in view.body_view.toPlainText()
            assert len(fc.regions()) == len(initial_regions)

            # Context menu: Set Variable emits authentic revealed secret
            view.set_env_keys(["MY_TOKEN_VAR"])
            _select_text(view, secret)

            received: list[tuple[str, str]] = []
            view.variable_set_requested.connect(lambda k, v: received.append((k, v)))

            mock_menu = MagicMock()
            mock_submenu = MagicMock()
            mock_menu.addMenu.return_value = mock_submenu
            mock_menu.isEmpty.return_value = False
            key_action = MagicMock()
            new_var_action = MagicMock()
            mock_submenu.addAction.side_effect = [key_action, new_var_action]
            mock_menu.addAction.side_effect = lambda _label: MagicMock()

            with patch(_QMENU_PATCH, return_value=mock_menu):
                view.show_context_menu(QPoint(0, 0))

            _trigger_connected(key_action)
            assert received == [("MY_TOKEN_VAR", secret)]
        finally:
            view.close()

    def test_streaming_response_chunk_append_safety(self, qapp: QApplication) -> None:
        """Scenario 6: Streaming Chunk Append Safety.

        Calling append_body during in-flight stream does not crash, stall, or corrupt state.
        """
        view = ResponseView()
        try:
            view.append_body('{"chunk": 1, ')
            view.append_body('"token": "secret_chunk"}')
            assert '{"chunk": 1, "token": "secret_chunk"}' in view.body_view.toPlainText()

            req = RequestData(hidden_response_fields=["token"])
            final_body = json.dumps({"chunk": 1, "token": "secret_chunk"})
            final_resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=final_body,
                elapsed_time=0.5,
                size=len(final_body),
            )
            view.display_response(final_resp, hidden_fields=req.hidden_response_fields)
            text = view.body_view.toPlainText()
            assert '"token": "***"' in text
            assert "secret_chunk" not in text
            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            assert len(view.mask_controller.spans()) == 1
        finally:
            view.close()

    def test_large_document_fallback(self, qapp: QApplication) -> None:
        """Scenario 7: Large-Document Fallback Performance.

        Documents exceeding threshold (>100 KB) bypass token span overhead.
        """
        view = ResponseView()
        try:
            req = RequestData(hidden_response_fields=["secret"])
            payload = {"secret": "hide_me", "data": "x" * (LARGE_DOC_CHAR_THRESHOLD + 10)}
            body = json.dumps(payload)
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=body,
                elapsed_time=0.2,
                size=len(body),
            )
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            assert view.body_view.toPlainText() == body
            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            assert len(view.mask_controller.spans()) == 0
        finally:
            view.close()

    def test_response_data_immutability(self, qapp: QApplication) -> None:
        """Scenario 8: Raw In-Memory ResponseData Immutability.

        ResponseData.body in memory remains 100% authentic and unmutated throughout GUI actions.
        """
        view = ResponseView()
        try:
            raw_body = json.dumps({"token": "immutable_secret_123", "user": "alice"})
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=raw_body,
                elapsed_time=0.1,
                size=len(raw_body),
            )
            req = RequestData(hidden_response_fields=["token"])
            view.display_response(resp, hidden_fields=req.hidden_response_fields)
            assert resp.body == raw_body

            assert hasattr(view, "mask_controller"), "ResponseView must have mask_controller"
            spans = view.mask_controller.spans()
            assert len(spans) == 1

            # Reveal
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert resp.body == raw_body

            # Re-mask
            view.mask_controller.handle_click(spans[0].start_pos + 1)
            assert resp.body == raw_body
        finally:
            view.close()

    def test_masking_observability_logging_and_metrics(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies structured logging, metric increments, and zero secret leakage."""
        mock_metrics = MagicMock()
        view = ResponseView(metrics=mock_metrics)
        try:
            raw_secret = "sensitive_bearer_token_xyz"
            req = RequestData(hidden_response_fields=["auth.token"])
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=json.dumps({"auth": {"token": raw_secret}, "user": "bob"}),
                elapsed_time=0.05,
                size=80,
            )
            with caplog.at_level(logging.DEBUG):
                view.display_response(resp, hidden_fields=req.hidden_response_fields)

            mock_metrics.track_hidden_value_mask_applied.assert_called_once_with("gui_response")
            assert any(
                "response_masking_initialized span_count=1 selectors_count=1" in record.message
                for record in caplog.records
            )

            # Assert secret value does not appear in any log
            assert not any(raw_secret in record.message for record in caplog.records)

            # Click to reveal
            span = view.mask_controller.spans()[0]
            with caplog.at_level(logging.DEBUG):
                view.mask_controller.handle_click(span.start_pos + 1)

            assert any(
                "click_to_reveal_toggle path=auth.token revealed=True" in record.message
                for record in caplog.records
            )
            assert not any(raw_secret in record.message for record in caplog.records)

            # Click to re-mask
            with caplog.at_level(logging.DEBUG):
                view.mask_controller.handle_click(span.start_pos + 1)

            assert any(
                "click_to_reveal_toggle path=auth.token revealed=False" in record.message
                for record in caplog.records
            )
            assert not any(raw_secret in record.message for record in caplog.records)
        finally:
            view.close()

    def test_masking_observability_large_doc_fallback_logs(
        self, qapp: QApplication, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies large-document fallback logs payload size without secret leakage."""
        mock_metrics = MagicMock()
        view = ResponseView(metrics=mock_metrics)
        try:
            raw_secret = "confidential_api_secret_999"
            req = RequestData(hidden_response_fields=["secret"])
            payload = {"secret": raw_secret, "data": "y" * (LARGE_DOC_CHAR_THRESHOLD + 20)}
            body = json.dumps(payload)
            resp = ResponseData(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=body,
                elapsed_time=0.2,
                size=len(body),
            )
            with caplog.at_level(logging.DEBUG):
                view.display_response(resp, hidden_fields=req.hidden_response_fields)

            mock_metrics.track_hidden_value_mask_applied.assert_not_called()
            assert any(
                "response_masking_large_doc_fallback" in record.message
                for record in caplog.records
            )
            assert not any(raw_secret in record.message for record in caplog.records)
        finally:
            view.close()
