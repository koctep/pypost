"""Mypy baseline gate for pypost/core and pypost/models (PYPOST-734)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_mypy_baseline import BASELINE_PATH, _parse_errors

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestMypyBaseline:
    def test_baseline_file_exists(self) -> None:
        assert BASELINE_PATH.is_file()

    def test_baseline_scope_is_core_and_models(self) -> None:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        assert data["scope"] == ["pypost/core", "pypost/models"]
        assert data["error_count"] == len(data["errors"])
        assert data["error_count"] > 0

    def test_parse_errors_extracts_path_line_code(self) -> None:
        sample = (
            "pypost/core/http_client.py:218: error: Incompatible default "
            "for parameter \"variables\" [assignment]\n"
        )
        assert _parse_errors(sample) == ["pypost/core/http_client.py:218:assignment"]

    def test_baseline_entries_use_scoped_paths(self) -> None:
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for entry in data["errors"]:
            assert entry.startswith("pypost/core/") or entry.startswith("pypost/models/")
