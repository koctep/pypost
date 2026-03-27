from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

from pydantic import BaseModel, Field

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
    max_retries: int = 0
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
