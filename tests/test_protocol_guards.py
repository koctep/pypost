"""Tests for the shared runtime-checkable protocol conformance guard."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

import pytest

from tests.helpers.protocol_guards import _assert_tracker_satisfies_all_protocol_methods

pytestmark = pytest.mark.timeout(10)


@runtime_checkable
class _ExampleProtocol(Protocol):
    def execute(self, query: str, *, limit: int = 1) -> None:
        ...


class _ExampleImplementation:
    def execute(self, query: str, *, limit: int = 1) -> None:
        del query, limit


def test_shared_guard_accepts_an_independent_runtime_checkable_protocol():
    assert isinstance(_ExampleImplementation(), _ExampleProtocol)
    _assert_tracker_satisfies_all_protocol_methods(
        _ExampleImplementation,
        _ExampleProtocol,
    )
