"""Tests for pypost.core.collection_export (PYPOST-989)."""

import json

import pytest

pytestmark = pytest.mark.timeout(60)

from pathlib import Path

from pypost.core.collection_export import (
    CollectionExportError,
    CollectionExportResult,
    build_export_payload,
    collection_for_export,
    format_export_result,
    suggested_export_filename,
    write_export_file,
)
from pypost.core.collection_import import load_collection_import_candidates
from pypost.models.models import Collection, RequestData


def _make_collection(
    col_id: str = "col-1",
    name: str = "Billing API",
    requests=None,
) -> Collection:
    return Collection(
        id=col_id,
        name=name,
        requests=requests
        or [
            RequestData(
                id="req-1",
                name="Create invoice",
                method="POST",
                url="https://api.example.com/invoices",
                headers={"Authorization": "Bearer {{token}}"},
                params={"dry_run": "true"},
                body='{"amount": 100}',
                body_type="json",
                post_script="print(response.status_code)",
                expose_as_mcp=True,
                mcp_description="Create an invoice",
            )
        ],
    )


def test_collection_for_export_returns_match_by_id():
    collection = _make_collection()
    result = collection_for_export([collection], selected_collection_id="col-1")
    assert result is collection


def test_collection_for_export_without_selection_returns_none():
    collection = _make_collection()
    assert collection_for_export([collection], selected_collection_id=None) is None
    assert collection_for_export([collection], selected_collection_id="missing") is None


def test_suggested_export_filename_sanitizes_invalid_chars():
    collection = Collection(id="c1", name='Team/API:staging')
    assert suggested_export_filename(collection) == "Team_API_staging.json"


def test_build_export_payload_preserves_request_fields():
    collection = _make_collection()
    payload = build_export_payload(collection)
    request = payload["requests"][0]
    assert payload["name"] == "Billing API"
    assert request["method"] == "POST"
    assert request["url"] == "https://api.example.com/invoices"
    assert request["headers"] == {"Authorization": "Bearer {{token}}"}
    assert request["params"] == {"dry_run": "true"}
    assert request["body"] == '{"amount": 100}'
    assert request["post_script"] == "print(response.status_code)"
    assert request["expose_as_mcp"] is True
    assert request["mcp_description"] == "Create an invoice"


def test_write_export_file_round_trips_through_import(tmp_path):
    collection = _make_collection()
    export_path = tmp_path / "Billing API.json"
    payload = build_export_payload(collection)
    write_export_file(export_path, payload)

    imported, parse_errors = load_collection_import_candidates(export_path)
    assert parse_errors == []
    assert len(imported) == 1
    assert imported[0].name == "Billing API"
    request = imported[0].requests[0]
    assert request.method == "POST"
    assert request.url == "https://api.example.com/invoices"
    assert request.headers == {"Authorization": "Bearer {{token}}"}
    assert request.expose_as_mcp is True


def test_write_export_file_raises_on_write_failure(tmp_path, monkeypatch):
    export_path = tmp_path / "export.json"

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", boom)
    with pytest.raises(CollectionExportError, match="Could not write file"):
        write_export_file(export_path, {"name": "Billing API", "requests": []})


def test_format_export_result_includes_name_and_path():
    result_text = format_export_result(
        CollectionExportResult(
            collection_name="Billing API",
            request_count=2,
            path=Path("/tmp/Billing API.json"),
        )
    )
    assert 'Exported collection "Billing API" (2 request(s))' in result_text
    assert "/tmp/Billing API.json" in result_text


def test_exported_json_is_single_object_shape(tmp_path):
    collection = _make_collection()
    export_path = tmp_path / "export.json"
    write_export_file(export_path, build_export_payload(collection))
    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data["name"] == "Billing API"
