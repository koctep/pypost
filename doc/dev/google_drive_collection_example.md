# Google Drive Collection Example

## Overview

The Google Drive collection example (`examples/collections/google_drive.json`) provides a
canonical, production-ready REST collection conforming to PyPost Collection Schema v2.
It demonstrates interacting with Google Drive API v3 for file listing, metadata lookup,
binary media download, file creation, multipart upload, and sharing permissions.

## Architecture

- **Collection ID**: `google-drive-v3`
- **Specification Version**: `2.0.0`
- **Data Models**: Deserializes into `pypost.models.models.Collection` and `RequestData`.
- **Secrets Management**: OAuth tokens are parameterized using `CollectionVariable` with
  `secret: true`, ensuring tokens are never hardcoded or leaked into version control.
- **Contract Tests**: `tests/test_google_drive_collection_example.py` validates schema
  conformance, request signatures, and variable definitions offline without live network
  dependencies.

## Key Requests

1. `gdrive-files-list`: GET `{{ google_drive_base_url }}/files` with query filters.
2. `gdrive-files-get-metadata`: GET `{{ google_drive_base_url }}/files/{{ file_id }}`.
3. `gdrive-files-download-media`: GET `{{ google_drive_base_url }}/files/{{ file_id }}?alt=media`.
4. `gdrive-files-create-metadata`: POST `{{ google_drive_base_url }}/files`.
5. `gdrive-files-upload-multipart`: POST to upload endpoint with `uploadType=multipart`.
6. `gdrive-permissions-list`: GET `{{ google_drive_base_url }}/files/{{ file_id }}/permissions`.
7. `gdrive-permissions-create`: POST `{{ google_drive_base_url }}/files/{{ file_id }}/permissions`.

## Configuration

- `google_drive_base_url`: Base URL for Drive v3 REST endpoints
  (default: `https://www.googleapis.com/drive/v3`).
- `google_drive_upload_base_url`: Base URL for file upload endpoints
  (default: `https://www.googleapis.com/upload/drive/v3`).
- `google_drive_access_token`: OAuth 2.0 Bearer access token (`secret: true`).
- `file_id`: Target file identifier or `root`.

## Troubleshooting

- **401 Unauthorized**: Ensure `google_drive_access_token` is populated with a valid OAuth token
  having `https://www.googleapis.com/auth/drive` or relevant read/write scopes.
- **Upload Failures**: Confirm that multipart requests send to `google_drive_upload_base_url`
  rather than standard metadata endpoints.
