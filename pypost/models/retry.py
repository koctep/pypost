from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    max_retries: int = 0
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
