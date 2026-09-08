"""What to put in front of the user when a request fails.

Deciding whether a failure is worth reporting, and phrasing it, are separate
from showing a dialog. Keeping them here means the presenter renders what it is
given, and the wording can be read -- and tested -- without a widget.
"""
from dataclasses import dataclass

from pypost.models.errors import ErrorCategory, ExecutionError

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
    ErrorCategory.SCRIPT: (
        "Post-script execution failed: {detail}. Review the script for errors."
    ),
    ErrorCategory.HISTORY: (
        "History could not be recorded: {detail}."
    ),
    ErrorCategory.UNKNOWN: (
        "An unexpected error occurred: {detail}."
    ),
}

# Wording older code paths used before cancellation had a category of its own.
_LEGACY_CANCELLATION_WORDS = ("cancelled", "aborted")


@dataclass(frozen=True)
class ErrorPrompt:
    title: str
    message: str


def describe(error: object, url: str = "") -> ErrorPrompt | None:
    """Describe a failed request, or return None if nothing should be said.

    A request the user stopped is not a failure to report.
    """
    if isinstance(error, ExecutionError):
        if error.category is ErrorCategory.CANCELLED:
            return None
        template = _ERROR_MESSAGES.get(
            error.category, _ERROR_MESSAGES[ErrorCategory.UNKNOWN],
        )
        return ErrorPrompt(
            title="Request Error",
            message=template.format(url=url, detail=error.detail or error.message),
        )

    text = str(error)
    if any(word in text.lower() for word in _LEGACY_CANCELLATION_WORDS):
        return None
    return ErrorPrompt(title="Error", message=f"Request failed: {text}")
