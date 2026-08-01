"""PYPOST-900: unit proof for tests.helpers.fixture_drive."""

from __future__ import annotations

import pytest

from tests.helpers.fixture_drive import call_yield_fixture, run_yield_fixture, unwrap_yield_fixture

pytestmark = pytest.mark.timeout(30)


@pytest.fixture
def sample_yield_fixture() -> int:
    yield 42


def test_unwrap_yield_fixture_returns_callable() -> None:
    """unwrap_yield_fixture exposes the underlying generator function."""
    fn = unwrap_yield_fixture(sample_yield_fixture)
    gen = fn()
    assert next(gen) == 42
    with pytest.raises(StopIteration):
        next(gen)


def test_run_yield_fixture_drives_setup_and_teardown() -> None:
    """run_yield_fixture returns setup value and completes teardown."""
    value = run_yield_fixture(unwrap_yield_fixture(sample_yield_fixture)())
    assert value == 42


def test_call_yield_fixture_compose() -> None:
    """call_yield_fixture unwraps and drives in one step."""
    assert call_yield_fixture(sample_yield_fixture) == 42
