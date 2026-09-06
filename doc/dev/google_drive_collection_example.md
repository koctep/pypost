# Google Drive Collection Example

## Overview

The Google Drive collection example (`examples/collections/google_drive.json`) provides a
canonical, production-ready REST collection conforming to PyPost Collection Schema v2.
It demonstrates interacting with Google Drive API v3 for file listing, metadata lookup,
binary media download, file creation, multipart and resumable uploads, and sharing permissions.

## Architecture

- **Collection ID**: `google-drive-v3`
- **Specification Version**: `2.0.0`
- **Data Models**: Deserializes into `pypost.models.models.Collection` and `RequestData`.
- **Secrets Management**: OAuth tokens are parameterized using `CollectionVariable` with
  `secret: true`, ensuring tokens are never hardcoded or leaked into version control.
- **Contract Tests**: `tests/test_google_drive_collection_example.py` validates schema
  conformance, request signatures, and variable definitions offline without live network
  dependencies.
- **Resumable Handoff**: The initiation request returns a session URL in `Location`; the
  caller copies that value into `google_drive_upload_session_url` for the chunk request.

## Key Requests

1. `gdrive-files-list`: GET `{{ google_drive_base_url }}/files` with query filters.
2. `gdrive-files-get-metadata`: GET `{{ google_drive_base_url }}/files/{{ file_id }}`.
3. `gdrive-files-download-media`: GET `{{ google_drive_base_url }}/files/{{ file_id }}?alt=media`.
4. `gdrive-files-create-metadata`: POST `{{ google_drive_base_url }}/files`.
5. `gdrive-files-upload-multipart`: POST to upload endpoint with `uploadType=multipart`.
6. `gdrive-files-upload-resumable-initiate`: POST
   `{{ google_drive_upload_base_url }}/files?uploadType=resumable`.
7. `gdrive-files-upload-resumable-chunk`: PUT to
   `{{ google_drive_upload_session_url }}`.
8. `gdrive-permissions-list`: GET `{{ google_drive_base_url }}/files/{{ file_id }}/permissions`.
9. `gdrive-permissions-create`: POST `{{ google_drive_base_url }}/files/{{ file_id }}/permissions`.

## Resumable Upload Flow

The fixture models a two-stage flow for uploading a large file. It does not automatically
chain requests or split a local file into chunks.

1. Send `gdrive-files-upload-resumable-initiate`. Its exact URL is
   `{{ google_drive_upload_base_url }}/files?uploadType=resumable`; it sends JSON metadata and
   uses `Authorization: Bearer {{ google_drive_access_token }}`. Capture the response's
   `Location` header.
2. Set `google_drive_upload_session_url` to that opaque `Location` value, replace the example
   text body in `gdrive-files-upload-resumable-chunk` with the current file bytes, and send the
   PUT request. Its exact URL is `{{ google_drive_upload_session_url }}`.
3. For each chunk, set `google_drive_chunk_start` and `google_drive_chunk_end` to inclusive
   byte offsets, `google_drive_chunk_length` to the chunk byte length, and
   `google_drive_file_size` to the complete file size. For a contiguous chunk, length is
   `chunk_end - chunk_start + 1`.

The chunk request sends `Content-Range: bytes <start>-<end>/<file-size>` and
`Content-Length: <chunk-length>`. A `308 Resume Incomplete` response means continue with the
next range. `200 OK` or `201 Created` means the upload completed. The session URL is the
server-provided handoff value; do not reconstruct it or substitute the normal Drive base URL.

## Configuration

- `google_drive_base_url`: Base URL for Drive v3 REST endpoints
  (default: `https://www.googleapis.com/drive/v3`).
- `google_drive_upload_base_url`: Base URL for file upload endpoints
  (default: `https://www.googleapis.com/upload/drive/v3`).
- `google_drive_access_token`: OAuth 2.0 Bearer access token (`secret: true`).
- `google_drive_upload_session_url`: The `Location` header returned by the initiation request.
  The fixture leaves it blank until a session is created.
- `google_drive_chunk_start`, `google_drive_chunk_end`, and `google_drive_chunk_length`:
  Inclusive range and byte length for the current chunk.
- `google_drive_file_size`: Total file size used in `Content-Range`.
- `file_id`: Target file identifier or `root`.

Use placeholders and local PyPost variables only. Never commit a real access token, session URL,
or file content. The access-token variable is marked secret in the fixture; although the session
URL is a runtime handoff variable, treat it as sensitive and discard it when the upload session
is no longer needed.

The contract tests in `tests/test_google_drive_collection_example.py` load the fixture and inspect
its IDs, URLs, headers, variables, and documented status outcomes without making network requests.
They do not validate OAuth credentials, create a live upload session, upload bytes, retry chunks,
or verify Google Drive behavior.

## Troubleshooting

- **401 Unauthorized**: Ensure `google_drive_access_token` is populated with a valid OAuth token
  having `https://www.googleapis.com/auth/drive` or relevant read/write scopes.
- **Upload Failures**: Confirm that multipart requests send to `google_drive_upload_base_url`
  rather than standard metadata endpoints.
- **308 after a chunk**: Read the server's acknowledged range and send the next contiguous chunk;
  keep `Content-Length` consistent with the inclusive `Content-Range` offsets.
- **Invalid session URL**: Start a new initiation request and copy its `Location` header exactly;
  session URLs are opaque and may expire.
