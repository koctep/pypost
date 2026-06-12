"""Default retry policy settings section."""

import logging
from typing import Any

from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLineEdit, QSpinBox, QWidget

from pypost.models.retry import (
    RetryableCodesValidationFailure,
    RetryPolicy,
    parse_retryable_status_codes,
)
from pypost.models.settings import AppSettings

logger = logging.getLogger("pypost.ui.dialogs.settings_dialog")


class RetryPolicySection:
    def __init__(self, current_settings: AppSettings, parent: QWidget) -> None:
        default_policy = RetryPolicy()
        current_policy = current_settings.default_retry_policy or default_policy

        self.max_retries_spin = QSpinBox(parent)
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(current_policy.max_retries)

        self.retry_delay_spin = QDoubleSpinBox(parent)
        self.retry_delay_spin.setRange(0.1, 30.0)
        self.retry_delay_spin.setSingleStep(0.1)
        self.retry_delay_spin.setDecimals(1)
        self.retry_delay_spin.setValue(current_policy.retry_delay_seconds)

        self.retry_backoff_spin = QDoubleSpinBox(parent)
        self.retry_backoff_spin.setRange(1.0, 5.0)
        self.retry_backoff_spin.setSingleStep(0.1)
        self.retry_backoff_spin.setDecimals(1)
        self.retry_backoff_spin.setValue(current_policy.retry_backoff_multiplier)

        self.retryable_codes_edit = QLineEdit(parent)
        self.retryable_codes_edit.setPlaceholderText("e.g. 429,500,502,503,504")
        self.retryable_codes_edit.setText(
            ",".join(str(c) for c in current_policy.retryable_status_codes)
        )

    def add_to_form(self, form: QFormLayout) -> None:
        form.addRow("Max Retries (0 = disabled):", self.max_retries_spin)
        form.addRow("Retry Delay (seconds):", self.retry_delay_spin)
        form.addRow("Retry Backoff Multiplier:", self.retry_backoff_spin)
        form.addRow("Retryable Status Codes:", self.retryable_codes_edit)

    def validate(self, parent: QWidget) -> RetryPolicy | None:
        parsed_codes = parse_retryable_status_codes(self.retryable_codes_edit.text())
        if isinstance(parsed_codes, RetryableCodesValidationFailure):
            logger.warning(
                "retryable_codes_settings_validation_failed reason=%s",
                parsed_codes.reason,
            )
            from pypost.ui.dialogs.settings_dialog import (
                show_invalid_retryable_status_codes,
            )

            show_invalid_retryable_status_codes(parent, parsed_codes.message)
            return None
        return RetryPolicy(
            max_retries=self.max_retries_spin.value(),
            retry_delay_seconds=self.retry_delay_spin.value(),
            retry_backoff_multiplier=self.retry_backoff_spin.value(),
            retryable_status_codes=parsed_codes,
        )

    def collect_fields(self, retry_policy: RetryPolicy) -> dict[str, Any]:
        return {"default_retry_policy": retry_policy}
