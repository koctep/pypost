from __future__ import annotations

import json
import logging
import logging.handlers
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from platformdirs import user_data_dir

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 5.0
# Bounded: an unreachable webhook must not let alerts accumulate without limit.
WEBHOOK_QUEUE_SIZE = 64
WEBHOOK_SHUTDOWN_TIMEOUT_SECONDS = 6.0


@dataclass
class AlertPayload:
    request_name: str
    endpoint: str
    retries_attempted: int
    final_error_category: str
    final_error_message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "request_name": self.request_name,
            "endpoint": self.endpoint,
            "retries_attempted": self.retries_attempted,
            "final_error_category": self.final_error_category,
            "final_error_message": self.final_error_message,
        }


class AlertManager:
    """Emits structured alerts to a rotating log file and/or HTTP webhook."""

    _LOG_FILENAME = "pypost-alerts.log"
    _MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
    _BACKUP_COUNT = 3

    def __init__(
        self,
        log_path: Optional[Path] = None,
        webhook_url: Optional[str] = None,
        webhook_auth_header: Optional[str] = None,
    ) -> None:
        resolved = log_path or Path(user_data_dir("pypost")) / self._LOG_FILENAME
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self._webhook_url = webhook_url
        self._webhook_auth_header = webhook_auth_header
        self._webhook_queue: queue.Queue = queue.Queue(maxsize=WEBHOOK_QUEUE_SIZE)
        self._webhook_thread: threading.Thread | None = None
        self._webhook_lock = threading.Lock()

        handler = logging.handlers.RotatingFileHandler(
            resolved,
            maxBytes=self._MAX_BYTES,
            backupCount=self._BACKUP_COUNT,
            encoding="utf-8",
        )
        self._logger = logging.getLogger(f"pypost.alerts.{id(self)}")
        self._logger.propagate = False
        self._logger.setLevel(logging.INFO)

        # Guard: remove stale handlers left by a GC'd instance at this address.
        stale_handlers = list(self._logger.handlers)
        if stale_handlers:
            logger.warning(
                "alert_manager_stale_handlers_evicted count=%d log_path=%s"
                " — prior AlertManager was not closed; evicting to prevent accumulation",
                len(stale_handlers),
                resolved,
            )
        for stale in stale_handlers:
            try:
                stale.close()
            except Exception:  # noqa: BLE001
                pass
            self._logger.removeHandler(stale)

        self._logger.addHandler(handler)
        logger.debug("alert_manager_init log_path=%s webhook=%s", resolved,
                     "yes" if webhook_url else "no")
        self._handler = handler  # owned reference for close()

    def close(self) -> None:
        """Stop the webhook dispatcher and release the log handler."""
        self._stop_dispatcher()
        try:
            self._handler.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            self._logger.removeHandler(self._handler)
        except Exception:  # noqa: BLE001
            pass
        logger.debug("alert_manager_close logger=%s", self._logger.name)

    def __enter__(self) -> "AlertManager":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def configure_webhook(
        self,
        webhook_url: Optional[str],
        webhook_auth_header: Optional[str],
    ) -> None:
        """Apply webhook settings without replacing the log handler."""
        self._webhook_url = webhook_url
        self._webhook_auth_header = webhook_auth_header

    def emit(self, payload: AlertPayload) -> None:
        """Write JSON alert to the rotating log file and optionally send to webhook."""
        self._logger.info(json.dumps(payload.to_dict()))
        logger.warning(
            "alert_emitted request_name=%r endpoint=%r retries=%d"
            " error_category=%s webhook=%s",
            payload.request_name, payload.endpoint, payload.retries_attempted,
            payload.final_error_category, "yes" if self._webhook_url else "no",
        )
        if self._webhook_url:
            self._enqueue_webhook(payload)

    def flush(self, timeout: float | None = None) -> None:
        """Block until queued webhooks have been attempted.

        For tests and teardown. Each attempt is bounded by the request timeout,
        so this cannot wait indefinitely on an unreachable endpoint.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while self._webhook_queue.unfinished_tasks:
            if deadline is not None and time.monotonic() >= deadline:
                logger.warning("alert_webhook_flush_timeout timeout=%.1f", timeout)
                return
            time.sleep(0.01)

    def _enqueue_webhook(self, payload: AlertPayload) -> None:
        """Hand the POST to a background thread.

        emit() runs on the request thread, inside the failure the user is
        already waiting on. Posting synchronously added the webhook timeout to
        that wait, for an alert the user never sees.

        The destination is captured here rather than read in the dispatcher, so
        an alert raised under one configuration is not delivered to another.
        """
        item = (payload, self._webhook_url, self._webhook_auth_header)
        self._ensure_dispatcher()
        try:
            self._webhook_queue.put_nowait(item)
        except queue.Full:
            logger.warning(
                "alert_webhook_dropped reason=queue_full url=%r", self._webhook_url
            )

    def _ensure_dispatcher(self) -> None:
        with self._webhook_lock:
            if self._webhook_thread is not None and self._webhook_thread.is_alive():
                return
            self._webhook_thread = threading.Thread(
                target=self._dispatch_webhooks,
                name="pypost-alert-webhooks",
                daemon=True,
            )
            self._webhook_thread.start()

    def _stop_dispatcher(self) -> None:
        with self._webhook_lock:
            thread = self._webhook_thread
            self._webhook_thread = None
        if thread is None or not thread.is_alive():
            return
        self._webhook_queue.put(None)
        thread.join(timeout=WEBHOOK_SHUTDOWN_TIMEOUT_SECONDS)
        if thread.is_alive():
            logger.warning(
                "alert_webhook_dispatcher_stop_timeout timeout=%.1f",
                WEBHOOK_SHUTDOWN_TIMEOUT_SECONDS,
            )

    def _dispatch_webhooks(self) -> None:
        while True:
            item = self._webhook_queue.get()
            try:
                if item is None:
                    return
                payload, url, auth_header = item
                self._send_webhook(payload, url, auth_header)
            finally:
                self._webhook_queue.task_done()

    def _send_webhook(
        self, payload: AlertPayload, url: str, auth_header: Optional[str],
    ) -> None:
        headers = {"Content-Type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
        try:
            resp = requests.post(
                url,
                json=payload.to_dict(),
                headers=headers,
                timeout=WEBHOOK_TIMEOUT_SECONDS,
            )
            logger.debug("alert_webhook_ok url=%r status=%d", url, resp.status_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("alert_webhook_failed url=%r error=%s", url, exc)
