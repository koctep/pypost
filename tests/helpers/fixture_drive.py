"""Drive pytest yield fixtures outside a request (test harness only).

Packaging caplog proofs and similar unit tests sometimes need to invoke yield
fixtures manually. Pytest exposes the underlying generator via a private API;
this module isolates that coupling so pytest upgrades touch one file.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, TypeVar

import pytest

__all__ = [
    "call_yield_fixture",
    "run_yield_fixture",
    "unwrap_yield_fixture",
]

T = TypeVar("T")


def unwrap_yield_fixture(fixture: Any) -> Callable[..., Iterator[T]]:
    """Return the underlying generator function for a pytest yield fixture."""
    return fixture._get_wrapped_function()


def run_yield_fixture(gen: Iterator[T]) -> T:
    """Drive a yield-fixture generator through setup and teardown."""
    value = next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    return value


def call_yield_fixture(fixture: Any) -> T:
    """Unwrap and drive a pytest yield fixture outside a request."""
    return run_yield_fixture(unwrap_yield_fixture(fixture)())
