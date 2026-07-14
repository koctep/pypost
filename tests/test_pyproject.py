"""Validate pyproject.toml stays aligned with requirements.in sources (PYPOST-785/808)."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

from pypost.version import __version__

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = REPO_ROOT / "pyproject.toml"
REQUIREMENTS_IN = REPO_ROOT / "requirements.in"
REQUIREMENTS_DEV_IN = REPO_ROOT / "requirements-dev.in"
REQUIREMENTS_OTEL_IN = REPO_ROOT / "requirements-otel.in"

_SPEC_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*(.*)$")


def _read_direct_specs(path: Path) -> list[str]:
    specs: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        specs.append(line)
    return specs


def _normalize_spec(spec: str) -> str:
    match = _SPEC_RE.match(spec.strip())
    assert match is not None, f"invalid requirement spec: {spec!r}"
    name, version = match.group(1), match.group(2).strip()
    return f"{name.lower()}{version}"


def _load_pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


class TestPyprojectToml:
    def test_pyproject_exists(self) -> None:
        assert PYPROJECT.is_file()

    def test_project_metadata(self) -> None:
        data = _load_pyproject()
        project = data["project"]
        assert project["name"] == "pypost"
        assert project.get("dynamic") == ["version"]
        assert "version" not in project
        dynamic_version = data["tool"]["setuptools"]["dynamic"]["version"]
        assert dynamic_version == {"attr": "pypost.version.__version__"}
        assert __version__
        assert project["requires-python"] == ">=3.11"
        assert project["license"] == {"text": "MIT"}

    def test_dependencies_match_requirements_in(self) -> None:
        project = _load_pyproject()["project"]
        pyproject_specs = [_normalize_spec(spec) for spec in project["dependencies"]]
        requirements_specs = [_normalize_spec(spec) for spec in _read_direct_specs(REQUIREMENTS_IN)]
        assert pyproject_specs == requirements_specs

    def test_dev_extra_matches_requirements_dev_in(self) -> None:
        project = _load_pyproject()["project"]
        dev_specs = project["optional-dependencies"]["dev"]
        pyproject_specs = [_normalize_spec(spec) for spec in dev_specs]
        requirements_specs = [
            _normalize_spec(spec) for spec in _read_direct_specs(REQUIREMENTS_DEV_IN)
        ]
        assert pyproject_specs == requirements_specs

    def test_otel_extra_matches_requirements_otel_in(self) -> None:
        project = _load_pyproject()["project"]
        otel_specs = project["optional-dependencies"]["otel"]
        pyproject_specs = [_normalize_spec(spec) for spec in otel_specs]
        requirements_specs = [
            _normalize_spec(spec) for spec in _read_direct_specs(REQUIREMENTS_OTEL_IN)
        ]
        assert pyproject_specs == requirements_specs

    def test_otel_extra_defines_opentelemetry_packages(self) -> None:
        project = _load_pyproject()["project"]
        otel_specs = project["optional-dependencies"]["otel"]
        normalized = [_normalize_spec(spec) for spec in otel_specs]
        assert "opentelemetry-api==1.42.1" in normalized
        assert "opentelemetry-sdk==1.42.1" in normalized
