"""Contract tests for Google Drive v3 example collection fixture (PYPOST-1268)."""

from __future__ import annotations

from pathlib import Path
import pytest

from pypost.core.collection_serializer import read_collection_file
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
GOOGLE_DRIVE_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "google_drive.json"


class TestGoogleDriveCollectionFixture:
    def test_fixture_file_exists(self) -> None:
        assert GOOGLE_DRIVE_COLLECTION_PATH.is_file(), (
            f"Expected Google Drive collection file at {GOOGLE_DRIVE_COLLECTION_PATH}"
        )

    def test_fixture_loads_as_collection(self) -> None:
        collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
        assert isinstance(collection, Collection)
        assert collection.id == "google-drive-v3"
        assert collection.name == "Google Drive API v3"
        assert collection.version == "2.0.0"

    def test_fixture_declares_required_variables(self) -> None:
        collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
        var_map = {v.name: v for v in collection.variables}

        assert "google_drive_base_url" in var_map
        assert var_map["google_drive_base_url"].default == "https://www.googleapis.com/drive/v3"
        assert var_map["google_drive_base_url"].secret is False

        assert "google_drive_upload_base_url" in var_map
        expected_upload = "https://www.googleapis.com/upload/drive/v3"
        assert var_map["google_drive_upload_base_url"].default == expected_upload
        assert var_map["google_drive_upload_base_url"].secret is False

        assert "google_drive_access_token" in var_map
        assert var_map["google_drive_access_token"].secret is True

    def test_fixture_declares_core_requests(self) -> None:
        collection = read_collection_file(GOOGLE_DRIVE_COLLECTION_PATH)
        req_map = {r.id: r for r in collection.requests}

        expected_ids = {
            "gdrive-files-list",
            "gdrive-files-get-metadata",
            "gdrive-files-download-media",
            "gdrive-files-create-metadata",
            "gdrive-files-upload-multipart",
            "gdrive-permissions-list",
            "gdrive-permissions-create",
        }
        missing = expected_ids - set(req_map.keys())
        assert not missing, f"Missing expected requests in Google Drive collection: {missing}"

        # Verify Bearer token authorization header template on core endpoints
        for req_id in expected_ids:
            req = req_map[req_id]
            auth_header = req.headers.get("Authorization", "")
            assert "{{ google_drive_access_token }}" in auth_header, (
                f"Request {req_id} missing Authorization Bearer template variable"
            )
