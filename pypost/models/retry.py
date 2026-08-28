from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Union

from pydantic import BaseModel, Field, model_validator

_HTTP_STATUS_MIN = 100
_HTTP_STATUS_MAX = 599


@dataclass(frozen=True)
class RetryableCodesValidationFailure:
    """Structured failure from parse_retryable_status_codes."""

    reason: str
    message: str


def parse_retryable_status_codes(
    raw: str,
) -> Union[List[int], RetryableCodesValidationFailure]:
    """Parse comma-separated HTTP status codes; each must be in 100..599."""
    stripped = raw.strip()
    if not stripped:
        return []
    result: List[int] = []
    for segment in stripped.split(","):
        token = segment.strip()
        if not token:
            return RetryableCodesValidationFailure(
                reason="empty_segment",
                message=(
                    "Retryable status codes cannot include empty entries between "
                    "commas. Use a comma only between numbers (e.g. 429,500,503)."
                ),
            )
        if not token.isdigit():
            return RetryableCodesValidationFailure(
                reason="invalid_token",
                message=(
                    "Each entry must be a whole number (HTTP status code). "
                    "Separate codes with commas (e.g. 429,500,502,503,504)."
                ),
            )
        value = int(token)
        if value < _HTTP_STATUS_MIN or value > _HTTP_STATUS_MAX:
            return RetryableCodesValidationFailure(
                reason="out_of_range",
                message=(
                    "Each status code must be between 100 and 599. "
                    "Separate codes with commas (e.g. 429,500,502,503,504)."
                ),
            )
        result.append(value)
    return result


class RetryPolicy(BaseModel):
    max_retries: int = Field(default=0, ge=0)
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = Field(default_factory=lambda: [429, 500, 502, 503, 504])

    def __init__(
        self,
        *args: Any,
        max_attempts: int | None = None,
        initial_delay_sec: float | None = None,
        backoff_factor: float | None = None,
        retry_on_status_codes: List[int] | None = None,
        **kwargs: Any,
    ) -> None:
        if max_attempts is not None and "max_retries" not in kwargs:
            kwargs["max_retries"] = max_attempts
        if initial_delay_sec is not None and "retry_delay_seconds" not in kwargs:
            kwargs["retry_delay_seconds"] = initial_delay_sec
        if backoff_factor is not None and "retry_backoff_multiplier" not in kwargs:
            kwargs["retry_backoff_multiplier"] = backoff_factor
        if retry_on_status_codes is not None and "retryable_status_codes" not in kwargs:
            kwargs["retryable_status_codes"] = retry_on_status_codes
        super().__init__(*args, **kwargs)

    @model_validator(mode="before")
    @classmethod
    def _remap_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            if "max_attempts" in data and "max_retries" not in data:
                data["max_retries"] = data.pop("max_attempts")
            if "initial_delay_sec" in data and "retry_delay_seconds" not in data:
                data["retry_delay_seconds"] = data.pop("initial_delay_sec")
            if "backoff_factor" in data and "retry_backoff_multiplier" not in data:
                data["retry_backoff_multiplier"] = data.pop("backoff_factor")
            if "retry_on_status_codes" in data and "retryable_status_codes" not in data:
                data["retryable_status_codes"] = data.pop("retry_on_status_codes")
        return data

    @property
    def max_attempts(self) -> int:
        return self.max_retries

    @property
    def initial_delay_sec(self) -> float:
        return self.retry_delay_seconds

    @property
    def backoff_factor(self) -> float:
        return self.retry_backoff_multiplier

    @property
    def retry_on_status_codes(self) -> List[int]:
        return self.retryable_status_codes
