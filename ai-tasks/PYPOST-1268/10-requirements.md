# PYPOST-1268: Create collection example for Google Drive

## Goals

Provide PyPost users and developers with a production-ready, standardized example collection showcasing integration with the Google Drive API v3. This example enables users to quickly understand and adopt PyPost for Google Drive workflows (listing files, viewing metadata, uploading/creating files, and managing permissions/sharing) while ensuring full compatibility with PyPost Collection Schema v2 and security best practices regarding secret management.

## Business Context & Value

Google Drive API v3 is one of the most widely used REST APIs in developer tooling, automation, and productivity ecosystems. PyPost currently includes example collections for Jira Cloud and local MCP probing, but lacks coverage for Google Workspace / Drive APIs. Supplying a curated, verified Google Drive collection accelerates user onboarding, provides a canonical pattern for Bearer-token-based cloud APIs, and guarantees schema correctness across releases.

## User Stories

- As an API developer or tester using PyPost, I want an out-of-the-box collection of Google Drive v3 REST requests so that I can immediately interact with Google Drive without hand-crafting endpoints, headers, and parameter definitions.
- As a team lead configuring PyPost environments, I want clearly documented and parameterized configuration variables (such as base URLs and OAuth access tokens) so that my credentials remain safely separated and uncommitted.
- As a PyPost contributor, I want automated contract and schema tests for the Google Drive collection so that regressions in collection structure or serialization are detected immediately during CI quality gates.

## Definition of Done

1. A valid collection example file exists under `examples/collections/google_drive.json` adhering to PyPost collection JSON format v2.
2. The collection covers core Google Drive v3 REST operations:
   - Listing files with query filters, ordering, and pagination fields.
   - Getting file metadata and binary content.
   - Creating/uploading file metadata and multipart/resumable request outlines.
   - Managing file permissions (listing and creating sharing permissions).
3. All authentication and host configurations rely on standard parameterized template variables (`google_drive_access_token`, `google_drive_base_url`, `google_drive_upload_base_url`) with safe defaults.
4. Companion environment or manifest references are updated consistently.
5. Automated contract tests verify that the collection loads cleanly into PyPost models without validation errors.
6. User/developer documentation (`examples/README.md`) references the new Google Drive collection example.

## Non-Functional Requirements

- **Security & Secret Safety**: Credentials (OAuth Bearer tokens) must never be hardcoded into collection files; they must strictly use template variables (`google_drive_access_token`) marked as secrets where appropriate.
- **Offline CI Testability**: Automated contract and schema tests for the collection must run completely offline without making external HTTP requests to Google APIs.
- **Schema Compatibility**: The collection JSON structure must strictly conform to PyPost Collection Schema v2 and deserialization models (`Collection`, `RequestData`, `CollectionVariable`).
- **Maintainability & Documentation**: Request definitions must include clear names, descriptions, and representative query parameter templates.

## Constraints & Assumptions

- **Constraints**:
  - Live OAuth2 handshake / token refresh mechanisms are out of scope; PyPost uses the provided access token via standard header substitution.
  - Test suites must not mutate existing unrelated test cases or require internet access.
- **Assumptions**:
  - The primary API target is Google Drive REST API v3.
  - End users obtain OAuth2 access tokens via Google Cloud Console / OAuth Playground / CLI external to PyPost and provide them via PyPost variables.

## Main Business Entities & Components

1. **Google Drive Collection (`google_drive.json`)**:
   - The top-level collection containing grouped REST request templates, metadata, variable declarations, and versioning.
2. **Drive Files & Metadata Resource**:
   - Represents files/folders in Drive with attributes: file ID, name, MIME type, parent folders, trash status, and metadata fields.
3. **Drive Permissions & Sharing Resource**:
   - Represents access control on files with attributes: role (reader, commenter, writer, owner), type (user, group, domain, anyone), and email address.
4. **Drive Uploads Resource**:
   - Dedicated endpoint structure for file creation and content upload using Google's upload base URL.
5. **Configuration & Environment Variables**:
   - `google_drive_base_url` (default: `https://www.googleapis.com/drive/v3`)
   - `google_drive_upload_base_url` (default: `https://www.googleapis.com/upload/drive/v3`)
   - `google_drive_access_token` (secret placeholder)
6. **Contract Test Suite Component**:
   - Automated unit/contract tests validating parsing, variable schemas, and request signatures in Python.

## Task Description

Create `examples/collections/google_drive.json` along with accompanying automated tests in `tests/test_example_fixtures.py` (or dedicated test file) and documentation updates in `examples/README.md`.

## Q&A

- **Q**: What API version should the collection target?
  **A**: Google Drive REST API v3.
- **Q**: How should authorization headers be formatted?
  **A**: Standard Bearer authorization: `Authorization: Bearer {{ google_drive_access_token }}`.
- **Q**: What programming languages are involved?
  **A**: JSON (collection schema v2) and Python (automated verification tests).
