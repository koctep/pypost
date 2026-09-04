"""Shared bounded wait support for asynchronous collection-import presenter tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from tests.helpers.process_until import process_until

__all__ = ["wait_import"]

_IMPORT_WAIT_MS = 5_000


class _ImportActions(Protocol):
    """Presenter import-actions surface required to determine idleness."""

    def is_busy(self) -> bool: ...


class _ImportPresenter(Protocol):
    """Presenter surface required by :func:`wait_import`."""

    _import_actions: _ImportActions


def wait_import(
    done: Callable[[], bool],
    presenter: _ImportPresenter | None = None,
    timeout_ms: int = _IMPORT_WAIT_MS,
) -> None:
    """Pump the event loop until an import outcome is visible and the presenter is idle."""

    last_done = False

    def condition() -> bool:
        nonlocal last_done
        last_done = done()
        if not last_done:
            return False
        if presenter is not None and presenter._import_actions.is_busy():
            return False
        return True

    def timeout_detail() -> str:
        details = [f"outcome={last_done}"]
        if presenter is not None:
            details.append(f"busy={presenter._import_actions.is_busy()}")
        return " ".join(details)

    process_until(condition, timeout_ms=timeout_ms, timeout_detail=timeout_detail)
