"""Guard that pytest --strict-markers stays enabled (PYPOST-865)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.timeout(10)

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"

_REQUIRED_MARKERS = ("timeout", "slow", "agent_e2e")


def _pytest_ini_options() -> dict:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["tool"]["pytest"]["ini_options"]


def test_addopts_includes_strict_markers() -> None:
    """Default pytest addopts must enable --strict-markers (unknown marks fail)."""
    addopts = _pytest_ini_options()["addopts"]
    assert isinstance(addopts, list)
    assert "--strict-markers" in addopts, (
        "pyproject.toml [tool.pytest.ini_options] addopts must include "
        "--strict-markers so unknown markers fail loudly (PYPOST-865)"
    )


def _marker_registered(markers: list[str], name: str) -> bool:
    prefix_colon = f"{name}:"
    prefix_paren = f"{name}("
    return any(
        entry == name
        or entry.startswith(prefix_colon)
        or entry.startswith(prefix_paren)
        for entry in markers
    )


def test_required_custom_markers_are_registered() -> None:
    """Registered markers required by the suite must remain declared."""
    markers = _pytest_ini_options()["markers"]
    assert isinstance(markers, list)
    for name in _REQUIRED_MARKERS:
        assert _marker_registered(markers, name), (
            f"marker {name!r} must be registered in pyproject.toml "
            f"[tool.pytest.ini_options] markers (PYPOST-865)"
        )
