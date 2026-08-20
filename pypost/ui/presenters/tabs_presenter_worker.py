"""Request worker lifecycle handlers for TabsPresenter (PYPOST-731)."""

from __future__ import annotations

import logging
from functools import partial
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer

from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.ui.collection_item_dialogs import show_request_error, show_request_failed_error

if TYPE_CHECKING:
    from pypost.models.response import ResponseData
    from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter

logger = logging.getLogger(__name__)

_ERROR_MESSAGES = {
    ErrorCategory.NETWORK: (
        "Could not connect to {url}. Check that the server is running and reachable."
    ),
    ErrorCategory.TIMEOUT: (
        "Request to {url} timed out. Try increasing the timeout or check server load."
    ),
    ErrorCategory.TEMPLATE: (
        "Template rendering failed: {detail}. Check variable names and syntax."
    ),
    ErrorCategory.BODY: (
        "Could not convert YAML body to JSON: {detail}. Check YAML syntax and structure."
    ),
    ErrorCategory.SCRIPT: ("Post-script execution failed: {detail}. Review the script for errors."),
    ErrorCategory.HISTORY: ("History could not be recorded: {detail}."),
    ErrorCategory.UNKNOWN: ("An unexpected error occurred: {detail}."),
}


class TabsPresenterWorkerHandlers:
    """Worker signal handlers extracted from TabsPresenter."""

    def _discard_chunk_buffer(self: TabsPresenter, tab: RequestTab) -> None:
        """Stop pending flush timer and drop buffered chunks for *tab*.

        Prevents a late ``_flush_chunk_buffer`` from appending after
        ``display_response`` (setText) or into a cleared body (PYPOST-887).
        """
        tab_key = id(tab)
        timer = self._chunk_flush_timers.pop(tab_key, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
        self._chunk_buffers.pop(tab_key, None)

    def _on_request_finished(
        self: TabsPresenter,
        tab: RequestTab,
        response: ResponseData,
    ) -> None:
        self._clear_tab_worker(tab)
        self._discard_chunk_buffer(tab)
        method = tab.request_data.method if tab.request_data else "UNKNOWN"
        logger.info(
            "request_finished method=%s status_code=%s elapsed_time=%.3fs size=%s",
            method,
            response.status_code,
            response.elapsed_time,
            response.size,
        )
        self._metrics.track_response_received(method, str(response.status_code))
        tab.response_view.display_response(response)
        self._reset_tab_ui_state(tab)
        tab.response_view.status_label.setText(f"Status: {response.status_code}")
        tab.response_view.time_label.setText(f"Time: {response.elapsed_time:.3f}s")
        tab.response_view.size_label.setText(f"Size: {response.size} bytes")
        self.request_executed.emit()

    def _on_request_error(self: TabsPresenter, tab: RequestTab, error) -> None:
        self._clear_tab_worker(tab)
        self._discard_chunk_buffer(tab)
        self._reset_tab_ui_state(tab)

        if isinstance(error, str):
            if "cancelled" in error.lower() or "aborted" in error.lower():
                logger.info("request_cancelled error_msg=%s", error)
                return
            logger.error("request_error error_msg=%s", error)
            show_request_failed_error(self._tabs, error)
            return

        if isinstance(error, ExecutionError):
            if error.category == ErrorCategory.CANCELLED:
                logger.info("request_cancelled category=%s", error.category)
                return

            url = tab.request_data.url if tab.request_data else ""
            template = _ERROR_MESSAGES.get(error.category, _ERROR_MESSAGES[ErrorCategory.UNKNOWN])
            user_msg = template.format(url=url, detail=error.detail or error.message)

            logger.error(
                "request_error category=%s message=%s detail=%s",
                error.category,
                error.message,
                error.detail,
            )
            show_request_error(self._tabs, user_msg)

    def _on_script_output(
        self: TabsPresenter,
        tab: RequestTab,
        logs: list[str],
        err: object,
    ) -> None:
        if logs:
            for line in str(logs).splitlines():
                logger.debug("script_output tab_id=%s line=%s", id(tab), line)
        if err is not None and not isinstance(err, str):
            logger.warning(
                "script_output_ignored reason=invalid_error_type type=%s",
                type(err).__name__,
            )
            return
        if err:
            logger.warning("script_error tab_id=%s error=%s", id(tab), err)

    def _on_headers_received(
        self: TabsPresenter, tab: RequestTab, status: int, headers: dict
    ) -> None:
        tab.response_view.status_label.setText(f"Status: {status}")

    def _on_chunk_received(self: TabsPresenter, tab: RequestTab, chunk: str) -> None:
        tab_key = id(tab)
        self._chunk_buffers.setdefault(tab_key, []).append(chunk)
        timer = self._chunk_flush_timers.get(tab_key)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setInterval(self._chunk_flush_ms)
            timer.timeout.connect(partial(self._flush_chunk_buffer, tab))
            self._chunk_flush_timers[tab_key] = timer
        timer.start()

    def _flush_chunk_buffer(self: TabsPresenter, tab: RequestTab) -> None:
        tab_key = id(tab)
        chunks = self._chunk_buffers.pop(tab_key, [])
        if not chunks:
            return
        tab.response_view.append_body("".join(chunks))
        current_text = tab.response_view.body_view.toPlainText()
        size_bytes = len(current_text.encode("utf-8"))
        tab.response_view.size_label.setText(f"Size: {size_bytes} bytes")

    def _on_retry_attempt(
        self: TabsPresenter,
        tab: RequestTab,
        attempt: int,
        max_retries: int,
    ) -> None:
        tab.request_editor.send_btn.setText(f"Retrying\u2026 ({attempt} of {max_retries})")

    def _clear_tab_worker(
        self: TabsPresenter,
        tab: RequestTab,
        *,
        reason: str = "completed",
        request_data=None,
    ) -> None:
        if tab.worker is None:
            return
        if reason == "stale":
            method = request_data.method if request_data else "UNKNOWN"
            url = request_data.url if request_data else ""
            logger.debug("stale_worker_cleared method=%s url=%s", method, url)
        tab.worker = None

    def _reset_tab_ui_state(self: TabsPresenter, tab: RequestTab) -> None:
        tab.request_editor.send_btn.setEnabled(True)
        tab.request_editor.send_btn.setText("Send")
