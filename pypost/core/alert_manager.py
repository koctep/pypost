from __future__ import annotations

import json
import logging
import logging.handlers
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from platformdirs import user_data_dir

logger = logging.getLogger(__name__)


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

        handler = logging.handlers.RotatingFileHandler(
            resolved,
            maxBytes=self._MAX_BYTES,
            backupCount=self._BACKUP_COUNT,
            encoding="utf-8",
        )
        self._logger = logging.getLogger(f"pypost.alerts.{id(self)}")
        self._logger.propagate = False
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(handler)

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
            self._send_webhook(payload)

    def _send_webhook(self, payload: AlertPayload) -> None:
        headers = {"Content-Type": "application/json"}
        if self._webhook_auth_header:
            headers["Authorization"] = self._webhook_auth_header
        try:
            requests.post(
                self._webhook_url,
                json=payload.to_dict(),
                headers=headers,
                timeout=5.0,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "alert_webhook_failed url=%r error=%s", self._webhook_url, exc
            )
