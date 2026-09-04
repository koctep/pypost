"""Contract tests for the shared presenter import wait helper (PYPOST-1230)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QTimer

from tests.helpers.collection_import_wait import wait_import

pytestmark = pytest.mark.timeout(30)


class _FakeImportActions:
    def __init__(self, state: dict[str, bool]) -> None:
        self._state = state

    def is_busy(self) -> bool:
        return self._state["busy"]


class _FakePresenter:
    def __init__(self, state: dict[str, bool]) -> None:
        self._import_actions = _FakeImportActions(state)


def test_wait_import_requires_outcome_and_idle_before_returning(qapp) -> None:
    """An early outcome must not release the wait while import actions remain busy."""
    state = {"outcome": False, "busy": True}
    presenter = _FakePresenter(state)

    QTimer.singleShot(0, lambda: state.__setitem__("outcome", True))
    QTimer.singleShot(40, lambda: state.__setitem__("busy", False))

    wait_import(lambda: state["outcome"], presenter, timeout_ms=500)

    assert state["outcome"] is True
    assert state["busy"] is False


def test_wait_import_fails_with_bounded_timeout_when_completion_never_occurs(qapp) -> None:
    """A stalled outcome must produce the shared bounded timeout assertion."""
    presenter = _FakePresenter({"outcome": False, "busy": True})

    with pytest.raises(
        AssertionError,
        match=(
            r"condition not met within 120ms.*outcome=False busy=True"
        ),
    ):
        wait_import(lambda: False, presenter, timeout_ms=120)
