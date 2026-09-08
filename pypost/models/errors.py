import enum
from dataclasses import dataclass, field
from typing import Optional


class ErrorCategory(str, enum.Enum):
    # The user stopped the request. Not a failure, and not reported as one.
    CANCELLED = "cancelled"
    NETWORK = "network"
    TIMEOUT = "timeout"
    TEMPLATE = "template"
    SCRIPT = "script"
    HISTORY = "history"
    UNKNOWN = "unknown"


@dataclass
class ExecutionError(Exception):
    category: ErrorCategory
    message: str
    detail: Optional[str] = field(default=None)

    def __str__(self) -> str:
        return self.message
