"""Tests for pypost.core.environment_export (PYPOST-988)."""

import json

import pytest

pytestmark = pytest.mark.timeout(60)

from pathlib import Path

from pypost.core.environment_export import (
    EnvironmentExportError,
    ExportPlanResult,
    ExportScope,
    build_export_payload,
    environments_for_export,
    export_includes_hidden,
    format_export_result,
    suggested_export_filename,
    write_export_file,
)
from pypost.core.environment_import import load_import_candidates
from pypost.core.storage import StorageManager
from pypost.models.models import Environment


def _make_storage(tmp_path, monkeypatch) -> StorageManager:
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager(data_dir=tmp_path / "pypost-data")


def test_environments_for_export_all_returns_copy():
    envs = [Environment(name="Dev"), Environment(name="Prod")]
    result = environments_for_export(envs, scope=ExportScope.ALL, selected_index=0)
    assert [e.name for e in result] == ["Dev", "Prod"]
    assert result is not envs


def test_environments_for_export_selected_returns_one():
    envs = [Environment(name="Dev"), Environment(name="Prod")]
    result = environments_for_export(envs, scope=ExportScope.SELECTED, selected_index=1)
    assert len(result) == 1
    assert result[0].name == "Prod"


def test_environments_for_export_selected_without_row_returns_empty():
    envs = [Environment(name="Dev")]
    assert environments_for_export(envs, scope=ExportScope.SELECTED, selected_index=-1) == []


def test_export_includes_hidden_detects_hidden_keys():
    plain = Environment(name="Plain", variables={"host": "x"})
    secret = Environment(name="Secret", variables={"token": "abc"}, hidden_keys={"token"})
    assert export_includes_hidden([plain]) is False
    assert export_includes_hidden([secret]) is True


def test_suggested_export_filename_single_and_multi():
    assert suggested_export_filename([Environment(name="Staging")]) == "Staging.json"
    assert (
        suggested_export_filename([Environment(name="Dev"), Environment(name="Prod")])
        == "environments.json"
    )


def test_build_export_payload_single_object_shape(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    env = Environment(name="Dev", variables={"HOST": "dev.example.com"})
    payload = build_export_payload([env], storage)
    assert isinstance(payload, dict)
    assert payload["name"] == "Dev"


def test_build_export_payload_list_shape(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    envs = [
        Environment(name="Dev", variables={"HOST": "dev.example.com"}),
        Environment(name="Prod", variables={"HOST": "prod.example.com"}),
    ]
    payload = build_export_payload(envs, storage)
    assert isinstance(payload, list)
    assert len(payload) == 2


def test_write_export_file_round_trips_through_import(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    env = Environment(
        name="Staging",
        variables={"host": "https://staging.example.com", "token": "secret"},
        hidden_keys={"token"},
    )
    export_path = tmp_path / "export.json"
    payload = build_export_payload([env], storage)
    write_export_file(export_path, payload)

    imported, parse_errors = load_import_candidates(export_path, storage)
    assert parse_errors == []
    assert len(imported) == 1
    assert imported[0].name == "Staging"
    assert imported[0].variables["token"] == "secret"
    assert imported[0].hidden_keys == {"token"}


def test_write_export_file_raises_on_write_failure(tmp_path, monkeypatch):
    export_path = tmp_path / "export.json"

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", boom)
    with pytest.raises(EnvironmentExportError, match="Could not write file"):
        write_export_file(export_path, {"name": "Dev", "variables": {}})


def test_format_export_result_includes_hidden_note():
    result_text = format_export_result(
        ExportPlanResult(
            exported_count=1,
            environment_names=["Prod"],
            includes_hidden=True,
            path=Path("/tmp/prod.json"),
        )
    )
    assert "Hidden variable values" in result_text
    assert "/tmp/prod.json" in result_text
